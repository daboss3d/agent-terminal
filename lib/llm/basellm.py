from abc import ABC, abstractmethod
from typing import Generator, Union, Dict # Added Generator, Union, Dict

class BaseApiLLM(ABC):

    def __init__(self, base_url : str, model_name: str):
        self.model_name = model_name
        self.base_url = base_url
        # params dictionary
        self.params = {
            "system_prompt": "respond to the question the best you can"
        }
        print(f"Initializing API LLM: {self.model_name} to {self.base_url}")

    # @abstractmethod
    def set_model(self, model_path: str) -> None:
        """se the Model id."""
        pass

    def print_model(self):
        """Prints the current model name"""
        print("Current Model ->",self.model_name)

    @abstractmethod
    def generate_text(self, prompt: str, stream: bool = False, max_tokens: int = 50) -> Generator[Union[str, Dict], None, None]:
        """
        Generates text based on the provided prompt.
        Yields string chunks of the generated text when streaming.
        Finally, yields a dictionary containing token counts and other metadata.

        Yields:
            Union[str, Dict]: String chunks of text, or a final Dict with metadata.
                              The dict will have an "is_final_metadata": True key.
                              Example final dict: {
                                  "text": "", # Can be empty if all text was yielded
                                  "prompt_tokens": int,
                                  "completion_tokens": int,
                                  "total_tokens": int,
                                  "is_final_metadata": True
                              }
        """
        raise NotImplementedError

    # @abstractmethod
    def set_params(self, new_params: dict) -> None:
        """Sets parameters for the LLM like top_p probability and temperature."""
        
        # only set parameters if the key already exist
        for k, v in new_params.items():
            if k in self.params:
                self.params[k] = v
                # print(f"[BaseApiLLM] Updating the key '{k}' to '{v}' in params.")
            else :
                print(f"[BaseApiLLM] ERROR Updating the key '{k}' to '{v}' in params, the key '{k}' not exist")
