"""
会话管理 API
"""

from typing import Optional, Dict, Any


class SessionAPI:
    """会话管理 API"""

    def __init__(self, client):
        self.client = client

    def create_session(self) -> Dict[str, Any]:
        """创建会话"""
        return self.client.auth_manager.create_session()
    
    def query_session(self) -> Dict[str, Any]:
        """查询当前会话"""
        return self.client.post("/v1/auth/SessionQuery", data={})
    
    def delete_session(self) -> Dict[str, Any]:
        """删除当前会话"""
        result = self.client.post("/v1/auth/SessionDelete", data={})
        self.client.auth_manager.session_id = None
        self.client.auth_manager.signing_key = None
        self.client.auth_manager.encryption_key = None
        self.client.auth_manager.expires_at = 0
        return result
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """
        获取当前会话信息（本地缓存）
        
        返回本地缓存的会话信息，不会发起网络请求。
        如果会话不存在或已过期，返回 None。
        
        Returns:
            Optional[Dict[str, Any]]: 会话信息字典，包含 sessionId, expiresAt 等
        """
        if not self.client.auth_manager.session_id:
            return None
        
        return {
            "sessionId": self.client.auth_manager.session_id,
            "expiresAt": self.client.auth_manager.expires_at,
            "isExpired": self.client.auth_manager.expires_at < self.client.auth_manager._get_current_timestamp(),
        }
    
    def is_session_valid(self) -> bool:
        """
        检查当前会话是否有效
        
        检查本地缓存的会话是否仍然有效（未过期）。
        
        Returns:
            bool: 如果会话存在且未过期返回 True，否则返回 False
        """
        if not self.client.auth_manager.session_id:
            return False
        
        # 提前 60 秒认为过期
        import time
        return time.time() < (self.client.auth_manager.expires_at - 60)
