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
                    { "role": "system", "content": "respond to the question"},
                    { "role": "user", "content": prompt},
                ],
                stream = True
            )

            for chunk in completion:
                data = chunk.choices[0].delta.content
                if data != None:
                    print(data, end="")


        else:
            completion = self.client.chat.completions.create(
                model = f"{self.model_name}",
                messages = [
                    { "role": "system", "content": "respond to the question"},
                    { "role": "user", "content": prompt},
                ]
            )
            print(completion)



    def set_params(self, new_params: dict) -> None:
        print(f"Parameters updated: {new_params}")

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
 