"""
Response encryption utility using AES-256.
"""

import base64
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os

from src.core.config import settings

# Get encryption key from environment
ENCRYPTION_KEY = settings.ENCRYPTION_KEY.encode('utf-8')

# Ensure key is exactly 32 bytes
if len(ENCRYPTION_KEY) != 32:
    raise ValueError("Encryption key must be exactly 32 bytes for AES-256")


def encrypt_response(data: dict) -> dict:
    """
    Encrypt a JSON response using AES-256-CBC.
    
    Args:
        data: Dictionary to encrypt
        
    Returns:
        Dictionary with encrypted data and metadata
    """
    try:
        # Convert data to JSON string
        json_str = json.dumps(data)
        json_bytes = json_str.encode('utf-8')
        
        # Generate random IV (16 bytes for AES)
        iv = os.urandom(16)
        
        # Pad the data to be multiple of 128 bits (16 bytes)
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(json_bytes) + padder.finalize()
        
        # Create cipher and encrypt
        cipher = Cipher(
            algorithms.AES(ENCRYPTION_KEY),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Encode to base64 for JSON transmission
        encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
        iv_b64 = base64.b64encode(iv).decode('utf-8')
        
        return {
            "encrypted": True,
            "algorithm": "AES-256-CBC",
            "data": encrypted_b64,
            "iv": iv_b64,
            "encoding": "base64"
        }
    except Exception as e:
        # If encryption fails, return original data with error
        return {
            "encrypted": False,
            "error": str(e),
            "data": data
        }


def decrypt_response(encrypted_data: str, iv: str) -> dict:
    """
    Decrypt an encrypted response.
    
    Args:
        encrypted_data: Base64-encoded encrypted data
        iv: Base64-encoded initialization vector
        
    Returns:
        Decrypted dictionary
    """
    try:
        # Decode from base64
        encrypted_bytes = base64.b64decode(encrypted_data)
        iv_bytes = base64.b64decode(iv)
        
        # Create cipher and decrypt
        cipher = Cipher(
            algorithms.AES(ENCRYPTION_KEY),
            modes.CBC(iv_bytes),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_bytes) + decryptor.finalize()
        
        # Unpad the data
        unpadder = padding.PKCS7(128).unpadder()
        json_bytes = unpadder.update(padded_data) + unpadder.finalize()
        
        # Convert back to dictionary
        json_str = json_bytes.decode('utf-8')
        return json.loads(json_str)
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")
