from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import os
from src.utils.helpers import load_json_file, save_json_file
from src.rag.retriever import RAGRetriever

# -qU 

class CreateUserInput(BaseModel):
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    age: Optional[int] = Field(None, description="User's age")
    role: Optional[str] = Field(None, description="User's role")

class UpdateUserInput(BaseModel):
    email: str = Field(..., description="Email of the user to update")
    data: Dict[str, Any] = Field(..., description="Data to update")

class DeleteUserInput(BaseModel):
    email: str = Field(..., description="Email of the user to delete")

class GetUsersInput(BaseModel):
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters for the query")

class DatabaseTools:
    """Tools for interacting with the MongoDB database"""
    
    def __init__(self, mongodb_client):
        """Initialize database tools
        
        Args:
            mongodb_client: MongoDB client instance
        """
        self.mongodb = mongodb_client
        self.json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "user.json")
        # Initialize RAG retriever for refreshing data
        self.retriever = RAGRetriever(self.json_path)
    
    def create_user(self, input_data: CreateUserInput) -> str:
        """Create a new user in the database
        
        Args:
            input_data: User data to create
            
        Returns:
            str: Result message
        """
        # Convert pydantic model to dict
        try:
            # Try different pydantic versions
            if hasattr(input_data, "model_dump"):
                # Pydantic v2
                user_data = input_data.model_dump(exclude_none=True)
            else:
                # Pydantic v1
                user_data = input_data.dict(exclude_none=True)
            
            # Ensure only relevant fields
            user_data = {k: v for k, v in user_data.items() if k in ["name", "email", "age", "role"]}
        except Exception as e:
            print(f"Error converting model to dict: {e}")
            # Fallback to manual dictionary creation
            user_data = {}
            if hasattr(input_data, "name") and input_data.name:
                user_data["name"] = input_data.name
            if hasattr(input_data, "email") and input_data.email:
                user_data["email"] = input_data.email
            if hasattr(input_data, "age") and input_data.age is not None:
                user_data["age"] = input_data.age
            if hasattr(input_data, "role") and input_data.role:
                user_data["role"] = input_data.role
        
        # Check if user with same email already exists
        existing_users = self.mongodb.get_users({"email": user_data.get("email")})
        if existing_users:
            return f"User with email {user_data.get('email')} already exists."
        
        # Insert user into database
        result = self.mongodb.create_user(user_data)
        
        if result:
            # Refresh RAG data to maintain consistency - wrap in try/except to prevent cascading errors
            try:
                self.retriever.refresh_data()
            except Exception as e:
                print(f"Warning: Failed to refresh RAG data: {e}")
            
            # Serialize the user data safely
            try:
                user_json = json.dumps(user_data, default=str)
            except Exception:
                # If serialization fails, create a simpler dict
                simple_data = {
                    "name": str(user_data.get("name", "")),
                    "email": str(user_data.get("email", ""))
                }
                if "age" in user_data:
                    simple_data["age"] = int(user_data.get("age", 0))
                if "role" in user_data:
                    simple_data["role"] = str(user_data.get("role", ""))
                user_json = json.dumps(simple_data)
            
            return f"User created successfully: {user_json}"
        else:
            return "Failed to create user"
    
    def get_users(self, input_data: Optional[GetUsersInput] = None) -> str:
        """Get users from the database
        
        Args:
            input_data: Optional filters
            
        Returns:
            str: Result message with users
        """
        filters = None
        if input_data and input_data.filters:
            filters = input_data.filters
        
        users = self.mongodb.get_users(filters)
        
        if users:
            try:
                return f"Found {len(users)} users: {json.dumps(users, indent=2, default=str)}"
            except Exception as e:
                print(f"Error serializing users: {e}")
                return f"Found {len(users)} users, but couldn't display them due to serialization error."
        else:
            return "No users found"
    
    def update_user(self, input_data: UpdateUserInput) -> str:
        """Update a user in the database
        
        Args:
            input_data: User email and data to update
            
        Returns:
            str: Result message
        """
        email = input_data.email
        update_data = input_data.data
        
        # Check if user exists
        existing_users = self.mongodb.get_users({"email": email})
        if not existing_users:
            return f"User with email {email} not found."
        
        result = self.mongodb.update_user(email, update_data)
        
        if result:
            # Refresh RAG data
            try:
                self.retriever.refresh_data()
            except Exception as e:
                print(f"Warning: Failed to refresh RAG data: {e}")
                
            try:
                return f"User {email} updated successfully with: {json.dumps(update_data, default=str)}"
            except Exception as e:
                print(f"Error serializing update data: {e}")
                return f"User {email} updated successfully."
        else:
            return f"Failed to update user {email}"
    
    def delete_user(self, input_data: DeleteUserInput) -> str:
        """Delete a user from the database
        
        Args:
            input_data: User email to delete
            
        Returns:
            str: Result message
        """
        email = input_data.email
        
        # Check if user exists
        existing_users = self.mongodb.get_users({"email": email})
        if not existing_users:
            return f"User with email {email} not found."
        
        result = self.mongodb.delete_user(email)
        
        if result:
            # Refresh RAG data
            try:
                self.retriever.refresh_data()
            except Exception as e:
                print(f"Warning: Failed to refresh RAG data: {e}")
                
            return f"User {email} deleted successfully"
        else:
            return f"Failed to delete user {email}"