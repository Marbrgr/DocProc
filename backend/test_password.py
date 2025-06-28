#!/usr/bin/env python3
"""
Test password hashing and verification
"""

from app.utils.auth import hash_password, verify_password
from sqlalchemy.orm import Session
from app.database import engine
from app.models import User

def test_password():
    print("🔍 Testing password hashing...")
    
    # Test the hashing functions
    test_password = "demo123"
    hashed = hash_password(test_password)
    print(f"Original password: {test_password}")
    print(f"Hashed password: {hashed}")
    
    # Test verification
    is_valid = verify_password(test_password, hashed)
    print(f"Verification result: {is_valid}")
    
    # Check what's in the database
    print("\n🔍 Checking database...")
    db = Session(engine)
    try:
        user = db.query(User).filter(User.username == "demo").first()
        if user:
            print(f"User found: {user.username}")
            print(f"Email: {user.email}")
            print(f"Stored password hash: {user.password}")
            
            # Test verification against stored hash
            is_valid_db = verify_password(test_password, user.password)
            print(f"Verification against DB hash: {is_valid_db}")
        else:
            print("User not found in database!")
    finally:
        db.close()

if __name__ == "__main__":
    test_password() 