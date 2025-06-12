from abc import ABC, abstractmethod

class BaseApiLLM(ABC):

    def __init__(self, base_url : str, model_name: str):
        self.model_name = model_name
        self.base_url = base_url
        print(f"Initializing API LLM: {self.model_name} to  {self.base_url}")

    # @abstractmethod
    def set_model(self, model_path: str) -> None:
        """se the Model id."""
        pass

    def print_model(self):
        """Prints the current model name"""
        print("Current Model ->",self.model_name)

    @abstractmethod
    def generate_text(self, prompt: str, max_tokens: int = 50) -> str:
        """Generates text based on the provided prompt."""
        pass

    @abstractmethod
    def set_params(self, new_params: dict) -> None:
        """Sets parameters for the LLM like top_p probability and temperature."""
        pass