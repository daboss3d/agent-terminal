from openai import OpenAI
 

from lib.llm.basellm import BaseApiLLM

class OpenAiApi(BaseApiLLM):

    def __init__(self, base_url : str, model_name: str):
        super().__init__(base_url, model_name)
        self.client = OpenAI(base_url=f"{self.base_url}/engines/v1", api_key="docker")
        print("OpenAI API -> ",self.base_url)



    def generate_text(self, prompt: str, stream: bool = True,  max_tokens: int = 50) -> str:

        if stream:
            completion = self.client.chat.completions.create(
                model = f"{self.model_name}",
                messages = [
                    { "role": "system", "content": self.params["system_prompt"]},
                    { "role": "user", "content": prompt},
                ],
                stream = True
            )

            response_content = ""
            for chunk in completion:
                data = chunk.choices[0].delta.content
                if data: # Check if data is not None and not empty
                    response_content += data
                    yield data # Yield each chunk for streaming
            # When streaming, we might not need to return the full accumulated content here,
            # as it's yielded. However, if a return value is expected by some callers
            # when stream=True, this might need adjustment. For now, focus on yielding.
            # return response_content
            return # Ensure a clear return path if needed, or rely on StopIteration

        else: # Not streaming
            completion = self.client.chat.completions.create(
                model = f"{self.model_name}",
                messages = [
                    { "role": "system", "content": self.params["system_prompt"]},
                    { "role": "user", "content": prompt},
                ],
                stream = False # Explicitly False
            )
            # Extract the text content from the completion
            if completion.choices and completion.choices[0].message:
                return completion.choices[0].message.content
            return "" # Return empty string if no content



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
 