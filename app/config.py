import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # LinkedIn Credentials
    LINKEDIN_CLIENT_ID = os.environ.get('LINKEDIN_CLIENT_ID')
    LINKEDIN_CLIENT_SECRET = os.environ.get('LINKEDIN_CLIENT_SECRET') 
    LINKEDIN_REDIRECT_URI = os.environ.get('LINKEDIN_REDIRECT_URI') 
    
    # Facebook/Instagram Credentials (same app handles both)
    FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID')
    FACEBOOK_APP_SECRET = os.environ.get('FACEBOOK_APP_SECRET')
    FACEBOOK_REDIRECT_URI = os.environ.get('FACEBOOK_REDIRECT_URI')
    
    # OpenAI API Key
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        missing = []
        warnings = []
        
        # Required credentials
        if not cls.OPENAI_API_KEY:
            missing.append('OPENAI_API_KEY')
        if not cls.LINKEDIN_CLIENT_ID:
            missing.append('LINKEDIN_CLIENT_ID')
        if not cls.LINKEDIN_CLIENT_SECRET:
            missing.append('LINKEDIN_CLIENT_SECRET')
        
        # Optional but recommended for full functionality
        if not cls.FACEBOOK_APP_ID:
            warnings.append('FACEBOOK_APP_ID (Facebook/Instagram posting disabled)')
        if not cls.FACEBOOK_APP_SECRET:
            warnings.append('FACEBOOK_APP_SECRET (Facebook/Instagram posting disabled)')
        
        if missing:
            print(f"⚠️ Missing required configuration: {', '.join(missing)}")
        if warnings:
            print(f"ℹ️ Optional configuration not set: {', '.join(warnings)}")
        if not missing and not warnings:
            print("✅ All configuration loaded successfully")
        elif not missing:
            print("✅ Required configuration loaded successfully")
        
        return len(missing) == 0
    
    UPLOAD_FOLDER = 'uploads'
    IMAGES_FOLDER = 'images'
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
