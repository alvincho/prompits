# Ollama is an LLM service that uses Ollama to complete prompts
# Ollama has endpoints: /generate, /chat, /embeddings
# has base url: http://localhost:11434 and can be initialized with a base url

from typing import Dict, List, Any
import requests
import json
from .LLM import LLM
from .APIService import Endpoint
import traceback
from prompits.Practice import Practice

class Ollama(LLM):
    """
    Ollama is an LLM service that uses Ollama to complete prompts
    Ollama has endpoints: /generate, /chat, /embeddings
    has base url: http://localhost:11434 and can be initialized with a base url

    !!! This class will be deprecated by APIService class !!!
    """
    def __init__(self, name: str, description: str = None, 
                 default_model: str = None, base_url: str = "http://localhost:11434"):
        # if default_model is not provided, get the first model from the list of models
        self.base_url = base_url    
        if default_model is None:
            models = self.ListModels()
            if "models" in models:
                default_model = models["models"][0]["name"]  
        super().__init__(name, description, default_model)
        self.base_url = base_url
        self.AddPractice(Practice("Chat", self.Chat))
        self.AddPractice(Practice("Embeddings", self.Embeddings))
        self.AddPractice(Practice("ListModels", self.ListModels))

    def Chat(self, prompt: str, model: str = None, full_response: bool = False):
        """
        Chat with the LLM.
        
        Args:
            prompt (str): The prompt to send
            model (str, optional): The model to use. Defaults to the default model.
            
        Returns:
            Dict: The chat response
        """ 
        if model is None:
            model = self.default_model
            
        # Try the chat endpoint first, fall back to generate if it fails
        try:
            # First try the /api/chat endpoint (newer Ollama versions)
            url = f"{self.base_url}/api/chat"
            headers = {"Content-Type": "application/json"}
            data = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            self.log(f"Ollama:Sending chat request to {url} with data: {data}")
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            # The response is a stream of JSON objects, one per line
            # We need to collect the full response
            full_content = ""
            last_response = None
            
            # Parse the response line by line
            for line in response.text.strip().split('\n'):
                if line:
                    try:
                        chunk = json.loads(line)
                        last_response = chunk
                        if "message" in chunk and "content" in chunk["message"]:
                            full_content += chunk["message"]["content"]
                    except json.JSONDecodeError:
                        pass
            
            # Use the last response as our result and add the complete text
            if last_response:
                last_response["complete_text"] = full_content
                if full_response:
                    return last_response
                else:
                    return {"result": {"complete_text": full_content}}
            else:
                return {"error": "Failed to parse streaming response", "complete_text": ""}
            
        except requests.exceptions.RequestException as e:
            # If chat endpoint fails, try the /api/generate endpoint (older Ollama versions)
            try:
                url = f"{self.base_url}/api/generate"
                headers = {"Content-Type": "application/json"}
                data = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
                
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                
                # For non-streaming, we get a single JSON response
                result = response.json()
                
                # Add the complete text to the response using the 'response' field
                if "response" in result:
                    result["complete_text"] = result["response"]
                if full_response:
                    return {"result": result}
                else:
                    return {"result": {"complete_text": result["complete_text"]}}
                
            except Exception as inner_e:
                self.log(f"Both endpoints failed. Chat error: {str(e)}, Generate error: {str(inner_e)}")
                traceback.print_exc()
                return {"error": f"Both endpoints failed. Chat error: {str(e)}, Generate error: {str(inner_e)}"}
        except Exception as e:
            self.log(f"Error generating chat response: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}
    
    def Embeddings(self, prompt: str, model: str = None):
        """
        Embed a prompt using the LLM.
        
        Args:
            prompt (str): The prompt to embed
            model (str, optional): The model to use. Defaults to the default model.
            
        Returns:
            Dict: The embedding response
        """
        if model is None:
            model = self.default_model
            
        # Use direct requests instead of the Request method
        url = f"{self.base_url}/api/embeddings"
        headers = {"Content-Type": "application/json"}
        data = {"model": model, "prompt": prompt}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.log(f"Error generating embedding: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}

    def ListModels(self):
        """
        List all models available.
        
        Returns:
            Dict: The models response
        """
        # Use direct requests instead of the Request method
        url = f"{self.base_url}/api/tags"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.log(f"Error listing models: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}
    
    def CurrentModelList(self):
        """
        List all models currently available.
        
        Returns:
            List[str]: List of model names
        """
        response = self.ListModels()
        if "models" in response:
            return [model["name"] for model in response["models"]]
        return []

    def ToJson(self):
        """
        Convert the Ollama service to a JSON object.
        
        Returns:
            dict: JSON representation of the Ollama service
        """
        # Get base JSON data from parent which includes practices
        json_data = super().ToJson()
        self.log(f"Ollama ToJson start: {json_data}","DEBUG")
        # Ensure practices are explicitly included, even if parent chain didn't include them
        if "practices" not in json_data and hasattr(self, "practices"):
            json_data["practices"] = {}
            for name, practice in self.practices.items():
                json_data["practices"][name] = practice.ToJson()
        
        # Add Ollama-specific fields
        json_data.update({
            "type": "Ollama",
            "base_url": self.base_url
        })
        self.log(f"Ollama ToJson end: {json_data}","DEBUG")
        return json_data
