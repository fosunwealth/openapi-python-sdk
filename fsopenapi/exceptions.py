class APIError(Exception):
    """API 业务错误异常"""
    def __init__(self, code, message, request_id=None, data=None):
        self.code = code
        self.message = message
        self.request_id = request_id
        self.data = data
        super().__init__(f"API Error {code}: {message} (Request ID: {request_id})")

class AuthenticationError(APIError):
    """鉴权相关错误"""
    pass

class PermissionError(APIError):
    """权限相关错误"""
    pass

class RateLimitError(APIError):
    """限流相关错误"""
    pass

class CacheError(APIError):
    """缓存相关错误（通常表示服务端缓存操作失败）"""
    pass
