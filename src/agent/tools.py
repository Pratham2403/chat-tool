from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import os
from src.utils.helpers import load_json_file, save_json_file
from src.rag.retriever import RAGRetriever

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
        user_data = input_data.model_dump(exclude_none=True, include=["name", "email", "age", "role"])
        
        # Insert user into database
        result = self.mongodb.create_user(user_data)
        
        if result:
          
            
            return f"User created successfully: {json.dumps(user_data)}"
        else:
            return "Failed to create user"
    
    def get_users(self, input_data: GetUsersInput = None) -> str:
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
            return f"Found {len(users)} users: {json.dumps(users, indent=2)}"
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
        
        result = self.mongodb.update_user(email, update_data)
        
        if result:

            
            
            # Refresh RAG data
            self.retriever.refresh_data()
            return f"User {email} updated successfully with: {json.dumps(update_data)}"
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
        
        result = self.mongodb.delete_user(email)
        
        if result:
            return f"User {email} deleted successfully"
        else:
            return f"Failed to delete user {email}"