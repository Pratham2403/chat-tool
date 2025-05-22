import sys
import os

class TerminalInterface:
    """Terminal interface for interacting with the agent"""
    
    def __init__(self, agent_workflow):
        """Initialize the terminal interface
        
        Args:
            agent_workflow: Agent workflow instance
        """
        self.agent = agent_workflow
        
    def display_welcome(self):
        """Display welcome message"""
        print("\n" + "=" * 50)
        print("Welcome to RAG-LLM-Web Terminal Interface")
        print("Type 'q' to exit the chat")
        print("=" * 50 + "\n")
        
    def start_chat(self):
        """Start the chat interface"""
        self.display_welcome()
        
        while True:
            # Get user input
            user_input = input("\nYou: ")
            
            # Check for exit command
            if user_input.lower() == "q":
                print("\nGoodbye!")
                break
                
            # Process query through agent
            try:
                print("\nProcessing...")
                response = self.agent.process_query(user_input)
                
                # Display response
                print("\nAgent:", response)
                
            except Exception as e:
                print(f"\nError: {str(e)}")
                
    def format_json_output(self, json_data):
        """Format JSON data for terminal display
        
        Args:
            json_data: JSON data to format
            
        Returns:
            str: Formatted string
        """
        import json
        
        try:
            if isinstance(json_data, str):
                # Try to parse JSON string
                data = json.loads(json_data)
            else:
                data = json_data
                
            # Pretty print with indentation
            return json.dumps(data, indent=2)
            
        except Exception:
            # If not valid JSON, return as is
            return str(json_data)