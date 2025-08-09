"""
Test script for MongoDB integration.
Run this script to verify the MongoDB connection and user management.
"""
import os
import sys
from dotenv import load_dotenv
from database import db, initialize_users

# Load environment variables from .env file
load_dotenv()

def test_connection():
    """Test MongoDB connection"""
    try:
        # Test the connection by pinging the database
        db.client.admin.command('ping')
        print("✅ Successfully connected to MongoDB")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return False

def test_user_management():
    """Test user management functions"""
    test_username = "test_user_123"
    test_password = "test_password_123"
    test_role = "test_role"
    
    # Clean up test user if exists
    db.users.delete_one({"username": test_username})
    
    # Test add_user
    print("\nTesting add_user...")
    if db.add_user(test_username, test_password, test_role):
        print(f"✅ Successfully added test user: {test_username}")
    else:
        print("❌ Failed to add test user")
        return False
    
    # Test verify_user with correct password
    print("\nTesting verify_user with correct password...")
    user = db.verify_user(test_username, test_password)
    if user and user["username"] == test_username and user["role"] == test_role:
        print("✅ Successfully verified user with correct password")
    else:
        print("❌ Failed to verify user with correct password")
        return False
    
    # Test verify_user with incorrect password
    print("\nTesting verify_user with incorrect password...")
    user = db.verify_user(test_username, "wrong_password")
    if user is None:
        print("✅ Correctly rejected incorrect password")
    else:
        print("❌ Incorrectly accepted wrong password")
        return False
    
    # Test get_user
    print("\nTesting get_user...")
    user = db.get_user(test_username)
    if user and user["username"] == test_username and user["role"] == test_role:
        print("✅ Successfully retrieved user details")
    else:
        print("❌ Failed to retrieve user details")
        return False
    
    # Clean up
    db.users.delete_one({"username": test_username})
    return True

def test_initialize_users():
    """Test user initialization"""
    print("\nTesting user initialization...")
    try:
        # Clean up any existing test users
        test_usernames = ["Tony", "Bruce", "Sam", "Peter", "Sid", "Natasha"]
        db.users.delete_many({"username": {"$in": test_usernames}})
        
        success_count, total_users, errors = initialize_users()
        
        if errors:
            print(f"⚠️  Encountered {len(errors)} errors during user initialization:")
            for error in errors:
                print(f"   - {error}")
        
        if success_count == total_users:
            print(f"✅ Successfully initialized {success_count}/{total_users} users")
            return True
        else:
            print(f"❌ Only initialized {success_count}/{total_users} users")
            return False
    except Exception as e:
        print(f"❌ Error during user initialization test: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Testing MongoDB Integration ===")
    
    # Check if required environment variables are set
    required_vars = ['MONGO_URI']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file with these variables. See .env.example")
        sys.exit(1)
    
    # Run tests
    connection_ok = test_connection()
    
    if connection_ok:
        print("\n=== Running User Management Tests ===")
        user_tests_ok = test_user_management()
        
        print("\n=== Running User Initialization Test ===")
        init_ok = test_initialize_users()
        
        if user_tests_ok and init_ok:
            print("\n✅ All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
    else:
        print("\n❌ Connection test failed. Please check your MongoDB connection details.")
        sys.exit(1)
