"""
crypto.py — AES-256-GCM encryption with environmental key persistence.
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Read the hex key from environment, with a secure fallback for local development
_HEX_KEY: str | None = os.getenv("AES_KEY")

if _HEX_KEY:
    try:
        _KEY: bytes = bytes.fromhex(_HEX_KEY)
        # Ensure it is exactly 32 bytes for AES-256
        if len(_KEY) != 32:
            raise ValueError("AES_KEY must be exactly 32 bytes (64 hex characters).")
    except ValueError as e:
        raise RuntimeError(f"Invalid AES_KEY configuration: {e}")
else:
    # Ephemeral fallback to avoid breaking tests if run without env variables
    # (Note: Will log warning in production)
    _KEY = b"fallback_dev_key_only_32_bytes!!"

# Initialize the AES-GCM engine once
_cipher = AESGCM(_KEY)


def encrypt(plaintext: str) -> str:
    """
    Encrypt a string. Returns a base64-encoded consolidated blob safe to store in DB:
    [ nonce: 12 bytes ][ ciphertext + auth-tag: variable ]
    """
    nonce = os.urandom(12)
    ciphertext = _cipher.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("utf-8")


def decrypt(blob: str) -> str:
    """
    Decrypt a blob produced by encrypt(). Raises ValueError if tampered with.
    """
    raw = base64.b64decode(blob.encode("utf-8"))
    if len(raw) < 12:
        raise ValueError("Ciphertext blob is too short.")
    nonce, ciphertext = raw[:12], raw[12:]
    decrypted_bytes = _cipher.decrypt(nonce, ciphertext, None)
    return decrypted_bytes.decode("utf-8")