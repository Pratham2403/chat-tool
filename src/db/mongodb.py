import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

load_dotenv()

class MongoDB:
    """MongoDB Database Connection Class."""
    
    def __init__(self):
        """Initialize MongoDB connection."""
        self.uri = os.getenv("MONGODB_URI")
        self.client = None
        self.db = None
        
    def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            
            #Test the Connection
            self.client.admin.command('ping')
            self.db = self.client["chat-tool"]
            print("MongoDB connection established.")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"MongoDB connection error: {e}")
            return False
        
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")
        else:
            print("No MongoDB connection to close.")


    def create_user(self, user_data):
        """Create User in the MongoDB Database
        
        Args:
            user_data (dict): User data to be inserted into the database.
            
        Returns:
            str : The ID of the inserted user or None if the insertion failed.
        """
        
        try:
            collection = self.db["users"]
            result = collection.insert_one(user_data)
            
            
            return str(result.inserted_id)

        except Exception as e:
            print(f"Error creating user: {e}")
            return None
        
        
        
    def get_users(self, query=None):
        """Get Users from the MongoDB Database
        
        Args:
            query (dict, optional): Query to filter users. Defaults to None.
            
        Returns:
            list : List of users matching the query or all users if no query is provided.
        """
        
        try:
            collection = self.db["users"]
            if query:
                # Exclude the _id field from the results
                return list(collection.find(query, {"_id": 0}))
            else:
                return list(collection.find({}, {"_id": 0}))

        except Exception as e:
            print(f"Error getting users: {e}")
            return []
                
                
                
    def update_user(self, email, update_data):
        """Update User in the MongoDB Database
        
        Args:
            email (str): Email of the user to be updated.
            update_data (dict): Data to update the user with.
            
        Returns:
            bool : True if the update was successful, False otherwise.
        """
        
        try:
            collection = self.db["users"]
            result = collection.update_one({"email": email}, {"$set": update_data})
            
            return result.modified_count > 0

        except Exception as e:
            print(f"Error updating user: {e}")
            return False
        
    def delete_user(self, email):
        """Delete User from the MongoDB Database
        
        Args:
            email (str): Email of the user to be deleted.
            
        Returns:
            bool : True if the deletion was successful, False otherwise.
        """
        
        try:
            collection = self.db["users"]
            result = collection.delete_one({"email": email})
            
            return result.deleted_count > 0

        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
