"""Instagram API integration for posting content to Instagram Business Accounts"""
import requests
import time
from app.config import Config
from app.exceptions import TokenExpiredException

def get_instagram_authorization_url():
    """Generate Instagram/Facebook OAuth authorization URL"""
    # Instagram uses Facebook OAuth with Instagram-specific scopes
    params = {
        'client_id': Config.FACEBOOK_APP_ID,
        'redirect_uri': Config.FACEBOOK_REDIRECT_URI.replace('/facebook/', '/instagram/'),
        'scope': 'instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement,business_management',
        'response_type': 'code',
        'auth_type': 'reauthenticate',
    }
    auth_url = 'https://www.facebook.com/v19.0/dialog/oauth'
    query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
    return f"{auth_url}?{query_string}"

def get_instagram_access_token(authorization_code):
    """Exchange authorization code for access token"""
    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "client_id": Config.FACEBOOK_APP_ID,
        "client_secret": Config.FACEBOOK_APP_SECRET,
        "redirect_uri": Config.FACEBOOK_REDIRECT_URI.replace('/facebook/', '/instagram/'),
        "code": authorization_code
    }
    
    response = requests.get(token_url, params=params)
    
    print(f"Instagram token response status: {response.status_code}")
    data = response.json()
    
    if "access_token" not in data:
        raise Exception(f"Failed to get Instagram token: {data}")
    
    return data.get("access_token")

def get_instagram_account_id(page_id, page_access_token):
    """Get Instagram Business Account ID linked to Facebook Page"""
    ig_account_url = f"https://graph.facebook.com/v19.0/{page_id}"
    ig_params = {
        "fields": "instagram_business_account",
        "access_token": page_access_token
    }
    ig_resp = requests.get(ig_account_url, params=ig_params)
    ig_data = ig_resp.json()
    
    # Check for token expiration/revocation
    if "error" in ig_data:
        error = ig_data["error"]
        if error.get("code") == 190 or error.get("type") == "OAuthException":
            raise TokenExpiredException('Instagram', f"Access token expired or invalid: {error.get('message')}")
    
    if "instagram_business_account" not in ig_data:
        raise Exception(
            "No Instagram Business Account linked to this Facebook Page. "
            "Please link an Instagram Business Account to your Facebook Page first."
        )
    
    return ig_data["instagram_business_account"]["id"]

def upload_image_to_facebook(page_id, page_access_token, image_path):
    """Upload image to Facebook and return public URL for Instagram"""
    fb_upload_url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
    
    with open(image_path, 'rb') as image_file:
        files = {'source': image_file}
        upload_params = {
            "published": "false",  # Don't publish to Facebook
            "access_token": page_access_token
        }
        upload_resp = requests.post(fb_upload_url, data=upload_params, files=files)
    
    if upload_resp.status_code != 200:
        raise Exception(f"Failed to upload image: {upload_resp.json()}")
    
    photo_id = upload_resp.json().get("id")
    
    # Get the image URL
    photo_url_endpoint = f"https://graph.facebook.com/v19.0/{photo_id}"
    photo_url_params = {
        "fields": "images",
        "access_token": page_access_token
    }
    photo_url_resp = requests.get(photo_url_endpoint, params=photo_url_params)
    
    if photo_url_resp.status_code != 200:
        raise Exception(f"Failed to get image URL: {photo_url_resp.json()}")
    
    images = photo_url_resp.json().get("images", [])
    if not images:
        raise Exception("No image URL found")
    
    return images[0]["source"]  # Highest resolution

def post_to_instagram(access_token, text, image_path=None):
    """
    Post content to Instagram Business Account
    
    Args:
        access_token: User access token (will be exchanged for page token)
        text: Post caption
        image_path: Path to image file (required for Instagram)
        
    Returns:
        dict with status, post_id, and other details
    """
    import os
    import datetime
    
    if not image_path or not os.path.exists(image_path):
        raise Exception("Instagram requires an image. Image path not provided or file not found.")
    
    # Get Page information (needed to access Instagram account)
    from app.facebook_api import get_page_info
    page_info = get_page_info(access_token)
    page_id = page_info['page_id']
    page_access_token = page_info['page_access_token']
    page_name = page_info['page_name']
    
    # Get Instagram Business Account ID
    print(f"🔍 Looking for Instagram account linked to '{page_name}'...")
    instagram_account_id = get_instagram_account_id(page_id, page_access_token)
    print(f"✅ Found Instagram account: {instagram_account_id}")
    
    # Add timestamp to caption
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final_caption = f"{text}\n\n📸 Posted via Video Pipeline at {current_time}"
    
    # Upload image to get public URL
    print(f"📤 Uploading image to Facebook...")
    image_url = upload_image_to_facebook(page_id, page_access_token, image_path)
    print(f"✅ Image uploaded: {image_url[:50]}...")
    
    # Create Instagram Media Container
    print(f"📱 Creating Instagram media container...")
    container_url = f"https://graph.facebook.com/v19.0/{instagram_account_id}/media"
    container_params = {
        "image_url": image_url,
        "caption": final_caption,
        "access_token": page_access_token
    }
    container_resp = requests.post(container_url, data=container_params)
    
    if container_resp.status_code != 200:
        raise Exception(f"Failed to create Instagram media container: {container_resp.json()}")
    
    creation_id = container_resp.json().get("id")
    print(f"✅ Media container created: {creation_id}")
    
    # Wait for container to be ready
    time.sleep(2)
    
    # Publish the Instagram Media Container
    print(f"📤 Publishing to Instagram...")
    publish_url = f"https://graph.facebook.com/v19.0/{instagram_account_id}/media_publish"
    publish_params = {
        "creation_id": creation_id,
        "access_token": page_access_token
    }
    publish_resp = requests.post(publish_url, data=publish_params)
    
    if publish_resp.status_code == 200:
        return {
            "status": "success",
            "platform": "Instagram",
            "page": page_name,
            "post_id": publish_resp.json().get("id"),
            "instagram_account_id": instagram_account_id,
            "message": "Successfully posted to Instagram! 📷"
        }
    else:
        raise Exception(f"Instagram publishing failed: {publish_resp.status_code}, {publish_resp.text}")
