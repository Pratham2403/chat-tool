import os
import json
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import time

class RAGRetriever:
    """Retriever Class that uses Elasticsearch for efficient text retrieval with built-in embedding generation"""
    
    def __init__(self, json_path, es_host="http://localhost:9200"):
        """Initialize the retriever with json path and Elasticsearch connection
        
        Args:
            json_path (str): The path to the JSON file.
            es_host (str): Elasticsearch host URL. Defaults to http://localhost:9200.
        """
        self.json_path = json_path
        try:
            # Fix Elasticsearch client to specify API version compatibility
            self.es_client = Elasticsearch(
                es_host, 
                request_timeout=30,
                headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=8"}
            )
            self.es_available = True
        except Exception as e:
            print(f"Error connecting to Elasticsearch: {e}")
            self.es_available = False
            
        self.index_name = "user_data"
        self.json_data = None
        self.load_data()
        
        # Only set up Elasticsearch if it's available
        if self.es_available:
            try:
                self.setup_elasticsearch()
            except Exception as e:
                print(f"Error setting up Elasticsearch: {e}")
                self.es_available = False
    
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
    
    def setup_elasticsearch(self):
        """Setup Elasticsearch index with basic settings"""
        try:
            # Check if index exists, delete if it does
            if self.es_client.indices.exists(index=self.index_name):
                self.es_client.indices.delete(index=self.index_name)
            
            # Define mapping for index - simplified
            mapping = {
                "mappings": {
                    "properties": {
                        "user_data": {
                            "type": "object"
                        },
                        "text": {
                            "type": "text"
                        }
                    }
                }
            }
            
            # Create the index with mappings
            self.es_client.indices.create(index=self.index_name, body=mapping)
            print(f"Created index: {self.index_name}")
            
            # Index the data
            if self.json_data:
                self._index_data()
                
        except Exception as e:
            print(f"Error setting up Elasticsearch: {e}")
            self.es_available = False
    
    def _index_data(self):
        """Index data into Elasticsearch with basic indexing"""
        try:
            actions = []
            
            for i, user in enumerate(self.json_data):
                user_str = json.dumps(user)
                
                # Create document for indexing - simplified
                doc = {
                    "_index": self.index_name,
                    "_id": f"user_{i}",
                    "_source": {
                        "user_data": user,
                        "text": user_str
                    }
                }
                
                actions.append(doc)
            
            # Bulk index documents
            if actions:
                success, failed = bulk(self.es_client, actions)
                print(f"Indexed {success} documents into Elasticsearch. Failed: {failed}")
                
        except Exception as e:
            print(f"Error indexing data: {e}")
            self.es_available = False
    
    def retrieve_context(self, query, n_results=2):
        """Retrieve context based on the query
        
        Args:
            query (str): The query to search for.
            n_results (int, optional): The number of results to return. Defaults to 2.
            
        Returns:
            list: List of retrieved documents.
        """
        # Always refresh data from file to ensure we have the latest
        self.load_data()
        
        # If no Elasticsearch or no data, return first n results from file
        if not self.es_available or not self.json_data:
            return self.json_data[:min(n_results, len(self.json_data))]
        
        try:
            # Use simple match query for text search
            search_body = {
                "size": n_results,
                "query": {
                    "match": {
                        "text": query
                    }
                }
            }
            
            # Execute search
            response = self.es_client.search(index=self.index_name, body=search_body)
            
            # Extract and return results
            relevant_docs = []
            for hit in response["hits"]["hits"]:
                user_data = hit["_source"]["user_data"]
                relevant_docs.append(user_data)
                
            return relevant_docs if relevant_docs else self.json_data[:min(n_results, len(self.json_data))]
            
        except Exception as e:
            print(f"Error retrieving context: {e}")
            # Fallback to returning the first n items from json_data
            return self.json_data[:min(n_results, len(self.json_data))]
    
    def refresh_data(self):
        """Refresh data by reloading JSON and reindexing"""
        self.load_data()
        
        if self.es_available:
            try:
                # Wait a bit to allow any database operations to complete
                time.sleep(0.5)
                self.setup_elasticsearch()
            except Exception as e:
                print(f"Error refreshing Elasticsearch data: {e}")
                # Continue without Elasticsearch
                self.es_available = False