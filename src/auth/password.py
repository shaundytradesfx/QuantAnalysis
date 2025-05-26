"""
Password hashing and verification utilities using bcrypt.
Follows OWASP password storage guidelines.
"""
import bcrypt
from typing import str


class PasswordManager:
    """
    Secure password hashing and verification using bcrypt.
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt with a strong cost factor.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password as a string
        """
        # Use cost factor of 12 for strong security (OWASP recommended)
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            hashed_password: Stored hash to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except Exception:
            # Return False for any exception (invalid hash format, etc.)
            return False
    
    @staticmethod
    def is_password_strong(password: str) -> tuple[bool, str]:
        """
        Check if password meets security requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if len(password) > 64:
            return False, "Password must be no more than 64 characters long"
        
        # Check for at least one uppercase, lowercase, digit, and special char
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            return False, "Password must contain uppercase, lowercase, digit, and special character"
        
        return True, "" 