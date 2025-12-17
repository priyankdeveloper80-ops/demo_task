import os
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app import app
from app.video_processor import extract_transcript
from app.content_generator import generate_linkedin_post
from app.linkedin_api import get_authorization_url, get_access_token, post_to_linkedin
from werkzeug.utils import secure_filename

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    posts = session.get('posted_content', [])
    return render_template('index.html', posts=posts)

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video_file' not in request.files and 'youtube_url' not in request.form:
        flash('No video source provided')
        return redirect(url_for('index'))
    
    try:
        if 'youtube_url' in request.form and request.form['youtube_url']:
            video_source = request.form['youtube_url']
            transcript = extract_transcript(video_source)
        else:
            file = request.files['video_file']
            if file.filename == '':
                flash('No file selected')
                return redirect(url_for('index'))
            
            if not allowed_file(file.filename):
                flash('Invalid file type')
                return redirect(url_for('index'))
            
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            transcript = extract_transcript(filepath)
            os.unlink(filepath)
        
        linkedin_post = generate_linkedin_post(transcript['text'])
        
        session['pending_post'] = {
            'transcript': transcript['text'],
            'linkedin_post': linkedin_post
        }
        
        return render_template('review.html', 
                             transcript=transcript['text'],
                             linkedin_post=linkedin_post)
    except Exception as e:
        flash(f'Error processing video: {str(e)}')
        return redirect(url_for('index'))

@app.route('/auth/linkedin')
def linkedin_auth():
    auth_url = get_authorization_url()
    return redirect(auth_url)

@app.route('/auth/linkedin/callback')
def linkedin_callback():
    code = request.args.get('code')
    if not code:
        flash('Authorization failed')
        return redirect(url_for('index'))
    
    try:
        access_token = get_access_token(code)
        session['linkedin_access_token'] = access_token
        
        pending_post = session.get('pending_post')
        if pending_post:
            return render_template('review.html',
                                 transcript=pending_post['transcript'],
                                 linkedin_post=pending_post['linkedin_post'],
                                 access_token=access_token)
        
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Authentication failed: {str(e)}')
        return redirect(url_for('index'))

@app.route('/post/linkedin', methods=['POST'])
def post_linkedin():
    access_token = session.get('linkedin_access_token') or request.form.get('access_token')
    post_text = request.form.get('post_text')
    
    if not access_token:
        flash('Not authenticated with LinkedIn')
        return redirect(url_for('index'))
    
    if not post_text:
        flash('No post content provided')
        return redirect(url_for('index'))
    
    try:
        result = post_to_linkedin(access_token, post_text)
        
        posted_content = session.get('posted_content', [])
        posted_content.append({
            'platform': 'LinkedIn',
            'content': post_text,
            'post_id': result.get('id', 'N/A'),
            'status': 'Posted'
        })
        session['posted_content'] = posted_content
        
        flash('Successfully posted to LinkedIn!')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Failed to post: {str(e)}')
        return redirect(url_for('index'))
