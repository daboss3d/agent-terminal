
import json
import requests

from lib.llm.basellm import BaseApiLLM
from lib.utils.text import hello_text , clear_markdown_to_color
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
        "prompt": f"{explain_terminal}\n\n{prompt}"
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



# Final methods ######################################################################################

def query_stream(model_name: str, base_url : str, prompt):

    payload =   {
        "model": model_name,
        "prompt": f"{prompt}"
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
    def generate_text(self, prompt: str, stream: bool = True,  max_tokens: int = 50) -> str:

        if stream:
             query_stream(self.model_name, f"{self.base_url}/api/generate", prompt)
        else:
            # Simulate text generation
            return f"{prompt} ... (continuation with {max_tokens} tokens)"

    def set_params(self, new_params: dict) -> None:
        print(f"Parameters updated: {new_params}")

    def list_models(self):
        return list_models(f"{self.base_url}")

    def generate_text_stream(self, prompt: str):
        query_stream(self.model_name, f"{self.base_url}/api/generate", prompt)
