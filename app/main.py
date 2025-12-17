from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os
from typing import Optional
from app.config import Config
from app.video_processor import extract_transcript
from app.content_generator import generate_linkedin_post
from app.linkedin_api import get_authorization_url, get_access_token, post_to_linkedin
from app.facebook_api import get_facebook_authorization_url, get_facebook_access_token, post_to_facebook
from app.instagram_api import get_instagram_authorization_url, get_instagram_access_token, post_to_instagram
from app.exceptions import TokenExpiredException
import tempfile
import shutil

app = FastAPI(title="Video to Social Media Pipeline")

# Validate configuration on startup
Config.validate_config()

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=Config.SECRET_KEY)

# Templates
templates = Jinja2Templates(directory="app/templates")

# Create uploads and images directories
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.IMAGES_FOLDER, exist_ok=True)

# Serve static images
app.mount("/images", StaticFiles(directory=Config.IMAGES_FOLDER), name="images")

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    posts = request.session.get('posted_content', [])
    return templates.TemplateResponse("index.html", {"request": request, "posts": posts})

@app.post("/upload")
async def upload_video(
    request: Request,
    video_file: Optional[UploadFile] = File(None),
    youtube_url: Optional[str] = Form(None)
):
    
    if not video_file and not youtube_url:
        request.session['error'] = 'No video source provided'
        return RedirectResponse(url="/", status_code=303)
    
    try:
        if youtube_url:
            transcript = extract_transcript(youtube_url)
        else:
            if not video_file or video_file.filename == '':
                request.session['error'] = 'No file selected'
                return RedirectResponse(url="/", status_code=303)
            
            if not allowed_file(video_file.filename):
                request.session['error'] = 'Invalid file type'
                return RedirectResponse(url="/", status_code=303)
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(video_file.filename)[1]) as tmp_file:
                shutil.copyfileobj(video_file.file, tmp_file)
                tmp_path = tmp_file.name
            
            try:
                transcript = extract_transcript(tmp_path)
            finally:
                os.unlink(tmp_path)
        
        # Extract video title if available
        video_title = transcript.get('title', 'Video Content Analysis')
        
        result = generate_linkedin_post(transcript['text'], video_title)
        
        # Handle both string and dict returns (for image support)
        if isinstance(result, dict):
            linkedin_post = result.get('post', result.get('content', ''))
            image_path = result.get('image_url')
            
            # Convert local path to web URL for preview
            if image_path and os.path.exists(image_path):
                image_filename = os.path.basename(image_path)
                image_url = f"/images/{image_filename}"
            else:
                image_url = image_path  # Keep original if it's HTTP URL
        else:
            linkedin_post = result
            image_url = None
            image_path = None
        
        pending_post_data = {
            'transcript': transcript['text'],
            'linkedin_post': linkedin_post,
            'image_url': image_url,  # Web URL for preview
            'image_path': image_path,  # Local path for uploading
            'video_title': video_title
        }
        request.session['pending_post'] = pending_post_data
        
        return templates.TemplateResponse("review.html", {
            "request": request,
            "transcript": transcript['text'],
            "linkedin_post": linkedin_post,
            "video_title": video_title,
            "image_url": image_url,
            "image_available": image_url is not None,
            "linkedin_authenticated": request.session.get('linkedin_access_token') is not None,
            "facebook_authenticated": request.session.get('facebook_access_token') is not None,
            "instagram_authenticated": request.session.get('instagram_access_token') is not None
        })
    except Exception as e:
        request.session['error'] = f'Error processing video: {str(e)}'
        return RedirectResponse(url="/", status_code=303)

@app.get("/auth/linkedin")
async def linkedin_auth():
    auth_url = get_authorization_url()
    return RedirectResponse(url=auth_url)

@app.get("/auth/linkedin/callback")
async def linkedin_callback(request: Request, code: Optional[str] = None):
    if not code:
        request.session['error'] = 'Authorization failed - no code'
        return RedirectResponse(url="/", status_code=303)
    
    try:
        access_token = get_access_token(code)
        request.session['linkedin_access_token'] = access_token
        
        pending_post = request.session.get('pending_post')
        
        if pending_post:
            return templates.TemplateResponse("review.html", {
                "request": request,
                "transcript": pending_post['transcript'],
                "linkedin_post": pending_post['linkedin_post'],
                "video_title": pending_post.get('video_title'),
                "image_url": pending_post.get('image_url'),  # Web URL for preview
                "image_available": pending_post.get('image_url') is not None,
                "linkedin_authenticated": True,
                "facebook_authenticated": request.session.get('facebook_access_token') is not None,
                "instagram_authenticated": request.session.get('instagram_access_token') is not None
            })
        else:
            request.session['success'] = 'LinkedIn authentication successful!'
            return RedirectResponse(url="/", status_code=303)
        
    except Exception as e:
        request.session['error'] = f'Authentication failed: {str(e)}'
        return RedirectResponse(url="/", status_code=303)

@app.get("/auth/facebook")
async def facebook_auth():
    if not Config.FACEBOOK_APP_ID:
        raise HTTPException(status_code=400, detail="Facebook integration not configured")
    auth_url = get_facebook_authorization_url()
    return RedirectResponse(url=auth_url)

@app.get("/auth/facebook/callback")
async def facebook_callback(request: Request, code: Optional[str] = None):
    if not code:
        request.session['error'] = 'Facebook authorization failed - no code'
        return RedirectResponse(url="/", status_code=303)
    
    try:
        access_token = get_facebook_access_token(code)
        request.session['facebook_access_token'] = access_token
        
        pending_post = request.session.get('pending_post')
        if pending_post:
            return templates.TemplateResponse("review.html", {
                "request": request,
                "transcript": pending_post['transcript'],
                "linkedin_post": pending_post['linkedin_post'],
                "video_title": pending_post.get('video_title'),
                "image_url": pending_post.get('image_url'),
                "image_available": pending_post.get('image_url') is not None,
                "linkedin_authenticated": request.session.get('linkedin_access_token') is not None,
                "facebook_authenticated": True,
                "instagram_authenticated": request.session.get('instagram_access_token') is not None
            })
        else:
            request.session['success'] = 'Facebook authentication successful!'
            return RedirectResponse(url="/", status_code=303)
        
    except Exception as e:
        request.session['error'] = f'Facebook authentication failed: {str(e)}'
        return RedirectResponse(url="/", status_code=303)

@app.get("/auth/instagram")
async def instagram_auth():
    if not Config.FACEBOOK_APP_ID:
        raise HTTPException(status_code=400, detail="Instagram integration not configured")
    auth_url = get_instagram_authorization_url()
    return RedirectResponse(url=auth_url)

@app.get("/auth/instagram/callback")
async def instagram_callback(request: Request, code: Optional[str] = None):
    if not code:
        request.session['error'] = 'Instagram authorization failed - no code'
        return RedirectResponse(url="/", status_code=303)
    
    try:
        access_token = get_instagram_access_token(code)
        request.session['instagram_access_token'] = access_token
        
        pending_post = request.session.get('pending_post')
        if pending_post:
            return templates.TemplateResponse("review.html", {
                "request": request,
                "transcript": pending_post['transcript'],
                "linkedin_post": pending_post['linkedin_post'],
                "video_title": pending_post.get('video_title'),
                "image_url": pending_post.get('image_url'),
                "image_available": pending_post.get('image_url') is not None,
                "linkedin_authenticated": request.session.get('linkedin_access_token') is not None,
                "facebook_authenticated": request.session.get('facebook_access_token') is not None,
                "instagram_authenticated": True
            })
        else:
            request.session['success'] = 'Instagram authentication successful!'
            return RedirectResponse(url="/", status_code=303)
        
    except Exception as e:
        request.session['error'] = f'Instagram authentication failed: {str(e)}'
        return RedirectResponse(url="/", status_code=303)

@app.post("/post/linkedin")
async def post_linkedin(
    request: Request,
    post_text: str = Form(...),
    access_token: Optional[str] = Form(None)
):
    session_token = request.session.get('linkedin_access_token')
    final_token = access_token or session_token
    
    if not final_token:
        request.session['error'] = 'Not authenticated with LinkedIn'
        return RedirectResponse(url="/", status_code=303)
    
    if not post_text:
        request.session['error'] = 'No post content provided'
        return RedirectResponse(url="/", status_code=303)
    
    try:
        # Get image path from session if available
        pending_post = request.session.get('pending_post', {})
        image_path = pending_post.get('image_path')
        
        result = post_to_linkedin(final_token, post_text, image_path)
        
        posted_content = request.session.get('posted_content', [])
        posted_content.append({
            'platform': 'LinkedIn',
            'content': post_text,
            'post_id': result.get('id', 'N/A'),
            'status': 'Posted'
        })
        request.session['posted_content'] = posted_content
        
        request.session['success'] = f'Successfully posted to LinkedIn! Post ID: {result.get("id", "N/A")}'
        return RedirectResponse(url="/", status_code=303)
        
    except Exception as e:
        import traceback
        print(f"LinkedIn posting error: {traceback.format_exc()}")
        request.session['error'] = f'Failed to post: {str(e)}'
        return RedirectResponse(url="/", status_code=303)

@app.post("/post/social")
async def post_social(
    request: Request,
    post_text: str = Form(...),
    platforms: Optional[str] = Form(None)  # Comma-separated platform list
):
    """Post to multiple social media platforms simultaneously"""
    if not post_text:
        request.session['error'] = 'No post content provided'
        return RedirectResponse(url="/", status_code=303)
    
    # Parse selected platforms
    selected_platforms = [p.strip() for p in platforms.split(',')] if platforms else []
    if not selected_platforms:
        request.session['error'] = 'No platforms selected'
        return RedirectResponse(url="/", status_code=303)
    
    # Get image path from session
    pending_post = request.session.get('pending_post', {})
    image_path = pending_post.get('image_path')
    
    results = []
    errors = []
    
    # Post to LinkedIn
    if 'linkedin' in selected_platforms:
        linkedin_token = request.session.get('linkedin_access_token')
        if linkedin_token:
            try:
                result = post_to_linkedin(linkedin_token, post_text, image_path)
                results.append(f"LinkedIn (Post ID: {result.get('id', 'N/A')})")
            except TokenExpiredException as e:
                # Clear expired token from session
                request.session.pop('linkedin_access_token', None)
                errors.append(f"LinkedIn: {str(e.message)}. Please re-authenticate.")
            except Exception as e:
                errors.append(f"LinkedIn: {str(e)}")
        else:
            errors.append("LinkedIn: Not authenticated")
    
    # Post to Facebook
    if 'facebook' in selected_platforms:
        facebook_token = request.session.get('facebook_access_token')
        if facebook_token:
            try:
                result = post_to_facebook(facebook_token, post_text, image_path)
                results.append(f"Facebook (Post ID: {result.get('post_id', 'N/A')})")
            except TokenExpiredException as e:
                # Clear expired token from session
                request.session.pop('facebook_access_token', None)
                errors.append(f"Facebook: {str(e.message)}. Please re-authenticate.")
            except Exception as e:
                errors.append(f"Facebook: {str(e)}")
        else:
            errors.append("Facebook: Not authenticated")
    
    # Post to Instagram
    if 'instagram' in selected_platforms:
        instagram_token = request.session.get('instagram_access_token')
        if instagram_token:
            if not image_path:
                errors.append("Instagram: Requires an image")
            else:
                try:
                    result = post_to_instagram(instagram_token, post_text, image_path)
                    results.append(f"Instagram (Post ID: {result.get('post_id', 'N/A')})")
                except TokenExpiredException as e:
                    # Clear expired token from session
                    request.session.pop('instagram_access_token', None)
                    errors.append(f"Instagram: {str(e.message)}. Please re-authenticate.")
                except Exception as e:
                    errors.append(f"Instagram: {str(e)}")
        else:
            errors.append("Instagram: Not authenticated")
    
    # Save all results to session
    posted_content = request.session.get('posted_content', [])
    for platform_result in results:
        posted_content.append({
            'platform': platform_result.split(' ')[0],
            'content': post_text[:100] + '...',
            'post_id': 'See logs',
            'status': 'Posted'
        })
    request.session['posted_content'] = posted_content
    
    # Build response message
    if results and not errors:
        request.session['success'] = f'Successfully posted to: {", ".join(results)}'
        return RedirectResponse(url="/", status_code=303)
    elif results and errors:
        # Some posted, some failed - show review page with new auth status
        request.session['warning'] = f'Posted to: {", ".join(results)}. Errors: {"; ".join(errors)}'
        pending_post = request.session.get('pending_post', {})
        if pending_post:
            return templates.TemplateResponse("review.html", {
                "request": request,
                "transcript": pending_post.get('transcript', ''),
                "linkedin_post": post_text,
                "video_title": pending_post.get('video_title', ''),
                "image_url": pending_post.get('image_url'),
                "image_available": pending_post.get('image_url') is not None,
                "linkedin_authenticated": request.session.get('linkedin_access_token') is not None,
                "facebook_authenticated": request.session.get('facebook_access_token') is not None,
                "instagram_authenticated": request.session.get('instagram_access_token') is not None
            })
        return RedirectResponse(url="/", status_code=303)
    else:
        # All failed - show review page with error and updated auth status
        request.session['error'] = f'Failed to post. Errors: {"; ".join(errors)}'
        pending_post = request.session.get('pending_post', {})
        if pending_post:
            return templates.TemplateResponse("review.html", {
                "request": request,
                "transcript": pending_post.get('transcript', ''),
                "linkedin_post": post_text,
                "video_title": pending_post.get('video_title', ''),
                "image_url": pending_post.get('image_url'),
                "image_available": pending_post.get('image_url') is not None,
                "linkedin_authenticated": request.session.get('linkedin_access_token') is not None,
                "facebook_authenticated": request.session.get('facebook_access_token') is not None,
                "instagram_authenticated": request.session.get('instagram_access_token') is not None
            })
        return RedirectResponse(url="/", status_code=303)
