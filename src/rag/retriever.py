#Implementing the Vecor Seach Functinoaloity, 
# This is where the Expected Semantic Seaarch will take place
# This is also the Root Loaction where the ElasticSearch will be implemented in the Future Iterations

import os
import json
import chromadb
from sentence_transformers import SentenceTransformer

class RAGRetriever:
    """Retriever Class that for now loads the JSON Data and uses the SentenceTransformer to get the embeddings and improve the context of our LLM"""
    
    def __init__(self, json_path):
        """Intitialize the retriever witj the json path
        
        Args:
            json_path (str): The path to the JSON file.
        
        """
        self.json_path = json_path
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.Client()
        self.collection = None
        self.json_data = None
        self.load_data()
        self.setup_vector_db()
    
    
    #Loads the Data from the JSON File
    def load_data(self):
        """Load Data from the JSON file."""
        try:
            if os.path.exists(self.json_path) and os.path.getsize(self.json_path) > 0:
                with open(self.json_path, 'r') as f:
                    data = json.load(f)
                # Remove any MongoDB _id fields from entries
                self.json_data = [
                    {k: v for k, v in item.items() if k != '_id'}
                    if isinstance(item, dict) else item
                    for item in data
                ]
            else:
                print(f"File {self.json_path} does not exist or is empty.")
                self.json_data = []
        except Exception as e:
            print(f"Error loading JSON file {self.json_path}: {e}")
            self.json_data = []
                
    
    
    #Setup the Vector Database  and store the Vecor Embeddings in the ChromaDb 
    def setup_vector_db(self):
        """Setup the Vector Database and store the Vector Embeddings in the ChromaDb
        
        """
        try:
            
            # Create or Get a Collection
            self.collection = self.chroma_client.get_or_create_collection("user_data")
            
            # Create Embeddings for the JSON Data (if available)
            if self.json_data :
                
                # Create Embeddings
                documents = []
                ids = []
                
                for i, user in enumerate(self.json_data):
                    user_str = json.dumps(user)
                    documents.append(user_str)
                    ids.append(f"user_{i}")
                    
                    
                # Create the Embedding and Store it in the ChromaDB
                
                if documents : 
                    embeddings = self.model.encode(documents, show_progress_bar=True).tolist()
                    
                    # Add the Embeddings to the Collection
                    self.collection.add(
                        documents=documents,
                        embeddings=embeddings,
                        # Could have been uselful is User Knows the ID and then passes the Query or, the LLM responses with a specific ID
                        # metadatas=[{"id": id} for id in ids],
                        ids=ids
                    )
                    
                    print(f"Added {len(documents)} documents to the vector database.")

        except Exception as e:
            print(f"Error setting up vector database: {e}")
            return





    # Generate the Entire Retrieval Context and Workflow
    def retrieve_context(self, query, n_results=2):
        """Retrieve Context from the Vector Database
        
        Args:
            query (str): The query to search for.
            n_results (int, optional): The number of results to return. Defaults to 2.
            
        Returns:
            list : List of retrieved documents.
        """
        try:
            # Get the Embedding for the Query
            query_embedding = self.model.encode(query).tolist()
            
            # Perform the Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
            )
            
            # ChromaDB returns documents as list of lists; flatten first batch
            docs_batch = []
            if results and 'documents' in results and results['documents']:
                first_batch = results['documents'][0] if isinstance(results['documents'][0], list) else results['documents']
                docs_batch = first_batch
            # Parse each document
            # Flatten nested lists and parse documents
            relevant_docs = []
            for doc in docs_batch:
                if isinstance(doc, list):
                    # Nested list: process each element
                    for subdoc in doc:
                        if isinstance(subdoc, str):
                            try:
                                relevant_docs.append(json.loads(subdoc))
                            except json.JSONDecodeError:
                                relevant_docs.append(subdoc)
                        else:
                            relevant_docs.append(subdoc)
                elif isinstance(doc, str):
                    try:
                        relevant_docs.append(json.loads(doc))
                    except json.JSONDecodeError:
                        relevant_docs.append(doc)
                else:
                    relevant_docs.append(doc)

            return relevant_docs

        except Exception as e:
            print(f"Error retrieving context: {e}")
            return []



    #Refresh the Vector Database to Redefine the Context if needed (Only useful if the JSON Data Keeps on Changing) This is done because we are not creating an MCP Server that can interact with the MongoDB Database:
    def refresh_data(self):
        """Refresh the Data by removing the old data and reloading the new data."""
        
        if self.collection:
            self.collection.delete()
        
        self.load_data()
        self.setup_vector_db()





