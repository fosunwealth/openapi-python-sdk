import base64
import hashlib
import hmac
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class CryptoManager:
    @staticmethod
    def load_identity_private_key(pem_string):
        """从 PEM 字符串加载 ECDSA P-384 长期私钥"""
        return serialization.load_pem_private_key(
            pem_string.encode('utf-8'),
            password=None,
        )

    @staticmethod
    def load_identity_public_key(pem_string):
        """从 PEM 字符串加载 ECDSA P-384 长期公钥"""
        return serialization.load_pem_public_key(
            pem_string.encode('utf-8')
        )

    @staticmethod
    def generate_ecdh_key_pair():
        """生成 secp384r1 (P-384) 曲线的 ECDH 密钥对"""
        private_key = ec.generate_private_key(ec.SECP384R1())
        public_key = private_key.public_key()

        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )

        if len(public_bytes) > 97:
            public_bytes = public_bytes[-97:]
        elif len(public_bytes) == 96:
            public_bytes = b'\x04' + public_bytes

        return private_key, base64.b64encode(public_bytes).decode('utf-8')

    @staticmethod
    def sign_handshake(private_key, eph_pub_b64, nonce_b64):
        """使用客户端长期私钥对 SHA256(eph_pub_bytes + nonce_bytes) 进行 ECDSA 签名"""
        eph_pub_bytes = base64.b64decode(eph_pub_b64)
        nonce_bytes = base64.b64decode(nonce_b64)
        data_to_sign = eph_pub_bytes + nonce_bytes
        signature = private_key.sign(
            data_to_sign,
            ec.ECDSA(hashes.SHA256())
        )
        return base64.b64encode(signature).decode('utf-8')

    @staticmethod
    def verify_handshake(public_key, eph_pub_b64, nonce_b64, signature_b64):
        """使用服务端长期公钥验证服务端的握手签名"""
        eph_pub_bytes = base64.b64decode(eph_pub_b64)
        nonce_bytes = base64.b64decode(nonce_b64)
        signature = base64.b64decode(signature_b64)
        data_to_verify = eph_pub_bytes + nonce_bytes
        try:
            public_key.verify(
                signature,
                data_to_verify,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except Exception:
            return False

    @staticmethod
    def compute_shared_secret(private_key, server_public_key_b64, client_nonce_b64, server_nonce_b64):
        """计算共享密钥并通过 HKDF 一次派生 enc_key(32) + mac_key(32)"""
        server_public_bytes = base64.b64decode(server_public_key_b64)
        server_public_key = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP384R1(), server_public_bytes
        )
        shared_key = private_key.exchange(ec.ECDH(), server_public_key)

        client_nonce = base64.b64decode(client_nonce_b64)
        server_nonce = base64.b64decode(server_nonce_b64)

        derived_bytes = HKDF(
            algorithm=hashes.SHA256(),
            length=64,
            salt=client_nonce + server_nonce,
            info=b"session-derivation",
        ).derive(shared_key)

        enc_key = derived_bytes[:32]
        mac_key = derived_bytes[32:]
        # 返回顺序与调用方对齐：signing_key, encryption_key
        return mac_key, enc_key

    @staticmethod
    def build_response_aad(session_id: str, timestamp: str, nonce: str) -> str:
        """构造响应解密使用的 AAD"""
        return f"X-session:{session_id}|X-timestamp:{timestamp}|X-nonce:{nonce}"

    @staticmethod
    def encrypt_body(encryption_key, plaintext_bytes, aad_bytes):
        """使用 AES-256-GCM 加密 Body"""
        aesgcm = AESGCM(encryption_key)
        iv = os.urandom(12)
        ciphertext_with_tag = aesgcm.encrypt(iv, plaintext_bytes, aad_bytes)
        ciphertext = ciphertext_with_tag[:-16]
        tag = ciphertext_with_tag[-16:]
        return (
            base64.b64encode(iv).decode('utf-8'),
            base64.b64encode(ciphertext).decode('utf-8'),
            base64.b64encode(tag).decode('utf-8'),
        )

    @staticmethod
    def decrypt_body(encryption_key, iv_b64, ciphertext_b64, tag_b64, aad_bytes):
        """使用 AES-256-GCM 解密 Body"""
        aesgcm = AESGCM(encryption_key)
        iv = base64.b64decode(iv_b64)
        ciphertext = base64.b64decode(ciphertext_b64)
        tag = base64.b64decode(tag_b64)
        return aesgcm.decrypt(iv, ciphertext + tag, aad_bytes)

    @staticmethod
    def sign(session_key, method, path, query, timestamp, nonce, body_bytes):
        """计算请求 HMAC-SHA256 签名"""
        body_sha_hex = hashlib.sha256(body_bytes).hexdigest() if body_bytes else hashlib.sha256(b"").hexdigest()
        canonical_string = f"{method.upper()}\n{path}\n{query}\n{timestamp}\n{nonce}\n{body_sha_hex}"
        signature_bytes = hmac.new(
            session_key,
            canonical_string.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature_bytes).decode('utf-8')
