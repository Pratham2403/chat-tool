# AI Agent Workflow with RAG and MongoDB Integration

A conversational AI agent built with LangGraph and Gemini 2.0 Flash that uses Retrieval-Augmented Generation (RAG) to process JSON data and perform CRUD operations on a MongoDB Atlas database.

## Features

- Agent workflow that iteratively processes user requests
- RAG implementation for enhanced context understanding
- MongoDB Atlas integration for database operations
- Support for CRUD operations (Create, Read, Update, Delete)
- Tool selection based on user intent

## Architecture

The system implements a loop-based agent workflow that:
1. Processes user input
2. Determines required actions/tools
3. Retrieves relevant context from JSON data
4. Performs database operations as needed
5. Responds with appropriate information or asks for clarification

## Prerequisites

- Python 3.8+
- MongoDB Atlas account
- Gemini 2.0 Flash API key

## Installation

```bash
# Clone the repository
git clone https://github.com/pratham2403/rag-llm-web.git
cd rag-llm-web

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the project root with:

```
GEMINI_API_KEY=your_gemini_api_key
MONGODB_URI=your_mongodb_connection_string
```

2. Configure your MongoDB collections in `config.json`

## Usage

```bash
# Start the application
python app.py
```


## Components

- **Agent Workflow**: LangGraph-based implementation that manages the conversation flow and decision-making process
- **RAG Module**: Retrieves and processes relevant information from JSON files
- **Tool Integration**: Custom tools for database operations
- **MongoDB Connector**: Handles database connections and operations

## Example Interactions

```
User: "Create a new user with name John Doe and email john@example.com"
Agent: "I'll create a new user. Do you want to specify any additional fields like 'age' or 'role'?"
User: "Yes, add age 30 and role developer"
Agent: "Creating user with name: John Doe, email: john@example.com, age: 30, role: developer... User created successfully!"
```

```
User: "Get all users"
Agent: "Retrieving all users from database... Found 5 users. Here they are: [user list]"
```

## License

MIT