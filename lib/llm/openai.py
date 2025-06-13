from openai import OpenAI
 

from lib.llm.basellm import BaseApiLLM

class OpenAiApi(BaseApiLLM):

    def __init__(self, base_url : str, model_name: str):
        super().__init__(base_url, model_name)
        self.client = OpenAI(base_url=f"{self.base_url}/engines/v1", api_key="docker")
        print("OpenAI API -> ",self.base_url)



from openai import OpenAI, APIConnectionError # Import APIConnectionError

from lib.llm.basellm import BaseApiLLM

class OpenAiApi(BaseApiLLM):

    def __init__(self, base_url : str, model_name: str):
        super().__init__(base_url, model_name)
        self.client = OpenAI(base_url=f"{self.base_url}/engines/v1", api_key="docker")
        print("OpenAI API -> ",self.base_url)



    def generate_text(self, prompt: str, stream: bool = False,  max_tokens: int = 50) -> dict:
        default_error_response = {
            "text": "", "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0
        }
        try:
            if stream:
                completion = self.client.chat.completions.create(
                    model=f"{self.model_name}",
                    messages=[
                        {"role": "system", "content": self.params["system_prompt"]},
                        {"role": "user", "content": prompt},
                    ],
                    stream=True,
                    # max_tokens=max_tokens
                )

                full_response_text = ""
                print()
                for chunk in completion:
                    data = chunk.choices[0].delta.content
                    if data is not None:
                        full_response_text += data
                        print(data, end="", flush=True)
                print()
                return {
                    "text": full_response_text,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            else:
                completion = self.client.chat.completions.create(
                    model=f"{self.model_name}",
                    messages=[
                        {"role": "system", "content": self.params["system_prompt"]},
                        {"role": "user", "content": prompt},
                    ],
                    # max_tokens=max_tokens
                )

                text_response = ""
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0

                if completion.choices and completion.choices[0].message:
                    text_response = completion.choices[0].message.content

                if hasattr(completion, 'usage') and completion.usage:
                    prompt_tokens = completion.usage.prompt_tokens if completion.usage.prompt_tokens is not None else 0
                    completion_tokens = completion.usage.completion_tokens if completion.usage.completion_tokens is not None else 0
                    total_tokens = completion.usage.total_tokens if completion.usage.total_tokens is not None else 0

                return {
                    "text": text_response,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                }
        except APIConnectionError as e:
            print(f"Error connecting to OpenAI API: {e}")
            return default_error_response
        except Exception as e: # Catch any other unexpected errors during API call
            print(f"An unexpected error occurred with OpenAI API: {e}")
            return default_error_response
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0

            if completion.choices and completion.choices[0].message:
                text_response = completion.choices[0].message.content

            if hasattr(completion, 'usage') and completion.usage:
                prompt_tokens = completion.usage.prompt_tokens if completion.usage.prompt_tokens is not None else 0
                completion_tokens = completion.usage.completion_tokens if completion.usage.completion_tokens is not None else 0
                total_tokens = completion.usage.total_tokens if completion.usage.total_tokens is not None else 0

            # print(completion) # Optional: for debugging the raw completion object
            return {
                "text": text_response,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }



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
 