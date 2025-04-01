# LLM service for prompt generation and execution
# LLM has practices: Chat, ListModels, CurrentModelList
# LLM is an APIService and abstract class

from .APIService import APIService
from prompits.Practice import Practice
class LLM(APIService):
    def __init__(self, name: str, description: str = None, default_model: str = "gpt-4o-mini"):
        super().__init__(name, description) 
        self.AddPractice(Practice("Chat", self.Chat))
        self.AddPractice(Practice("ListModels", self.ListModels))
        self.AddPractice(Practice("CurrentModelList", self.CurrentModelList))
        self.default_model = default_model

    def Chat(self, prompt: str, model: str = "gpt-4o-mini"):
        """
        Chat with the LLM.
        
        Returns:
            str: The response from the LLM
        """
        raise NotImplementedError("Chat is not implemented")

    def ListModels(self):
        """
        List all models available.
        """
        raise NotImplementedError("ListModels is not implemented")
    
    def CurrentModelList(self):
        """
        List all models currently available.
        """
        raise NotImplementedError("CurrentModelList is not implemented")

    def ToJson(self):
        """
        Convert the LLM service to a JSON object.
        
        Returns:
            dict: JSON representation of the LLM service
        """
        # Get base JSON data from parent which includes practices
        json_data = super().ToJson()
        self.log(f"LLM ToJson start: {json_data}","DEBUG")
        # Add LLM-specific fields
        json_data.update({
            "default_model": self.default_model,
            "type": "LLM"
        })
        self.log(f"LLM ToJson end: {json_data}","DEBUG")
        
        return json_data
