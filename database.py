import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError, ConnectionFailure
import bcrypt
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class Database:
    def __init__(self):
        """Initialize database connection and ensure indexes"""
        try:
            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                raise ValueError("MONGO_URI environment variable is not set")
                
            self.client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=30000,        # 30 second connection timeout
                socketTimeoutMS=45000,          # 45 second socket timeout
                connect=False                   # Lazy connection
            )
            
            # Test the connection
            self.client.admin.command('ping')
            
            self.db = self.client[os.getenv("DB_NAME", "rag_system")]
            self.users = self.db["users"]
            self._create_indexes()
            logger.info("Successfully connected to MongoDB")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def _create_indexes(self):
        """Create necessary database indexes"""
        try:
            # Create unique index on username
            self.users.create_index("username", unique=True)
            logger.info("Created database indexes")
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
            raise
    
    def add_user(self, username: str, password: str, role: str) -> bool:
        """Add a new user to the database"""
        if not username or not password or not role:
            logger.warning("Missing required fields for user creation")
            return False
            
        try:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            user_data = {
                "username": username,
                "password": hashed.decode('utf-8'),
                "role": role.lower(),
                "created_at": datetime.utcnow(),
                "last_login": None
            }
            
            result = self.users.insert_one(user_data)
            if result.inserted_id:
                logger.info(f"Created new user: {username}")
                return True
            return False
            
        except DuplicateKeyError:
            logger.warning(f"Username already exists: {username}")
            return False
        except Exception as e:
            logger.error(f"Error adding user {username}: {str(e)}")
            return False
    
    def verify_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify user credentials"""
        try:
            user = self.users.find_one({"username": username})
            if not user:
                logger.warning(f"Login attempt for non-existent user: {username}")
                return None
                
            if bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
                # Update last login time
                self.users.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"last_login": datetime.utcnow()}}
                )
                logger.info(f"Successful login for user: {username}")
                return {
                    "username": user["username"],
                    "role": user["role"],
                    "last_login": user.get("last_login")
                }
            
            logger.warning(f"Failed login attempt for user: {username}")
            return None
            
        except Exception as e:
            logger.error(f"Error verifying user {username}: {str(e)}")
            return None
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username (without sensitive data)"""
        try:
            user = self.users.find_one(
                {"username": username},
                {"password": 0}  # Exclude password from results
            )
            return user
        except Exception as e:
            logger.error(f"Error fetching user {username}: {str(e)}")
            return None

# Initialize database connection
db = Database()

def initialize_users():
    """
    Initialize default users if they don't exist.
    Returns tuple of (success_count, total_users, errors)
    """
    from datetime import datetime
    
    default_users = [
        {"username": "Tony", "password": "password123", "role": "engineering"},
        {"username": "Bruce", "password": "securepass", "role": "marketing"},
        {"username": "Sam", "password": "financepass", "role": "finance"},
        {"username": "Peter", "password": "pete123", "role": "engineering"},
        {"username": "Sid", "password": "sidpass123", "role": "marketing"},
        {"username": "Natasha", "password": "hrpass123", "role": "hr"}
    ]
    
    success_count = 0
    errors = []
    
    for user in default_users:
        try:
            if db.add_user(user["username"], user["password"], user["role"]):
                success_count += 1
                logger.info(f"Initialized user: {user['username']}")
            else:
                errors.append(f"Failed to add user: {user['username']}")
        except Exception as e:
            error_msg = f"Error initializing user {user['username']}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    logger.info(f"User initialization complete. Success: {success_count}/{len(default_users)}")
    if errors:
        logger.warning(f"Encountered {len(errors)} errors during user initialization")
    
    return success_count, len(default_users), errors
