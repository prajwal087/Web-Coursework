import re
from config import Config


class PasswordValidator:
    """Enforce strong password requirements"""
    
    @staticmethod
    def validate(password):
        """
        Validate password meets security requirements.
        Returns (is_valid: bool, message: str)
        """
        if not password:
            return False, "Password is required"
        
        min_length = Config.PASSWORD_MIN_LENGTH
        if len(password) < min_length:
            return False, f"Password must be at least {min_length} characters"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain an uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain a lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain a number"
        
        if Config.REQUIRE_SPECIAL_CHARS:
            if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
                return False, "Password must contain a special character (!@#$%^&*)"
        
        return True, "Password is valid"


class EmailValidator:
    """Validate email format"""
    
    @staticmethod
    def validate(email):
        """Validate email format. Returns (is_valid: bool, message: str)"""
        if not email:
            return False, "Email is required"
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        return True, "Email is valid"


class UsernameValidator:
    """Validate username format"""
    
    @staticmethod
    def validate(username):
        """Validate username format. Returns (is_valid: bool, message: str)"""
        if not username:
            return False, "Username is required"
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if len(username) > 80:
            return False, "Username must be 80 characters or fewer"
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Username may only contain letters, numbers, underscores, and hyphens"
        
        return True, "Username is valid"
