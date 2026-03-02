import base64
import hashlib
import hmac
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class CryptoManager:
    @staticmethod
    def generate_ecdh_key_pair():
        """生成 secp384r1 (P-384) 曲线的 ECDH 密钥对"""
        private_key = ec.generate_private_key(ec.SECP384R1())
        public_key = private_key.public_key()
        
        # 导出原始未压缩点数据 (X9.62 Uncompressed)
        # 目标格式: 0x04 (1字节) + X (48字节) + Y (48字节) = 严格 97 字节
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        
        # 核心修正：跨语言对接时，强制确保字节流长度为 97 字节
        if len(public_bytes) > 97:
            # 如果有多余的前缀，截取最后 97 字节
            public_bytes = public_bytes[-97:]
        elif len(public_bytes) == 96:
            # 如果缺失 0x04 标识位，手动补齐
            public_bytes = b'\x04' + public_bytes
            
        return private_key, base64.b64encode(public_bytes).decode('utf-8')

    @staticmethod
    def compute_shared_secret(private_key, server_public_key_b64):
        """计算共享密钥并派生双密钥 (对齐 Go 的 big.Int.Bytes() 行为)"""
        server_public_bytes = base64.b64decode(server_public_key_b64)
        server_public_key = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP384R1(), server_public_bytes
        )
        
        shared_key = private_key.exchange(ec.ECDH(), server_public_key)
        
        shared_key_stripped = shared_key.lstrip(b'\x00')
        
        # 1. 派生签名密钥 (Signing Key)
        signing_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"openapi-session-salt",
            info=b"openapi-signing-key",
        ).derive(shared_key_stripped)
        
        # 2. 派生加密密钥 (Encryption Key)
        encryption_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"openapi-session-salt",
            info=b"openapi-encryption-key",
        ).derive(shared_key_stripped)
        
        return signing_key, encryption_key

    @staticmethod
    def encrypt_body(encryption_key, plaintext_bytes, aad_bytes):
        """使用 AES-256-GCM 加密 Body"""
        aesgcm = AESGCM(encryption_key)
        iv = os.urandom(12) # GCM 推荐 12 字节 IV
        
        # 加密结果包含 ciphertext + tag (cryptography 库自动处理 tag)
        ciphertext_with_tag = aesgcm.encrypt(iv, plaintext_bytes, aad_bytes)
        
        # 分离 tag (最后 16 字节)
        ciphertext = ciphertext_with_tag[:-16]
        tag = ciphertext_with_tag[-16:]
        
        return base64.b64encode(iv).decode('utf-8'), \
               base64.b64encode(ciphertext).decode('utf-8'), \
               base64.b64encode(tag).decode('utf-8')

    @staticmethod
    def decrypt_body(encryption_key, iv_b64, ciphertext_b64, tag_b64, aad_bytes):
        """使用 AES-256-GCM 解密 Body"""
        aesgcm = AESGCM(encryption_key)
        iv = base64.b64decode(iv_b64)
        ciphertext = base64.b64decode(ciphertext_b64)
        tag = base64.b64decode(tag_b64)
        
        # cryptography 库要求 ciphertext 包含 tag
        plaintext_bytes = aesgcm.decrypt(iv, ciphertext + tag, aad_bytes)
        return plaintext_bytes

    @staticmethod
    def sign(session_key, method, path, query, timestamp, nonce, body_bytes):
        """
        计算 HMAC-SHA256 签名
        """
        # 1. 计算 Body 的 SHA256 Hex 摘要
        body_sha_hex = hashlib.sha256(body_bytes).hexdigest() if body_bytes else hashlib.sha256(b"").hexdigest()
        
        # 2. 构建规范字符串: {Method}\n{Path}\n{Query}\n{Timestamp}\n{Nonce}\n{BodySHAHex}
        canonical_string = f"{method.upper()}\n{path}\n{query}\n{timestamp}\n{nonce}\n{body_sha_hex}"
        
        # 调试打印：输出待签名字符串
        debug_string = canonical_string.replace('\n', '[NL]')
        
        # 3. HMAC-SHA256 签名
        signature_bytes = hmac.new(
            session_key,
            canonical_string.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
        
        # 4. 网关要求 Base64 编码
        return signature_b64
