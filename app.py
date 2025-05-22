import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.db.mongodb import MongoDB
from src.agent.workflow import AgentWorkflow
from src.cli.terminal import TerminalInterface

def main():
    """Main application entry point"""
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY not found in .env file")
        print("Please add your Gemini API key to .env file")
        return
    
    # Check for MongoDB URI
    if not os.getenv("MONGODB_URI"):
        print("Error: MONGODB_URI not found in .env file")
        print("Please add your MongoDB connection string to .env file")
        return
    
    # Initialize MongoDB connection
    mongodb = MongoDB()
    connection_result = mongodb.connect()
    
    if not connection_result:
        print("Failed to connect to MongoDB. Please check your connection string.")
        return
    
    # Get file paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "data", "user.json")
    config_path = os.path.join(current_dir, "config.json")
    
    # Initialize agent workflow
    agent = AgentWorkflow(mongodb, json_path, config_path)
    
    # Initialize terminal interface
    terminal = TerminalInterface(agent)
    
    try:
        # Start chat interface
        terminal.start_chat()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Close MongoDB connection
        mongodb.close()

if __name__ == "__main__":
    main()