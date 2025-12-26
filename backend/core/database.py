"""
Database module for MongoDB operations.
Handles connection, encryption, and data persistence.
"""

import hashlib
import base64
from pymongo import MongoClient
from cryptography.fernet import Fernet
from core.config import settings
import os

class DatabaseManager:
    """Manages all MongoDB operations and encryption/decryption."""
    
    def __init__(self):
        """Initialize database connection and encryption."""
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_DB]
        self.patients = self.db["patients"]
        self.doctors = self.db["doctors"]
        self.admins = self.db["admins"]
        self.cipher_suite = Fernet(self._get_encryption_key())
    
    @staticmethod
    def _get_encryption_key():
        """Get or create encryption key."""
        # Try to get from environment
        if settings.ENCRYPTION_KEY:
            return settings.ENCRYPTION_KEY.encode()
        
        # Try to read from file
        key_file = "encryption_key.key"
        try:
            with open(key_file, "rb") as f:
                key = f.read()
        except FileNotFoundError:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
        return key
    
    @staticmethod
    def hash_password(password):
        """Create a SHA-256 hash of the password."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(stored_hash, provided_password):
        """Verify a stored password hash against a provided password."""
        return stored_hash == DatabaseManager.hash_password(provided_password)
    
    def encrypt_data(self, data_string):
        """Encrypt a string using Fernet (AES)."""
        if not data_string:
            return data_string
        encrypted_data = self.cipher_suite.encrypt(data_string.encode('utf-8'))
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt_data(self, encrypted_data):
        """Decrypt a string that was encrypted with Fernet."""
        if not encrypted_data:
            return encrypted_data
        try:
            decrypted_data = self.cipher_suite.decrypt(base64.b64decode(encrypted_data.encode('utf-8')))
            return decrypted_data.decode('utf-8')
        except Exception as e:
            return encrypted_data  # Return as-is if decryption fails
    
    def encrypt_dict(self, data_dict):
        """Recursively encrypt values in a dictionary."""
        encrypted_dict = {}
        for key, value in data_dict.items():
            if isinstance(value, dict):
                encrypted_dict[key] = self.encrypt_dict(value)
            elif isinstance(value, list):
                encrypted_dict[key] = [self.encrypt_data(str(item)) if isinstance(item, str) else item for item in value]
            elif isinstance(value, str):
                encrypted_dict[key] = self.encrypt_data(value)
            else:
                encrypted_dict[key] = value
        return encrypted_dict
    
    def decrypt_dict(self, encrypted_dict):
        """Recursively decrypt values in a dictionary."""
        decrypted_dict = {}
        for key, value in encrypted_dict.items():
            if isinstance(value, dict):
                decrypted_dict[key] = self.decrypt_dict(value)
            elif isinstance(value, list):
                decrypted_dict[key] = [self.decrypt_data(item) if isinstance(item, str) else item for item in value]
            elif isinstance(value, str):
                decrypted_dict[key] = self.decrypt_data(value)
            else:
                decrypted_dict[key] = value
        return decrypted_dict
    
    def close(self):
        """Close the database connection."""
        self.client.close()


# Global database instance
db_manager = DatabaseManager()