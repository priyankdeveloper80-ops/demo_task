# Video-to-Social Media Pipeline

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--3.5-412991.svg)](https://openai.com/)

An AI-powered system that automatically converts videos into platform-optimized social media posts and publishes them to **LinkedIn**, **Instagram**, and **Facebook**.

## 🌟 Features

- **🎥 Multi-Source Video Processing**
  - Upload local video files (MP4, AVI, MOV, MKV, WebM)
  - Process YouTube videos via URL
  - Automatic audio extraction and transcription using OpenAI Whisper

- **🤖 AI-Powered Content Generation**
  - Intelligent post creation using OpenAI GPT-3.5
  - Platform-optimized content with proper formatting
  - Automatic hashtag generation based on video content
  - Engaging hooks and call-to-action elements

- **📱 Multi-Platform Publishing**
  - LinkedIn post publishing with image support
  - Facebook post publishing with images
  - Instagram post publishing (requires image)
  - Simultaneous multi-platform posting
  - OAuth 2.0 authentication for all platforms

- **🖼️ Image Support**
  - DALL-E 3 integration
  - Automatic image generation based on video content

- **🎨 Web Dashboard**
  - Clean, intuitive user interface
  - Real-time post preview and editing
  - Multi-platform authentication management
  - Post history tracking


## 🔧 Prerequisites

### System Requirements
- Python 3.8 or higher
- FFmpeg (for audio/video processing)
- 4GB+ RAM (for Whisper transcription)
- Internet connection

### API Credentials Required

1. **OpenAI API Key**
   - Sign up at [OpenAI Platform](https://platform.openai.com/)
   - Generate API key from dashboard
   - Required for content generation and transcription

2. **LinkedIn Developer Application**
   - Create app at [LinkedIn Developers](https://www.linkedin.com/developers/)
   - Required permissions: `w_member_social`, `r_liteprofile`
   - Get Client ID and Client Secret

3. **Facebook Developer Application** (for Facebook & Instagram)
   - Create app at [Facebook Developers](https://developers.facebook.com/)
   - Required permissions: `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`
   - Get App ID and App Secret
   - Note: Instagram posting requires a Business account linked to a Facebook Page

## 📦 Installation

### Step 1: Clone or Navigate to Project

```bash
cd video_generation
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies include:**
- `fastapi==0.104.1` - Web framework
- `uvicorn==0.24.0` - ASGI server
- `jinja2==3.1.2` - Template engine
- `python-multipart==0.0.6` - File upload support
- `python-dotenv==1.0.0` - Environment variable management
- `openai==1.3.0` - OpenAI API client
- `Pillow==10.1.0` - Image processing
- `openai-whisper==20231117` - Audio transcription
- `requests==2.31.0` - HTTP library
- `ffmpeg-python==0.2.0` - FFmpeg wrapper

### Step 4: Install FFmpeg

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**MacOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from [FFmpeg Official Site](https://ffmpeg.org/download.html)

### Step 5: Verify Installation

```bash
python -c "import whisper; import openai; print('✅ All dependencies installed!')"
ffmpeg -version
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI API Key (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here

# LinkedIn App Credentials (REQUIRED for LinkedIn posting)
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:5000/auth/linkedin/callback

# Facebook/Instagram App Credentials (OPTIONAL - enables Facebook & Instagram)
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
FACEBOOK_REDIRECT_URI=http://localhost:5000/auth/facebook/callback

# Secret key for session management (Change in production!)
SECRET_KEY=dev-secret-key-change-in-production
```

### Configuration File Details

The `app/config.py` file manages all configuration:

```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    LINKEDIN_CLIENT_ID = os.environ.get('LINKEDIN_CLIENT_ID')
    LINKEDIN_CLIENT_SECRET = os.environ.get('LINKEDIN_CLIENT_SECRET')
    LINKEDIN_REDIRECT_URI = os.environ.get('LINKEDIN_REDIRECT_URI')
    FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID')
    FACEBOOK_APP_SECRET = os.environ.get('FACEBOOK_APP_SECRET')
    FACEBOOK_REDIRECT_URI = os.environ.get('FACEBOOK_REDIRECT_URI')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
```

### LinkedIn App Setup

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Create a new app
3. Under "Auth" tab:
   - Add redirect URL: `http://localhost:5000/auth/linkedin/callback`
   - Request permissions: `w_member_social`, `r_liteprofile`
4. Copy Client ID and Client Secret to `.env`

### Facebook/Instagram App Setup

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app (Business type)
3. Add Facebook Login product
4. Under Settings → Basic:
   - Copy App ID and App Secret to `.env`
5. Under Facebook Login → Settings:
   - Add redirect URI: `http://localhost:5000/auth/facebook/callback`
6. Under App Review → Permissions:
   - Request: `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`

**Instagram Requirements:**
- Must have an Instagram Business account
- Instagram account must be linked to a Facebook Page
- You must be an admin of that Facebook Page

## 🚀 Usage

### Starting the Application

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the application
python run.py
```

The application will start at: **http://localhost:5000**

### Complete Workflow

#### 1. Upload Video

**Option A: Upload Local Video**
1. Open http://localhost:5000
2. Click "Choose File"
3. Select video file (MP4, AVI, MOV, MKV, WebM)
4. Click "Process Video"

**Option B: Process YouTube Video**
1. Open http://localhost:5000
2. Paste YouTube URL
3. Click "Process Video"

#### 2. AI Processing

The system automatically:
- Extracts audio from video
- Transcribes using OpenAI Whisper
- Generates optimized post using GPT-3.5
- Creates or attaches an image

#### 3. Review & Edit

After processing:
- Review the generated post
- Edit content if needed
- Preview attached image
- Select target platforms

#### 4. Authenticate Platforms

Click "Connect" buttons for desired platforms:
- **LinkedIn**: OAuth flow → authorize app
- **Facebook**: OAuth flow → select page
- **Instagram**: OAuth flow → link business account

#### 5. Publish

- Select platforms (LinkedIn, Facebook, Instagram)
- Click "Post to Selected Platforms"
- View success confirmation

### Command Line Usage (Alternative)

You can also run the server with custom settings:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```
