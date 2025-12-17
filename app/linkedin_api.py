import requests
from app.config import Config
from app.exceptions import TokenExpiredException

def get_authorization_url():
    params = {
        'response_type': 'code',
        'client_id': Config.LINKEDIN_CLIENT_ID,
        'redirect_uri': Config.LINKEDIN_REDIRECT_URI,
        'scope': 'openid profile w_member_social',  # Added 'openid profile' like in test.py
        'state': 'random_state_string'
    }
    
    auth_url = 'https://www.linkedin.com/oauth/v2/authorization'
    query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
    return f"{auth_url}?{query_string}"

def get_access_token(authorization_code):
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    token_data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": Config.LINKEDIN_REDIRECT_URI,
        "client_id": Config.LINKEDIN_CLIENT_ID,
        "client_secret": Config.LINKEDIN_CLIENT_SECRET,
    }

    response = requests.post(token_url, data=token_data)
    token_json = response.json()
    access_token = token_json.get("access_token")

    if not access_token:
        raise Exception(f"Failed to get token: {token_json}")
    
    return access_token

def get_profile_urn(access_token):
    # Exact same approach as test.py
    profile_url = "https://api.linkedin.com/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    profile_response = requests.get(profile_url, headers=headers)
    profile_data = profile_response.json()
    
    # Check for token expiration/revocation (401 error)
    if profile_response.status_code == 401 or profile_data.get('status') == 401:
        error_code = profile_data.get('code', '')
        if 'REVOKED' in error_code or 'EXPIRED' in error_code or error_code == 'REVOKED_ACCESS_TOKEN':
            raise TokenExpiredException('LinkedIn', f"Access token has been revoked or expired: {error_code}")
        raise TokenExpiredException('LinkedIn', f"Authentication failed: {profile_data}")
    
    if 'sub' not in profile_data:
        raise Exception(f"Error fetching profile: {profile_data}")
         
    user_urn = f"urn:li:person:{profile_data['sub']}"
    return user_urn

def upload_image_to_linkedin(access_token, image_path):
    """Upload image to LinkedIn and return asset URN"""
    import os
    
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return None
    
    user_urn = get_profile_urn(access_token)
    
    # Step 1: Register upload
    register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    register_data = {
        "registerUploadRequest": {
            "recipes": [
                "urn:li:digitalmediaRecipe:feedshare-image"
            ],
            "owner": user_urn,
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }
            ]
        }
    }
    
    register_response = requests.post(register_url, headers=headers, json=register_data)
    
    if register_response.status_code != 200:
        print(f"❌ Failed to register upload: {register_response.text}")
        return None
    
    register_result = register_response.json()
    upload_mechanism = register_result["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]
    asset_id = register_result["value"]["asset"]
    upload_url = upload_mechanism["uploadUrl"]
    
    # Step 2: Upload image
    with open(image_path, 'rb') as image_file:
        upload_headers = {"Authorization": f"Bearer {access_token}"}
        upload_response = requests.post(upload_url, headers=upload_headers, data=image_file)
        
        if upload_response.status_code not in [200, 201]:
            print(f"❌ Failed to upload image: {upload_response.text}")
            return None
    
    return asset_id

def post_to_linkedin(access_token, text, image_path=None):
    user_urn = get_profile_urn(access_token)

    # Add timestamp to prevent duplicate posts
    import datetime
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final_message = f"{text}\n\n(Posted at {current_time})"

    post_url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Upload image if provided
    media_asset = None
    if image_path:
        print(f"📎 Uploading image: {image_path}")
        media_asset = upload_image_to_linkedin(access_token, image_path)
        if not media_asset:
            print("⚠️ Image upload failed, posting without image")
    
    # Create post data
    post_data = {
        "author": user_urn,
        "lifecycleState": "PUBLISHED",
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    if media_asset:
        # Post with image
        post_data["specificContent"] = {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": final_message
                },
                "shareMediaCategory": "IMAGE",
                "media": [
                    {
                        "status": "READY",
                        "description": {
                            "text": "Generated image for LinkedIn post"
                        },
                        "media": media_asset,
                        "title": {
                            "text": "Post Image"
                        }
                    }
                ]
            }
        }
    else:
        # Text only post
        post_data["specificContent"] = {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": final_message
                },
                "shareMediaCategory": "NONE"
            }
        }

    post_response = requests.post(post_url, headers=headers, json=post_data)

    if post_response.status_code == 201:
        post_id = post_response.json().get("id", "Unknown ID")
        return {"id": post_id, "status": "success", "message": final_message}
    else:
        raise Exception(f"Failed to post to LinkedIn: Status {post_response.status_code}, Response: {post_response.text}")
