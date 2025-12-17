"""Facebook API integration for posting content to Facebook Pages"""
import requests
import time
from app.config import Config
from app.exceptions import TokenExpiredException

def get_facebook_authorization_url():
    """Generate Facebook OAuth authorization URL"""
    params = {
        'client_id': Config.FACEBOOK_APP_ID,
        'redirect_uri': Config.FACEBOOK_REDIRECT_URI,
        'scope': 'pages_manage_posts,pages_read_engagement,pages_show_list,business_management',
        'response_type': 'code',
        'auth_type': 'reauthenticate',
    }
    auth_url = 'https://www.facebook.com/v19.0/dialog/oauth'
    query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
    return f"{auth_url}?{query_string}"

def get_facebook_access_token(authorization_code):
    """Exchange authorization code for access token"""
    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "client_id": Config.FACEBOOK_APP_ID,
        "client_secret": Config.FACEBOOK_APP_SECRET,
        "redirect_uri": Config.FACEBOOK_REDIRECT_URI,
        "code": authorization_code
    }
    
    response = requests.get(token_url, params=params)
    
    print(f"Facebook token response status: {response.status_code}")
    data = response.json()
    
    if "access_token" not in data:
        raise Exception(f"Failed to get Facebook token: {data}")
    
    return data.get("access_token")

def get_page_info(user_access_token):
    """Get Facebook Page information and Page access token"""
    accounts_url = "https://graph.facebook.com/v19.0/me/accounts"
    response = requests.get(accounts_url, params={"access_token": user_access_token})
    accounts_data = response.json()
    
    # Check for token expiration/revocation
    if "error" in accounts_data:
        error = accounts_data["error"]
        if error.get("code") == 190 or error.get("type") == "OAuthException":
            raise TokenExpiredException('Facebook', f"Access token expired or invalid: {error.get('message')}")
    
    if "data" not in accounts_data or len(accounts_data["data"]) == 0:
        # Check permissions for debugging
        perm_url = "https://graph.facebook.com/v19.0/me/permissions"
        perm_resp = requests.get(perm_url, params={"access_token": user_access_token})
        perm_data = perm_resp.json()
        
        raise Exception(f"No Facebook Pages found. Permissions: {perm_data}")
    
    first_page = accounts_data["data"][0]
    return {
        'page_id': first_page["id"],
        'page_access_token': first_page["access_token"],
        'page_name': first_page["name"]
    }

def post_to_facebook(access_token, text, image_path=None):
    """
    Post content to Facebook Page
    
    Args:
        access_token: User access token (will be exchanged for page token)
        text: Post caption/text
        image_path: Optional path to image file
        
    Returns:
        dict with status, post_id, and other details
    """
    import os
    import datetime
    
    # Get Page information
    page_info = get_page_info(access_token)
    page_id = page_info['page_id']
    page_access_token = page_info['page_access_token']
    page_name = page_info['page_name']
    
    # Add timestamp to prevent duplicate posts
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final_caption = f"{text}\n\n(Posted via Video Pipeline at {current_time})"
    
    post_url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
    
    # Check if image exists
    if image_path and not os.path.exists(image_path):
        print(f"⚠️ Image file not found: {image_path}, posting text only")
        image_path = None
    
    if image_path:
        # Post with image
        print(f"📤 Posting to Facebook Page '{page_name}' with image...")
        with open(image_path, 'rb') as image_file:
            files = {'source': image_file}
            post_params = {
                "caption": final_caption,
                "access_token": page_access_token
            }
            response = requests.post(post_url, data=post_params, files=files)
    else:
        # Text-only post (use feed endpoint instead of photos)
        print(f"📤 Posting to Facebook Page '{page_name}' (text only)...")
        post_url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
        post_params = {
            "message": final_caption,
            "access_token": page_access_token
        }
        response = requests.post(post_url, data=post_params)
    
    print(f"Facebook post response status: {response.status_code}")
    
    if response.status_code == 200:
        return {
            "status": "success",
            "platform": "Facebook",
            "page": page_name,
            "post_id": response.json().get("id"),
            "message": "Successfully posted to Facebook! 🎉"
        }
    else:
        raise Exception(f"Facebook posting failed: {response.status_code}, {response.text}")
