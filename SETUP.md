# Setup Guide - Video to Social Media Pipeline

## Quick Start

This guide will help you set up the Video-to-Social Media Pipeline from scratch.

---

## 1. System Prerequisites

### Required Software

#### Python 3.8+

**Check if installed:**
```bash
python3 --version
```

**Install on Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**Install on MacOS:**
```bash
brew install python3
```

#### FFmpeg

**Check if installed:**
```bash
ffmpeg -version
```

**Install on Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Install on MacOS:**
```bash
brew install ffmpeg
```

**Install on Windows:**
1. Download from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to PATH

#### Git (Optional)

```bash
# Ubuntu/Debian
sudo apt install git

# MacOS
brew install git
```

### System Requirements

- **OS**: Linux, MacOS, or Windows
- **RAM**: Minimum 4GB (8GB+ recommended for Whisper)
- **Disk Space**: 2GB+ free space
- **Internet**: Stable connection for API calls

---

## 2. Project Setup

### Step 1: Navigate to Project Directory

```bash
cd video_generation
```

Or if cloning from repository:
```bash
git clone <repository-url>
cd video_generation
```

### Step 2: Create Virtual Environment

**Linux/MacOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### Step 3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- FastAPI and Uvicorn (web server)
- Jinja2 (templating)
- OpenAI library (GPT-3.5, Whisper, DALL-E)
- Image processing libraries
- HTTP client libraries

**Installation time:** ~3-5 minutes (depends on internet speed)

### Step 4: Verify Installation

```bash
python -c "import fastapi, openai, whisper; print('✅ All libraries installed successfully!')"
```

If you see the success message, proceed to the next step.

---

## 3. API Credentials Setup

### 3.1 OpenAI API Key (Required)

OpenAI provides GPT-3.5 for content generation and Whisper for transcription.

#### Steps:

1. **Sign up/Login:**
   - Go to https://platform.openai.com/
   - Create account or login

2. **Create API Key:**
   - Navigate to https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Name it: "Video Pipeline"
   - Click "Create"

3. **Copy the key:**
   - Copy the key (starts with `sk-proj-` or `sk-`)
   - **IMPORTANT:** You won't be able to see it again!

4. **Save for later:**
   - Save it in a secure note or password manager
   - We'll add it to `.env` file in Step 4

#### Pricing:
- **Whisper:** $0.006 per minute of audio
- **GPT-3.5 Turbo:** $0.50 per 1M input tokens, $1.50 per 1M output tokens
- **Free credits:** $5 for new accounts

---

### 3.2 LinkedIn Developer App (Required for LinkedIn posting)

#### Steps:

1. **Create LinkedIn App:**
   - Go to https://www.linkedin.com/developers/apps
   - Click "Create app"
   - Fill in details:
     - **App name:** "Video to Social Media Pipeline"
     - **LinkedIn Page:** Select your company page (or create one)
     - **Privacy policy URL:** Your website or GitHub page
     - **App logo:** Upload any logo (optional)
   - Click "Create app"

2. **Configure OAuth:**
   - Go to "Auth" tab
   - Under "OAuth 2.0 settings":
     - **Redirect URLs:** Add `http://localhost:5000/auth/linkedin/callback`
     - Click "Update"

3. **Request Permissions:**
   - Still in "Auth" tab
   - Under "OAuth 2.0 scopes":
     - Check `r_liteprofile` (Read profile info)
     - Check `w_member_social` (Post content)
   - Click "Update"

4. **Get Credentials:**
   - In "Auth" tab, find:
     - **Client ID** (looks like: `77p9nd64sykgmv`)
     - **Client Secret** (click "Show" to reveal)
   - Copy both values

5. **Verify App:**
   - If prompted, verify your app via email
   - LinkedIn may require manual review for production use

#### Save these values:
```
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
```

---

### 3.3 Facebook Developer App (Optional - for Facebook & Instagram)

Facebook app handles both Facebook and Instagram posting.

#### Steps:

1. **Create Facebook Developer Account:**
   - Go to https://developers.facebook.com/
   - Click "Get Started"
   - Complete registration

2. **Create App:**
   - Click "My Apps" → "Create App"
   - Choose "Business" type
   - Fill in:
     - **App Display Name:** "Video Social Pipeline"
     - **App Contact Email:** Your email
   - Click "Create App"

3. **Add Facebook Login:**
   - In app dashboard, click "Add Product"
   - Find "Facebook Login" → Click "Set Up"
   - Choose "Web" platform
   - Site URL: `http://localhost:5000`
   - Save and continue

4. **Configure OAuth Settings:**
   - Go to "Facebook Login" → "Settings"
   - **Valid OAuth Redirect URIs:** Add:
     ```
     http://localhost:5000/auth/facebook/callback
     ```
   - Click "Save Changes"

5. **Get App Credentials:**
   - Go to "Settings" → "Basic"
   - Copy:
     - **App ID** (number like: `1551567226180556`)
     - **App Secret** (click "Show" and enter password)

6. **Request Permissions:**
   - Go to "App Review" → "Permissions and Features"
   - Request these permissions:
     - `pages_manage_posts` (Post to pages)
     - `pages_read_engagement` (Read page data)
     - `instagram_basic` (Access Instagram)
     - `instagram_content_publish` (Post to Instagram)
   - Note: Some require app review approval

7. **Link Instagram Account (for Instagram posting):**
   - Must have Instagram Business account
   - Link to a Facebook Page you manage
   - Steps:
     1. Open Instagram app
     2. Go to Settings → Account → Switch to Professional Account
     3. Choose "Business"
     4. Connect to your Facebook Page

#### Save these values:
```
FACEBOOK_APP_ID=your_app_id_here
FACEBOOK_APP_SECRET=your_app_secret_here
```

---

## 4. Environment Configuration

### Create `.env` File

In the project root directory:

**Linux/MacOS:**
```bash
nano .env
```

**Windows:**
```cmd
notepad .env
```

### Add Configuration

Paste the following and replace with your actual values:

```bash
# ===========================
# OpenAI API Key (REQUIRED)
# ===========================
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_KEY_HERE

# ===========================
# LinkedIn App Credentials (REQUIRED for LinkedIn)
# ===========================
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:5000/auth/linkedin/callback

# ===========================
# Facebook/Instagram App Credentials (OPTIONAL)
# ===========================
# Leave commented out if you don't have Facebook/Instagram integration
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
FACEBOOK_REDIRECT_URI=http://localhost:5000/auth/facebook/callback

# ===========================
# Session Security (CHANGE IN PRODUCTION!)
# ===========================
SECRET_KEY=dev-secret-key-change-in-production
```

### Generate Secure Secret Key (Production)

For production deployment, generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Replace `dev-secret-key-change-in-production` with the generated value.

### Verify Configuration

```bash
python -c "from app.config import Config; Config.validate_config()"
```

**Expected output:**
```
✅ All configuration loaded successfully
```
