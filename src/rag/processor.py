import json
import os

class RAGProcessor:
    """Pricess the Context Query and Format it for the Agent for Apt response"""
    
    def __init__(self, config_path):
        """Initialize the processor
        
        Args:
            config_path (str): Path to the config file
        """
        self.config_path = config_path
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from config file
        
        Returns:
            dict: Configuration data
        """
        try:
            if os.path.exists(self.config_path) and os.path.getsize(self.config_path) > 0:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                print(f"Config file {self.config_path} is empty or doesn't exist")
                return {"collections": {"users": {"fields": []}}}
        except Exception as e:
            print(f"Error loading config: {e}")
            return {"collections": {"users": {"fields": []}}}
    
    def process_context(self, context, query_type):
        """Process context based on query type
        
        Args:
            context (list): List of context items
            query_type (str): Type of query (create, read, update, delete)
            
        Returns:
            dict: Processed context with relevant information
        """
        processed = {
            "available_fields": self.config.get("collections", {}).get("users", {}).get("fields", []),
            "relevant_data": context,
            "query_type": query_type
        }
        
        # Add specific context based on query type
        if query_type.lower() == "create":
            processed["required_fields"] = ["name", "email"]
            processed["optional_fields"] = [f for f in processed["available_fields"] if f not in ["name", "email"]]
            
        elif query_type.lower() == "update":
            processed["identifiers"] = ["email"]
            processed["updateable_fields"] = [f for f in processed["available_fields"] if f not in ["email"]]
            
        elif query_type.lower() == "delete":
            processed["identifiers"] = ["email"]
            
        # For read, no additional processing needed
            
        return processed
    
    def format_for_prompt(self, processed_context):
        """Format processed context for inclusion in agent prompt
        
        Args:
            processed_context (dict): Processed context
            
        Returns:
            str: Formatted context string for prompt
        """
        context_str = "--- DATABASE CONTEXT ---\n"
        
        # Add available fields
        fields = processed_context.get("available_fields", [])
        context_str += f"Available fields: {', '.join(fields)}\n"
        
        # Add query type specific information
        query_type = processed_context.get("query_type", "").lower()
        
        if query_type == "create":
            context_str += f"Required fields: {', '.join(processed_context.get('required_fields', []))}\n"
            context_str += f"Optional fields: {', '.join(processed_context.get('optional_fields', []))}\n"
            
        elif query_type == "update":
            context_str += f"Identifier fields: {', '.join(processed_context.get('identifiers', []))}\n"
            context_str += f"Updateable fields: {', '.join(processed_context.get('updateable_fields', []))}\n"
            
        elif query_type == "delete":
            context_str += f"Identifier fields: {', '.join(processed_context.get('identifiers', []))}\n"
        
        # Add sample data if available
        relevant_data = processed_context.get("relevant_data", [])
        if relevant_data:
            context_str += "\nSample data:\n"
            for i, item in enumerate(relevant_data[:2]):  # Limit to 2 samples
                context_str += f"Sample {i+1}: {json.dumps(item, indent=2)}\n"
        
        return context_str