
import json
import requests
from typing import Generator, Union, Dict # Added

from lib.llm.basellm import BaseApiLLM
# from lib.utils.text import clear_markdown_to_color # Removed as it's no longer in utils and functionality is not immediately required
from lib.llm.prompts import explain_terminal

config = {
    "ollama_url":"http://10.1.1.62:11434/api/generate",
    "model": "devstral:latest"
}
OLLAMA_URL = config["ollama_url"]
MODEL_NAME = config["model"]

def create_payload_query(prompt):
    ollama_prompt_explanation = """
        Explain what the shell command and its parameters do. Be concise. Don't use markdown to reply
    """

    return {
        "model": MODEL_NAME,
        "prompt": f"{explain_terminal}\n\n{prompt}",
        "system": "You are a Fresh assistant, Respond in French"
    }


def hello():
    print("hello from ollama 3")
    hello_text()


def query_ollama_stream(base_url : str, prompt):
    """
    Ask Olama for a response to a prompt
    """

    payload = create_payload_query(prompt)

    with requests.post(OLLAMA_URL, json=payload, stream=True) as response:

        response.raise_for_status()

        # Variable to hold concatenated response strings if no callback is provided
        full_response = ""

        # Iterating over the response line by line and displaying the details
        for line in response.iter_lines():
            if line:
                # Parsing each line (JSON chunk) and extracting the details
                chunk = json.loads(line)

                # If this is not the last chunk, add the "response" field value to full_response and print it
                if not chunk.get("done"):
                    response_piece = chunk.get("response", "")
                    full_response += response_piece
                    print(response_piece, end="", flush=True)

        if response == "":
            print("Error parsing response")
            exit(-1)


def query_ollama(base_url : str, prompt):

    payload = create_payload_query(prompt)

    response_text = ""

    try:
        with requests.post(base_url, json=payload, stream=True) as response:
            response.raise_for_status()
 
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    # Check if the chunk has a done flag
                    if not chunk.get("done"):
                        response_piece = chunk.get("response", "")
                        response_text += response_piece
                        # print(response_piece, end="", flush=True)

            print()  # To ensure new line after printing the command

    except requests.RequestException as e:
        print(f"Error fetching data from Ollama: {str(e)}")
    finally:
        if response_text.strip() == "":
            return "No response received."

        # spinner.stop()
        return clear_markdown_to_color(response_text)            





def query_stream(model_name: str, base_url : str, prompt):

    payload =   {
        "model": model_name,
        "prompt": f"{prompt}",
        "system": "You are a assistant, Respond the best you can"
    }

    with requests.post(base_url, json=payload, stream=True) as response:

        response.raise_for_status()

        # Variable to hold concatenated response strings if no callback is provided
        full_response = ""

        # Iterating over the response line by line and displaying the details
        for line in response.iter_lines():
            if line:
                # Parsing each line (JSON chunk) and extracting the details
                chunk = json.loads(line)

                # If this is not the last chunk, add the "response" field value to full_response and print it
                if not chunk.get("done"):
                    response_piece = chunk.get("response", "")
                    full_response += response_piece
                    print(response_piece, end="", flush=True)

        if response == "":
            print("Error parsing response")
            exit(-1)



# Final methods ######################################################################################

def generate_text(base_url : str, payload:dict, stream: bool = True ) -> Generator[Union[str, Dict], None, None]:
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0

    if stream:
        full_response = ""
        final_chunk_data = {}
        try:
            with requests.post(base_url, json=payload, stream=True) as response:
                response.raise_for_status()
                # print() # Start stream on new line - remove for generator
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        if not chunk.get("done"):
                            response_piece = chunk.get("response", "")
                            # full_response += response_piece # No need to accumulate full_response here for stream
                            yield response_piece # Yield the text chunk
                            # print(response_piece, end="", flush=True) # remove for generator
                        else:
                            # This is the final chunk with metadata
                            final_chunk_data = chunk
                            # print() # Newline after stream completion - remove for generator

                if final_chunk_data:
                    prompt_tokens = final_chunk_data.get("prompt_eval_count", 0)
                    completion_tokens = final_chunk_data.get("eval_count", 0)
                    total_tokens = prompt_tokens + completion_tokens

        except requests.RequestException as e:
            print(f"Error fetching data from Ollama (stream): {str(e)}")
            # In a generator, we might yield an error object or just stop.
            # For now, if an error occurs, the generator will stop, and no final dict is yielded.
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from Ollama (stream): {str(e)}")

        # Yield the final metadata dictionary for stream
        yield {
            "text": "", # Placeholder, full text was yielded in chunks
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "is_final_metadata": True
        }
    else: # Non-streaming
        response_text = ""
        final_chunk_data = {}
        prompt_tokens = 0 # Ensure these are initialized for non-streaming case too
        completion_tokens = 0
        total_tokens = 0
        try:
            with requests.post(base_url, json=payload, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        if not chunk.get("done"):
                            response_text += chunk.get("response", "")
                        else:
                            final_chunk_data = chunk

                if final_chunk_data:
                    prompt_tokens = final_chunk_data.get("prompt_eval_count", 0)
                    completion_tokens = final_chunk_data.get("eval_count", 0)
                    total_tokens = prompt_tokens + completion_tokens
                else:
                    print("Warning: Final 'done' chunk not processed in non-streaming mode for Ollama.")
        except requests.RequestException as e:
            print(f"Error fetching data from Ollama (non-stream): {str(e)}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from Ollama (non-stream): {str(e)}")

        yield response_text if response_text else "" # Yield accumulated text
        yield { # Yield final metadata
            "text": response_text, # Full text for non-streamed case
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "is_final_metadata": True
        }

def list_models(base_url):
    """
    List models available from the Ollama API.

    Args:
        base_url (str): The base URL of the Ollama API, e.g., "http://localhost:11434"

    Returns:
        list[str]: A list of model names, or an error message if the request fails.
    """
    try:
        response = requests.get(f"{base_url}/api/tags")
        response.raise_for_status()
        data = response.json()
        models = [model["name"] for model in data.get("models", [])]
        return models
    except requests.exceptions.RequestException as e:
        print(f"Error querying Ollama API: {e}")
        return []



# Example usage (you would need to create a concrete subclass of this)
class OllamaApi(BaseApiLLM):
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434"):
        super().__init__(base_url, model_name)
        # Ensure the base_url for generate_text is just the host, not the /api/generate path yet
        # The generate_text helper function appends /api/generate
        if self.base_url.endswith("/api/generate"):
             # print(f"Warning: base_url for OllamaApi includes /api/generate, stripping for broader compatibility.")
             self.base_url = self.base_url.replace("/api/generate", "")


    def generate_text(self, prompt: str, stream: bool = False,  max_tokens: int = 50) -> Generator[Union[str, Dict], None, None]:

        payload = {
            "model": self.model_name,
            "prompt": f"{prompt}",
            "system": self.params["system_prompt"]
        }

        # Use yield from to delegate to the generator helper function
        yield from generate_text(f"{self.base_url}/api/generate", payload, stream)

    def set_params(self, new_params: dict) -> None:
        # for k, v in new_params.items():
        #     if k in self.params:
        #         self.params[k] = v
        #         print(f"[OpenAiApi] Updating the key '{k}' to '{v}' in params.")
        super().set_params(new_params)

    def list_models(self):
        return list_models(f"{self.base_url}")


