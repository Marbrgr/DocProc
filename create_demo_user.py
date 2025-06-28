#!/usr/bin/env python3
"""
Create Demo User Script for DocuMind AI
Run this script to create a demo user for testing/demo purposes.
"""

import sys
import os

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_path)

from sqlalchemy.orm import Session
from app.database import get_db, engine
from app.models import User
from app.utils.auth import hash_password
import uuid

def create_demo_user():
    """Create a demo user for testing purposes"""
    
    # Demo user credentials
    demo_username = "demo"
    demo_email = "demo@documind.ai"
    demo_password = "demo123"  # Simple password for demo
    
    print("🚀 Creating DocuMind AI Demo User...")
    
    # Create database session
    db = Session(engine)
    
    try:
        # Check if demo user already exists
        existing_user = db.query(User).filter(User.username == demo_username).first()
        if existing_user:
            print(f"✅ Demo user '{demo_username}' already exists!")
            print(f"   Username: {demo_username}")
            print(f"   Password: {demo_password}")
            return
        
        # Hash the password
        hashed_password = hash_password(demo_password)
        
        # Create new demo user
        demo_user = User(
            id=uuid.uuid4(),
            username=demo_username,
            email=demo_email,
            password=hashed_password,
            documents_processed=0,
            is_admin=True  # Give admin privileges for demo
        )
        
        # Add to database
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        
        print("✅ Demo user created successfully!")
        print(f"   Username: {demo_username}")
        print(f"   Email: {demo_email}")
        print(f"   Password: {demo_password}")
        print(f"   User ID: {demo_user.id}")
        print("\n🎯 You can now log in to DocuMind AI with these credentials!")
        
    except Exception as e:
        print(f"❌ Error creating demo user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_demo_user() 