import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Adjust path to import from interactive_mode.py in the root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import from interactive_mode
from interactive_mode import (
    handle_input_submission,
    conversation_messages,
    # agent as actual_agent, # We will mock this
    # initialize_agent_and_apis, # Not directly called in tests, setup mocks instead
    get_status_text,
    get_response_formatted_text,
    # No need to import PtkTextArea, get_app for now, will mock them where needed
)

class TestInteractiveMode(unittest.TestCase):
    def setUp(self):
        # Reset conversation messages for each test
        conversation_messages.clear()
        # Add a consistent initial message if your functions expect one,
        # or clear it if they should start from scratch.
        # For these tests, starting fresh or with a minimal system message is fine.
        # conversation_messages.append(("system", "Initial message for test setup"))


        # Mock the global agent used by interactive_mode.py
        # Use spec=BaseAgent if BaseAgent is importable here and you want stricter mocking
        # from interactive_mode import BaseAgent # Would need BaseAgent importable
        self.mock_agent = MagicMock() # spec=BaseAgent)
        self.mock_agent.llm_apis = {"mock_api_1": MagicMock(), "mock_api_2": MagicMock()}

        # Mock internal state and methods that read/write it
        self.mock_agent.active_api_name = "mock_api_1" # Initial mocked state
        self.mock_agent.active_llm_api = self.mock_agent.llm_apis["mock_api_1"]
        self.mock_agent.active_llm_api.base_url = "http://mock_api_1/api" # Initial base_url

        # get_active_api_name mock reads the mocked internal state
        self.mock_agent.get_active_api_name = MagicMock(side_effect=lambda: self.mock_agent.active_api_name)

        # set_active_api mock updates the mocked internal state
        def mock_set_active_api_behavior(api_name_param):
            if api_name_param in self.mock_agent.llm_apis:
                self.mock_agent.active_api_name = api_name_param
                self.mock_agent.active_llm_api = self.mock_agent.llm_apis[api_name_param]
                # Update base_url based on the new active_llm_api mock
                if api_name_param == "mock_api_1":
                    self.mock_agent.active_llm_api.base_url = "http://mock_api_1/api"
                elif api_name_param == "mock_api_2":
                    self.mock_agent.active_llm_api.base_url = "http://mock_api_2/api"
                else:
                    self.mock_agent.active_llm_api.base_url = "http://default_mock/api"
                return True
            return False
        self.mock_agent.set_active_api = MagicMock(side_effect=mock_set_active_api_behavior)

        self.mock_agent.message_count = 0
        self.mock_agent.token_count = 0
        self.mock_agent.generate_response.return_value = "Mocked LLM response"

        self.agent_patcher = patch('interactive_mode.agent', self.mock_agent)
        self.mock_interactive_agent = self.agent_patcher.start() # This is self.mock_agent

        # Mock Buffer object for handle_input_submission
        self.mock_buffer = MagicMock()
        self.mock_buffer.text = ""
        # Add a reset method to the mock_buffer that clears its text attribute
        def mock_reset():
            self.mock_buffer.text = ""
        self.mock_buffer.reset = MagicMock(side_effect=mock_reset)


    def tearDown(self):
        self.agent_patcher.stop()
        conversation_messages.clear() # Clean up global state

    def test_handle_input_submission_normal_message(self):
        self.mock_buffer.text = "Hello"
        handle_input_submission(self.mock_buffer)

        # Check user message
        self.assertIn(("user", "Hello"), conversation_messages)
        # Check LLM call
        self.mock_interactive_agent.generate_response.assert_called_once_with("Hello")
        # Check LLM response message
        self.assertIn(("llm", "Mocked LLM response"), conversation_messages)
        # Check buffer reset
        self.mock_buffer.reset.assert_called_once()
        self.assertEqual(self.mock_buffer.text, "")


    def test_handle_input_submission_clear_command(self):
        conversation_messages.append(("user", "some message")) # Add a dummy message
        self.mock_buffer.text = "/clear"
        handle_input_submission(self.mock_buffer)

        self.assertEqual(len(conversation_messages), 1)
        self.assertEqual(conversation_messages[0], ("system", "Conversation cleared."))
        self.mock_buffer.reset.assert_called_once()
        self.assertEqual(self.mock_buffer.text, "")

    def test_handle_input_submission_help_command(self):
        self.mock_buffer.text = "/help"
        handle_input_submission(self.mock_buffer)

        # Check that a system message was added
        self.assertTrue(any(msg[0] == "system" for msg in conversation_messages))
        # Check that the help content is in the last system message
        help_content_found = False
        for sender, text in conversation_messages:
            if sender == "system" and "Available commands:" in text:
                help_content_found = True
                break
        self.assertTrue(help_content_found, "Help message content not found.")
        self.mock_buffer.reset.assert_called_once()
        self.assertEqual(self.mock_buffer.text, "")

    def test_handle_input_submission_api_switch_valid(self):
        self.mock_buffer.text = "/api mock_api_2"
        # Initial state for get_active_api_name is "mock_api_1" due to setUp.
        # The side_effect on set_active_api (configured in setUp) should change this.

        handle_input_submission(self.mock_buffer) # Single call to the function under test

        self.mock_agent.set_active_api.assert_called_once_with("mock_api_2")

        expected_message_content = "Successfully switched to API: mock_api_2"
        found_message = False
        # Ensure conversation_messages is checked correctly after the call
        # print(f"Debug conversation_messages: {conversation_messages}") # Conceptual debug
        for msg_type, msg_text in conversation_messages:
            if msg_type == "system" and expected_message_content in msg_text:
                found_message = True
                break
        self.assertTrue(found_message, f"API switch success message not found. Expected: '{expected_message_content}'. Actual: {conversation_messages}")
        self.mock_buffer.reset.assert_called_once()


    def test_handle_input_submission_api_switch_invalid(self):
        self.mock_interactive_agent.set_active_api.return_value = False # Simulate failure
        self.mock_buffer.text = "/api invalid_api"
        handle_input_submission(self.mock_buffer)

        self.mock_interactive_agent.set_active_api.assert_called_once_with("invalid_api")

        error_message_found = False
        for sender, text in conversation_messages:
            if sender == "system" and "Error: Unknown API 'invalid_api'" in text:
                error_message_found = True
                break
        self.assertTrue(error_message_found, "API switch error message not found.")
        self.mock_buffer.reset.assert_called_once()

    def test_get_status_text(self):
        # Agent is already mocked via self.agent_patcher
        self.mock_agent.message_count = 5 # Use self.mock_agent
        self.mock_agent.token_count = 123
        self.mock_agent.active_api_name = "test_api" # Set the internal state for get_active_api_name's side_effect
        self.mock_agent.active_llm_api.base_url = "http://test/url" # Ensure this aligns if needed

        status = get_status_text()
        self.assertIn("API: test_api", status) # get_status_text calls agent.get_active_api_name()
        self.assertIn("Endpoint: http://test/url", status)
        self.assertIn("Msgs: 5", status)
        self.assertIn("Tokens: 123", status)

    def test_get_response_formatted_text(self):
        conversation_messages.clear() # Start with a clean slate for this test
        conversation_messages.append(("user", "User message 1"))
        conversation_messages.append(("llm", "LLM response 1"))
        conversation_messages.append(("system", "System message 1"))

        formatted_text = get_response_formatted_text()
        expected_text = "You: User message 1\nLLM: LLM response 1\nSystem: System message 1"
        self.assertEqual(formatted_text, expected_text)

    @patch('interactive_mode.get_app') # Patch get_app where it's called
    def test_handle_input_submission_exit_command(self, mock_get_app):
        # Configure the mock returned by get_app()
        mock_app_instance = MagicMock()
        mock_get_app.return_value = mock_app_instance

        self.mock_buffer.text = "/exit"
        handle_input_submission(self.mock_buffer)

        mock_app_instance.exit.assert_called_once()
        self.mock_buffer.reset.assert_called_once()

if __name__ == '__main__':
    unittest.main()
