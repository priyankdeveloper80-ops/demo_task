"""Custom exceptions for social media API errors"""

class TokenExpiredException(Exception):
    """Raised when an access token is expired or revoked"""
    def __init__(self, platform, message=None):
        self.platform = platform
        self.message = message or f"{platform} access token has expired or been revoked"
        super().__init__(self.message)
