import os
import json
from typing import Dict, Any, Optional


def load_json_file(file_path: str) -> Any:
    """
    Load Data from JSON File.
    
    Args:
        file_path (str): The path to the JSON file.
        
    Returns:
        Any: Loaded data from the JSON file, or None if the file does not exist.
    """
    try:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'r') as f:
                return json.load(f)
        else :
            print(f"File {file_path} does not exist or is empty.")
            return None
    except Exception as e:
        print(f"Error loading JSON file {file_path}: {e}")
        return None
    
    
    
    
def save_json_file(file_path: str, data: Any) -> bool:
    """
    Save Data to JSON File.
    
    Args:
        file_path (str): The path to the JSON file.
        data (Any): The data to save.
        
    Returns:
        bool: True if the data was saved successfully, False otherwise.
    """
    try:
        with open(file_path, 'w') as f:
            # Use default=str to serialize non-serializable types (e.g., ObjectId) as strings
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        print(f"Error saving JSON file {file_path}: {e}")
        return False
    
    
    
    
def validate_email(email: str) -> bool:
    """
    Validate Email Address.
    
    Args:
        email (str): The email address to validate.
        
    Returns:
        bool: True if the email is valid, False otherwise.
    """
    import re
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email) )




def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from Text.
    
    Args:
        text (str): The text containing JSON data.
        
    Returns:
        Optional[Dict[str, Any]]: The extracted JSON data, or None if no valid JSON was found.
    """
    import re
    try:
        match = re.search(r'\{(?:[^{}]|(?R))*\}', text)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            # No JSON object found in the text
            return None
    except Exception as e:
        print(f"Error extracting JSON from text: {e}")
        return None


def safe_json_dumps(obj: Any) -> str:
    """
    Safely convert an object to a JSON string.
    
    Args:
        obj (Any): The object to convert.
        
    Returns:
        str: The JSON string.
    """
    try:
        return json.dumps(obj, default=str)
    except Exception as e:
        print(f"Error converting to JSON: {e}")
        # Create a safe version
        if isinstance(obj, dict):
            safe_obj = {}
            for k, v in obj.items():
                safe_obj[str(k)] = str(v)
            return json.dumps(safe_obj)
        elif isinstance(obj, list):
            return json.dumps([str(i) for i in obj])
        else:
            return json.dumps(str(obj))
