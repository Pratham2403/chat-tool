import os
from typing import Dict, List, Any, Tuple, Optional
from dotenv import load_dotenv
import json
from langgraph.graph import StateGraph, END, START
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel

from src.agent.tools import DatabaseTools, CreateUserInput, UpdateUserInput, DeleteUserInput, GetUsersInput
from src.rag.retriever import RAGRetriever
from src.rag.processor import RAGProcessor

# Load environment variables
load_dotenv()

class StateSchema(BaseModel):
    query: str
    context: Dict[str, Any]
    response: str
    complete: bool

    class Config:
        # Allow arbitrary types for context
        arbitrary_types_allowed = True

class AgentWorkflow:
    """Agent workflow for processing user queries and interacting with the database"""
    
    def __init__(self, mongodb_client, json_path, config_path):
        """Initialize the agent workflow
        
        Args:
            mongodb_client: MongoDB client instance
            json_path (str): Path to the JSON data
            config_path (str): Path to the configuration file
        """
        self.mongodb = mongodb_client
        self.json_path = json_path
        self.config_path = config_path
        
        # Initialize RAG components
        self.retriever = RAGRetriever(json_path)
        self.processor = RAGProcessor(config_path)
        
        # Initialize database tools
        self.db_tools = DatabaseTools(mongodb_client)
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.1
            # Removed deprecated parameter: convert_system_message_to_human
        )
        
        # Create workflow
        self.workflow = self._create_workflow()
    
    def _create_workflow(self):
        """Create the agent workflow
        
        Returns:
            Compiled workflow that can be invoked
        """
        # Define workflow states using a schema
        workflow = StateGraph(StateSchema)
        
        # Add nodes
        workflow.add_node("query_classifier", self._classify_query)
        workflow.add_node("tool_selector", self._select_tool)
        workflow.add_node("response_generator", self._generate_response)
        
        # Define edges
        workflow.add_edge(START, "query_classifier")
        workflow.add_edge("query_classifier", "tool_selector")
        workflow.add_edge("tool_selector", "response_generator")
        workflow.add_edge("response_generator", END)
        
        # Define conditional edges
        workflow.add_conditional_edges(
            "response_generator",
            self._check_completion,
            {
                True: END,
                False: "query_classifier"
            }
        )
        
        # Compile the graph to get an executable workflow with invoke()
        return workflow.compile()
    
    def _classify_query(self, state: StateSchema) -> Dict[str, Any]:
        """Classify the user query
        
        Args:
            state: Current state
            
        Returns:
            Dict: Updated state
        """
        query = state.query
        
        # Retrieve context from RAG
        context_items = self.retriever.retrieve_context(query)
        
        # Prepare system prompt
        system_prompt = """
        You are a query classifier for a database system. Your task is to determine the type of database operation
        the user wants to perform. Classify the query into one of these categories:
        
        1. CREATE - Creating a new user record
        2. READ - Reading/retrieving user records
        3. UPDATE - Updating an existing user record
        4. DELETE - Deleting a user record
        
        Provide your classification along with confidence (HIGH, MEDIUM, LOW) and explanation.
        """
        
        # Add context to prompt
        if context_items:
            system_prompt += "\n\nHere's some context about the database:\n"
            system_prompt += json.dumps(context_items, indent=2)
        
        # Get classification from LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]
        
        response = self.llm.invoke(messages)
        
        # Extract classification
        classification_text = response.content
        
        # Simple parsing of classification
        query_type = ""
        if "CREATE" in classification_text.upper():
            query_type = "create"
        elif "READ" in classification_text.upper():
            query_type = "read"
        elif "UPDATE" in classification_text.upper():
            query_type = "update"
        elif "DELETE" in classification_text.upper():
            query_type = "delete"
        else:
            # Default to read if unclear
            query_type = "read"
            
        # Process context
        processed_context = self.processor.process_context(context_items, query_type)
        formatted_context = self.processor.format_for_prompt(processed_context)
        
        # Update context on the state
        state.context = {
            "query_type": query_type,
            "classification": classification_text,
            "formatted_context": formatted_context,
            "raw_context": context_items
        }
        # Return updated state dict for graph
        return state.dict()
    
    def _select_tool(self, state: StateSchema) -> Dict[str, Any]:
        """Select and execute the appropriate tool
        
        Args:
            state: Current state
            
        Returns:
            Dict: Updated state
        """
        query = state.query
        context = state.context
        query_type = context["query_type"]
        formatted_context = context["formatted_context"]
        
        # Check if tool has already been executed for this query
        if "tool_result" in context and context["tool_result"]:
            # Tool already executed, just return the current state
            return state.dict()
        
        # Prepare system prompt
        system_prompt = f"""
        You are a tool selection agent for a database system. Based on the user query and the classified query type,
        extract the necessary parameters to execute the appropriate database tool.
        
        Query type: {query_type}
        
        {formatted_context}
        
        For CREATE operations, extract: name, email, age (optional), role (optional)
        For READ operations, extract any filter conditions (or return empty for all users)
        For UPDATE operations, extract: email (identifier) and the fields to update
        For DELETE operations, extract: email (identifier)
        
        Return ONLY the extracted parameters in JSON format.
        """
        
        # Get parameters from LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]
        
        response = self.llm.invoke(messages)
        
        # Try to parse JSON response
        try:
            # Extract JSON from the response
            response_text = response.content
            
            # Find JSON in the response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                parameters = json.loads(json_str)
            else:
                parameters = {}
                
            # Execute appropriate tool based on query type
            result = ""
            
            # Check if the same tool has already been executed for this query by looking at past results
            tool_already_executed = False
            if 'tool_result' in state.context:
                # Don't execute the same tool multiple times
                tool_already_executed = True
                result = state.context["tool_result"]
                
            if not tool_already_executed:
                if query_type == "create":
                    # Prepare input for create tool
                    create_input = CreateUserInput(
                        name=parameters.get("name", ""),
                        email=parameters.get("email", ""),
                        age=parameters.get("age"),
                        role=parameters.get("role")
                    )
                    result = self.db_tools.create_user(create_input)
                    
                elif query_type == "read":
                    # Prepare input for get tool
                    filters = parameters.get("filters", {})
                    get_input = GetUsersInput(filters=filters)
                    result = self.db_tools.get_users(get_input)
                    
                elif query_type == "update":
                    # Prepare input for update tool
                    email = parameters.get("email", "")
                    # Remove email from update data
                    update_data = {k: v for k, v in parameters.items() if k != "email"}
                    update_input = UpdateUserInput(email=email, data=update_data)
                    result = self.db_tools.update_user(update_input)
                    
                elif query_type == "delete":
                    # Prepare input for delete tool
                    email = parameters.get("email", "")
                    delete_input = DeleteUserInput(email=email)
                    result = self.db_tools.delete_user(delete_input)
            
            # Update state context with tool execution results
            state.context["tool_result"] = result if 'result' in locals() else None
            state.context["parameters"] = parameters if 'parameters' in locals() else {}
            # Return updated state dict
            return state.dict()
        
        except Exception as e:
            # Handle parsing errors
            state.context["tool_result"] = f"Error executing tool: {str(e)}"
            state.context["parameters"] = {}
            # Return updated state dict
            return state.dict()
    
    def _generate_response(self, state: StateSchema) -> Dict[str, Any]:
        """Generate a response to the user
        
        Args:
            state: Current state
            
        Returns:
            Dict: Updated state
        """
        query = state.query
        context = state.context
        query_type = context.get("query_type", "")
        tool_result = context.get("tool_result", "")
        parameters = context.get("parameters", {})
        
        # Prepare system prompt
        system_prompt = f"""
        You are an AI assistant for a database system. Provide a natural, conversational response to the user based on:
        
        1. Their original query: "{query}"
        2. The operation performed: {query_type}
        3. The result: {tool_result}
        
        If the operation was successful, summarize what was done.
        If the operation failed or was incomplete, explain what's missing and ask follow-up questions.
        
        Be concise and helpful. Do not invent data that isn't in the result.
        """
        
        # Get response from LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]
        
        response = self.llm.invoke(messages)
        
        # Check if the operation was successful based on tool_result
        operation_successful = "successfully" in tool_result.lower() if tool_result else False
        
        # Check if we need more information or if the operation failed
        complete = True
        
        # If required parameters are missing, mark as incomplete
        if query_type == "create" and (not parameters.get("name") or not parameters.get("email")):
            complete = False
        elif query_type == "update" and (not parameters.get("email") or len(parameters) <= 1):
            complete = False
        elif query_type == "delete" and not parameters.get("email"):
            complete = False
            
        # If the operation was attempted but failed, mark as complete to avoid retries
        if tool_result and not operation_successful:
            # Operation was attempted but failed - no need to retry
            complete = True
            
        # Update state with response and completion flag
        state.response = response.content
        state.complete = complete
        # Return updated state dict
        return state.dict()
    
    def _check_completion(self, state: StateSchema) -> bool:
        """Check if the interaction is complete
        
        Args:
            state: Current state
            
        Returns:
            bool: True if complete, False otherwise
        """
        return state.complete
    
    def process_query(self, query: str) -> str:
        """Process a user query through the workflow
        
        Args:
            query (str): User query
            
        Returns:
            str: Response to the user
        """
        try:
            # Initialize state
            state = {"query": query, "context": {}, "response": "", "complete": False}
            
            # Run workflow
            result = self.workflow.invoke(state)
            # Return the 'response' from the result mapping
            return result["response"]
        except Exception as e:
            # Handle any unexpected errors
            print(f"Error processing query: {e}")
            return f"I'm sorry, I encountered an error while processing your request. Please try again with a more specific query."