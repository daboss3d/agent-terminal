from openai import OpenAI, APIConnectionError # Import APIConnectionError
from typing import Generator, Union, Dict # Added

from lib.llm.basellm import BaseApiLLM

class OpenAiApi(BaseApiLLM):

    def __init__(self, base_url : str, model_name: str):
        super().__init__(base_url, model_name)
        # Ensure base_url for OpenAI client doesn't doubly append common suffixes if already present
        # The OpenAI client itself often handles this, but good to be mindful.
        # For v1.x client, base_url should be the base (e.g. http://localhost:1234/v1)
        # and then methods like client.chat.completions.create use paths relative to that.
        # The example path "/engines/v1" seems specific to older local proxy setups, might not be needed for all.
        # For now, assume it's correct for the user's setup.
        self.client = OpenAI(base_url=self.base_url, api_key="docker") # Simplified base_url usage if possible
        # self.client = OpenAI(base_url=f"{self.base_url}/engines/v1", api_key="docker") # Original
        print("OpenAI API -> ",self.base_url)


    def generate_text(self, prompt: str, stream: bool = False,  max_tokens: int = 50) -> Generator[Union[str, Dict], None, None]:
        default_error_dict = {
            "text": "Error during generation.",
            "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
            "is_final_metadata": True
        }
        try:
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0

            if stream:
                completion = self.client.chat.completions.create(
                    model=self.model_name, # No f-string needed if model_name is already a string
                    messages=[
                        {"role": "system", "content": self.params["system_prompt"]},
                        {"role": "user", "content": prompt},
                    ],
                    stream=True,
                    stream_options={"include_usage": True}
                )

                # print() # Removed for generator
                for chunk in completion:
                    if chunk.choices: # Ensure choices are present
                        delta = chunk.choices[0].delta
                        if delta and delta.content is not None:
                            yield delta.content # Yield text chunk

                    if chunk.usage: # Final chunk with usage info
                        usage = chunk.usage
                        prompt_tokens = usage.prompt_tokens
                        completion_tokens = usage.completion_tokens
                        total_tokens = usage.total_tokens
                        # print() # Removed for generator
                        yield { # Yield final metadata
                            "text": "", # Placeholder
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": total_tokens,
                            "is_final_metadata": True
                        }
                        return # End generation after final metadata
            else: # Non-streaming
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.params["system_prompt"]},
                        {"role": "user", "content": prompt},
                    ]
                )

                text_response = ""
                if completion.choices and completion.choices[0].message:
                    text_response = completion.choices[0].message.content or ""

                if hasattr(completion, 'usage') and completion.usage:
                    prompt_tokens = completion.usage.prompt_tokens if completion.usage.prompt_tokens is not None else 0
                    completion_tokens = completion.usage.completion_tokens if completion.usage.completion_tokens is not None else 0
                    total_tokens = completion.usage.total_tokens if completion.usage.total_tokens is not None else 0

                yield text_response # Yield accumulated text
                yield { # Yield final metadata
                    "text": text_response,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "is_final_metadata": True
                }
        except APIConnectionError as e:
            print(f"Error connecting to OpenAI API: {e}")
            yield default_error_dict
        except Exception as e:
            print(f"An unexpected error occurred with OpenAI API: {e}")
            yield default_error_dict



    def set_params(self, new_params: dict) -> None:

        # key_to_check = 'system_prompt'
        # if key_to_check in new_params:
        #     print(f"Updating the key '{key_to_check}' in params.")

        # for k, v in new_params.items():
        #     if k in self.params:
        #         self.params[k] = v
        #         print(f"[OpenAiApi] Updating the key '{k}' to '{v}' in params.")
        super().set_params(new_params)


    def list_models(self):
        # Getting models from OpenAI API
        print("Defined:",self.base_url, " Model ->", self.model_name)

        # client = OpenAI(base_url=f"{self.base_url}/engines/v1", api_key="docker")
        models = self.client.models.list()

        listModels = []
        for model in models:
            #print(f"Model Name: {model.id}, Model Owner: {model.owner}, Created: {model.created}")
            return [model.id for model in models] 

        return models


        # return response.data
 