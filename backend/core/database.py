"""
Database module for MongoDB operations.
Handles connection, encryption, and data persistence.
FIXED VERSION - Better error handling and connection testing
"""

import hashlib
import base64
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from cryptography.fernet import Fernet
from core.config import settings
import os

class DatabaseManager:
    """Manages all MongoDB operations and encryption/decryption."""
    
    def __init__(self):
        """Initialize database connection and encryption."""
        print("🔄 Initializing database connection...")
        
        # Initialize MongoDB connection
        try:
            self.client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000  # 5 second timeout
            )
            
            # Test connection
            self.client.admin.command('ping')
            print("✅ MongoDB connection successful")
            
            self.db = self.client[settings.MONGODB_DB]
            self.patients = self.db["patients"]
            self.doctors = self.db["doctors"]
            self.admins = self.db["admins"]
            
            # Create indexes for better performance
            self.patients.create_index("demographic")
            self.doctors.create_index("email")
            self.admins.create_index("email")
            
        except (ServerSelectionTimeoutError, ConnectionFailure) as e:
            print(f"❌ MongoDB connection failed: {e}")
            print(f"   Check your MONGODB_URI in .env file")
            print(f"   Current URI: {settings.MONGODB_URI[:20]}...")
            raise Exception("Cannot connect to MongoDB. Please check your connection string.")
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            raise
        
        # Initialize encryption
        try:
            key = settings.get_encryption_key()
            self.cipher_suite = Fernet(key)
            print("✅ Encryption initialized")
        except Exception as e:
            print(f"❌ Encryption setup failed: {e}")
            raise
    
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
        try:
            encrypted_data = self.cipher_suite.encrypt(data_string.encode('utf-8'))
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            print(f"Encryption error: {e}")
            return data_string
    
    def decrypt_data(self, encrypted_data):
        """Decrypt a string that was encrypted with Fernet."""
        if not encrypted_data:
            return encrypted_data
        try:
            decrypted_data = self.cipher_suite.decrypt(base64.b64decode(encrypted_data.encode('utf-8')))
            return decrypted_data.decode('utf-8')
        except Exception as e:
            print(f"Decryption error: {e}")
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
    
    def test_connection(self):
        """Test if database connection is working"""
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def close(self):
        """Close the database connection."""
        try:
            self.client.close()
            print("✅ Database connection closed")
        except Exception as e:
            print(f"Error closing connection: {e}")


# Global database instance
try:
    db_manager = DatabaseManager()
except Exception as e:
    print(f"❌ CRITICAL: Could not initialize database manager: {e}")
    print("   Please fix the error above before starting the server")
    db_manager = None