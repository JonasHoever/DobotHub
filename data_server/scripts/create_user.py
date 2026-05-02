#!/usr/bin/env python3
"""
data_server/scripts/create_user.py — Create a new user account
Usage: python scripts/create_user.py --username john --password secret123 --email john@example.com
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from app import create_app, db
from models import User
from utils import generate_uuid, hash_password


def main():
    parser = argparse.ArgumentParser(description="Create a new user account")
    parser.add_argument("--username", required=True, help="Username")
    parser.add_argument("--password", required=True, help="Password")
    parser.add_argument("--email", required=False, help="Email address")
    parser.add_argument("--env", default="development", help="Flask environment")
    
    args = parser.parse_args()
    
    # Create app context
    app = create_app(args.env)
    
    with app.app_context():
        # Check if user already exists
        existing = User.query.filter_by(username=args.username).first()
        if existing:
            print(f"Error: User '{args.username}' already exists")
            sys.exit(1)
        
        # Create user
        user = User(
            id=generate_uuid(),
            username=args.username,
            password_hash=hash_password(args.password),
            email=args.email,
            is_active=True
        )
        
        db.session.add(user)
        db.session.commit()
        
        print(f"✓ User '{args.username}' created successfully")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email or 'N/A'}")


if __name__ == "__main__":
    main()
