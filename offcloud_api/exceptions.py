class OffcloudError(Exception):
    """Base exception for all Offcloud API errors"""
    pass

class HTTPError(OffcloudError):
    """HTTP error responses"""
    def __init__(self, status_code: int, message: str):
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.message = message

class AuthError(HTTPError):
    """Authentication errors (401)"""
    pass

class NotFoundError(HTTPError):
    """Resource not found errors (404)"""
    pass

class RateLimitError(HTTPError):
    """Rate limit exceeded errors (429)"""
    pass

class BadRequestError(HTTPError):
    """Bad request errors (400)"""
    pass

class ServerError(HTTPError):
    """Server errors (5xx)"""
    pass

class TemporaryError(OffcloudError):
    """Temporary errors that can be retried"""
    pass

class FeatureNotAvailableError(OffcloudError):
    """Feature requires premium or is not available"""
    def __init__(self, feature: str):
        super().__init__(f"Feature not available: {feature}")
        self.feature = feature

class DownloadError(OffcloudError):
    """Download-specific errors"""
    pass