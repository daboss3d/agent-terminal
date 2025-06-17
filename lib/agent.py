from lib.llm.basellm import BaseApiLLM
from lib.llm.ollama import OllamaApi # For type hinting
from lib.llm.openai import OpenAiApi # For type hinting
from lib.utils.text import colorize

class BaseAgent:
    def __init__(self, llm_apis: dict[str, BaseApiLLM], default_api_name: str = None):
        self.llm_apis: dict[str, BaseApiLLM] = llm_apis
        self.active_llm_api: BaseApiLLM = None
        self.active_api_name: str = None
        self.message_count: int = 0
        self.token_count: int = 0 # Placeholder for future token counting

        if default_api_name and default_api_name in self.llm_apis:
            self.set_active_api(default_api_name)
        elif self.llm_apis:
            # Set the first available API as active if no default is specified or if specified default is invalid
            first_api_name = next(iter(self.llm_apis))
            self.set_active_api(first_api_name)

    def set_active_api(self, api_name: str) -> bool:
        # print(f"DEBUG_AGENT: Attempting to set active API to: {api_name}") # Removed
        if api_name in self.llm_apis:
            self.active_llm_api = self.llm_apis[api_name]
            self.active_api_name = api_name
            print(f"Agent: Active API set to '{api_name}'.")
            # print(f"DEBUG_AGENT: Active API is now: {self.active_api_name}") # Removed
            return True
        else:
            print(f"Error: API '{api_name}' not found in available LLMs.")
            return False

    def get_active_api_name(self) -> str:
        return self.active_api_name if self.active_llm_api else "None"

    def generate_response(self, prompt: str, stream: bool = False) -> str | None:
        if not self.active_llm_api:
            print("Error: No active LLM API selected.")
            return None

        # LLM API now returns a dictionary
        llm_response_data = self.active_llm_api.generate_text(prompt, stream=stream)

        if llm_response_data is None:
            # Handle case where API might fail and return None (e.g. connection error)
            return None

        self.message_count += 1
        self.token_count += llm_response_data.get("total_tokens", 0)

        # print(f"DEBUG_AGENT: Generating response with API: {self.active_api_name}") # Removed
        # print(f"DEBUG_AGENT: Prompt passed to LLM: '{prompt[:100]}...'") # Removed
        # if llm_response_data: # Removed block
            # print(f"DEBUG_AGENT: LLM response data: {llm_response_data}")
            # print(f"DEBUG_AGENT: Tokens for this call: {llm_response_data.get('total_tokens', 0)}")
        # print(f"DEBUG_AGENT: Cumulative message count: {self.message_count}") # Removed
        # print(f"DEBUG_AGENT: Cumulative token count: {self.token_count}") # Removed

        return llm_response_data.get("text")

    def print_status(self):
        active_api_name = self.get_active_api_name()
        active_api_str = colorize(active_api_name, "green") if self.active_llm_api else colorize(active_api_name, "red")

        status_lines = [
            "Status:",
            f"  Active API: {active_api_str}",
            f"  Messages Sent: {self.message_count}",
            f"  Tokens Used: {self.token_count}"
        ]
        print("\n".join(status_lines))

if __name__ == '__main__':
    # Example Usage (Optional: for basic testing directly within the file)
    # This part would require mock LLM APIs or actual running instances for full testing.

    # Mock/Dummy LLM API classes for demonstration
    class MockLLM(BaseApiLLM):
        def __init__(self, api_url: str, model_name: str, api_key: str = None):
            super().__init__(api_url, model_name, api_key)
            print(f"MockLLM '{model_name}' initialized at '{api_url}'.")

        def list_models(self) -> list[str]:
            return [self.model_name, "mock-model-2"]

        def generate_text(self, prompt: str, stream: bool = False, max_tokens: int = 50) -> dict: # Updated mock
            print(f"MockLLM '{self.model_name}' received prompt: '{prompt}'. Stream: {stream}")
            mock_text = f"Mocked response to: {prompt}"
            if stream:
                print("Streaming response chunk 1...")
                print("Streaming response chunk 2...")
                mock_text = "Mocked streamed response."

            # Mock token counts
            mock_prompt_tokens = len(prompt.split())
            mock_completion_tokens = len(mock_text.split())
            mock_total_tokens = mock_prompt_tokens + mock_completion_tokens

            return {
                "text": mock_text,
                "prompt_tokens": mock_prompt_tokens,
                "completion_tokens": mock_completion_tokens,
                "total_tokens": mock_total_tokens
            }

        def get_status(self) -> dict:
            return {"name": self.model_name, "status": "mocked_ok", "url": self.api_url}

    mock_openai_api = MockLLM("http://localhost:1234", "mock-gpt-4")
    mock_ollama_api = MockLLM("http://localhost:11434", "mock-llama2")

    available_apis = {
        "openai": mock_openai_api,
        "ollama": mock_ollama_api
    }

    print("\n--- Agent Initialization Test ---")
    # Test 1: Initialize with a default API
    agent1 = BaseAgent(llm_apis=available_apis, default_api_name="openai")
    print(f"Agent1 active API: {agent1.get_active_api_name()}")

    # Test 2: Initialize without a default API (should pick the first one)
    agent2 = BaseAgent(llm_apis=available_apis)
    print(f"Agent2 active API: {agent2.get_active_api_name()}") # Should be 'openai' as it's first

    # Test 3: Initialize with an invalid default API
    agent3 = BaseAgent(llm_apis=available_apis, default_api_name="nonexistent_api")
    print(f"Agent3 active API: {agent3.get_active_api_name()}") # Should default to first

    # Test 4: Initialize with empty APIs (should handle gracefully)
    empty_apis = {}
    agent_empty = BaseAgent(llm_apis=empty_apis)
    print(f"Agent_empty active API: {agent_empty.get_active_api_name()}")


    print("\n--- API Switching Test ---")
    agent = BaseAgent(llm_apis=available_apis, default_api_name="openai")
    print(f"Initial active API: {agent.get_active_api_name()}")
    agent.set_active_api("ollama")
    print(f"Switched active API: {agent.get_active_api_name()}")
    agent.set_active_api("nonexistent_api") # Try switching to an invalid API
    print(f"After trying invalid switch, active API: {agent.get_active_api_name()}")


    print("\n--- Response Generation Test ---")
    # Ensure an API is active, e.g., 'ollama' from previous step
    if agent.active_llm_api:
        print(f"Generating response using: {agent.get_active_api_name()}")
        response = agent.generate_response("Hello, agent!")
        print(f"Agent response: {response}")
        print(f"Message count: {agent.message_count}")

        print(f"\nGenerating streamed response using: {agent.get_active_api_name()}")
        response_stream = agent.generate_response("Tell me a story.", stream=True)
        # In a real stream=True scenario, generate_text would likely yield chunks.
        # Here, our mock just prints and returns a final string.
        print(f"Agent response (streamed): {response_stream}")
        print(f"Message count: {agent.message_count}")
        agent.print_status() # Demonstrate print_status
    else:
        print("Skipping response generation test as no API is active.")

    # Test response generation when no API is active
    print("\n--- No Active API Test ---")
    agent_no_api = BaseAgent(llm_apis=empty_apis)
    agent_no_api.print_status() # Status before any action
    response_no_api = agent_no_api.generate_response("Test prompt")
    print(f"Response when no API active: {response_no_api}, Count: {agent_no_api.message_count}")
    agent_no_api.print_status() # Status after attempting action

    print("\n--- End of BaseAgent Tests ---")
