import sys
import os
import unittest
from unittest.mock import MagicMock, patch, call # Ensure 'call' is imported
import requests # For requests.exceptions.ConnectionError

# Adjust path to import from interactive_mode.py in the root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import from interactive_mode
from interactive_mode import (
    handle_input_submission,
    conversation_messages,
    # agent, # Will be patched
    # initialize_agent_and_apis, # Not called directly
    get_status_text,
    get_response_formatted_text,
    _process_llm_stream, # Now testing this directly
    _update_ui_with_chunk, # And this directly
    # BaseAgent # Not needed if we mock agent entirely
)

class TestInteractiveMode(unittest.TestCase):
    def setUp(self):
        conversation_messages.clear()

        # Mock the global agent used by interactive_mode.py
        self.mock_agent = MagicMock()
        self.mock_agent.llm_apis = {"mock_api_1": MagicMock(), "mock_api_2": MagicMock()}
        self.mock_agent.active_api_name = "mock_api_1"
        self.mock_agent.active_llm_api = self.mock_agent.llm_apis["mock_api_1"]
        self.mock_agent.active_llm_api.base_url = "http://mock_api_1/api"
        self.mock_agent.get_active_api_name = MagicMock(side_effect=lambda: self.mock_agent.active_api_name)

        def mock_set_active_api_behavior(api_name_param):
            if api_name_param in self.mock_agent.llm_apis:
                self.mock_agent.active_api_name = api_name_param
                self.mock_agent.active_llm_api = self.mock_agent.llm_apis[api_name_param]
                if api_name_param == "mock_api_1": self.mock_agent.active_llm_api.base_url = "http://mock_api_1/api"
                elif api_name_param == "mock_api_2": self.mock_agent.active_llm_api.base_url = "http://mock_api_2/api"
                else: self.mock_agent.active_llm_api.base_url = "http://default_mock/api"
                return True
            return False
        self.mock_agent.set_active_api = MagicMock(side_effect=mock_set_active_api_behavior)
        self.mock_agent.message_count = 0
        self.mock_agent.token_count = 0
        # generate_response will now return a generator mock
        self.mock_response_generator = MagicMock()
        self.mock_agent.generate_response.return_value = self.mock_response_generator

        self.agent_patcher = patch('interactive_mode.agent', self.mock_agent)
        self.patched_agent_mock = self.agent_patcher.start()

        # Mock get_app for UI updates and exit command
        self.mock_app_instance = MagicMock()
        self.mock_app_instance.loop = MagicMock()
        self.mock_app_instance.loop.call_soon_threadsafe = MagicMock()
        self.mock_app_instance.run_in_executor = MagicMock() # Will be called by handle_input_submission
        self.mock_app_instance.is_running = True # Assume app is running for tests calling invalidate

        self.get_app_patcher = patch('interactive_mode.get_app', return_value=self.mock_app_instance)
        self.mock_get_app = self.get_app_patcher.start()

        # Mock Buffer object for handle_input_submission
        self.mock_buffer = MagicMock()
        self.mock_buffer.text = ""
        def mock_reset(): self.mock_buffer.text = ""
        self.mock_buffer.reset = MagicMock(side_effect=mock_reset)

    def tearDown(self):
        self.agent_patcher.stop()
        self.get_app_patcher.stop()
        conversation_messages.clear()

    def test_handle_input_submission_normal_message_calls_executor(self):
        self.mock_buffer.text = "Hello"
        # Configure the response generator mock for this test if _process_llm_stream is deeply checked
        # For this test, just checking if run_in_executor is called is enough.
        # self.mock_response_generator.__iter__.return_value = iter(["Test chunk", {"is_final_metadata": True, "total_tokens": 1}])

        handle_input_submission(self.mock_buffer)

        # Check user message was added (handle_input_submission still does this directly)
        self.assertIn(("user", "Hello"), conversation_messages)
        # Check placeholder for LLM response was added
        self.assertTrue(any(msg[0] == "llm" and msg[1] == "" for msg in conversation_messages), "LLM placeholder not found")

        self.patched_agent_mock.generate_response.assert_called_once_with("Hello", stream=True)

        # Assert run_in_executor was called
        self.mock_app_instance.run_in_executor.assert_called_once()
        args, _ = self.mock_app_instance.run_in_executor.call_args
        # First arg to run_in_executor is the function, second is the first arg to that function
        self.assertEqual(args[0].__name__, '_process_llm_stream') # Check correct function passed
        self.assertEqual(args[1], self.mock_response_generator) # Check generator passed
        self.assertTrue(isinstance(args[2], int)) # llm_response_index

        self.mock_buffer.reset.assert_called_once() # Buffer is reset immediately

    # Test for _process_llm_stream (new test)
    def test_process_llm_stream_success(self):
        conversation_messages.append(("llm", "")) # Placeholder for _update_ui_with_chunk
        llm_response_index = 0

        mock_data_stream = [
            "Hello ", "world",
            {"is_final_metadata": True, "total_tokens": 5, "text": "Hello world"}
        ]
        mock_generator = iter(mock_data_stream)

        # Directly call _process_llm_stream as it would be in the executor
        _process_llm_stream(mock_generator, llm_response_index)

        expected_calls = [
            call(_update_ui_with_chunk, "Hello ", llm_response_index),
            call(_update_ui_with_chunk, "world", llm_response_index),
            call(_update_ui_with_chunk, llm_response_index=llm_response_index,
                 is_final=True, error_message=None, token_info=mock_data_stream[2])
        ]
        self.mock_app_instance.loop.call_soon_threadsafe.assert_has_calls(expected_calls, any_order=False)

    # Test for _process_llm_stream with connection error (new test)
    def test_process_llm_stream_connection_error(self):
        conversation_messages.append(("llm", "")) # Placeholder
        llm_response_index = 0

        mock_generator_with_error = MagicMock()
        mock_generator_with_error.__iter__.side_effect = requests.exceptions.ConnectionError("Test connection error")

        _process_llm_stream(mock_generator_with_error, llm_response_index)

        expected_calls = [
            call(_update_ui_with_chunk,
                 llm_response_index=llm_response_index,
                 is_final=True,
                 error_message="ConnectionError: Test connection error"),
            call(self.mock_app_instance.invalidate) # From the finally block
        ]
        self.mock_app_instance.loop.call_soon_threadsafe.assert_has_calls(expected_calls, any_order=False)
        self.assertEqual(self.mock_app_instance.loop.call_soon_threadsafe.call_count, 2)

    # Test for _update_ui_with_chunk (new test)
    def test_update_ui_with_chunk(self):
        conversation_messages.append(("llm", "Initial:")) # index 0
        llm_response_index = 0

        # Test appending chunk
        _update_ui_with_chunk(chunk_text=" Test chunk", llm_response_index=llm_response_index)
        self.assertEqual(conversation_messages[llm_response_index], ("llm", "Initial: Test chunk"))
        self.mock_app_instance.invalidate.assert_called()
        self.mock_app_instance.invalidate.reset_mock() # Reset for next call count

        # Test final update with token info
        initial_msg_count = self.patched_agent_mock.message_count
        initial_token_count = self.patched_agent_mock.token_count
        token_info = {"total_tokens": 10, "text": "Final metadata text"} # text in token_info is also checked
        _update_ui_with_chunk(llm_response_index=llm_response_index, is_final=True, token_info=token_info)

        self.assertEqual(self.patched_agent_mock.message_count, initial_msg_count + 1)
        self.assertEqual(self.patched_agent_mock.token_count, initial_token_count + 10)
        # Check if error text from metadata is appended (it shouldn't if "Error" not in text)
        self.assertNotIn("[Final metadata text]", conversation_messages[llm_response_index][1])
        self.mock_app_instance.invalidate.assert_called()
        self.mock_app_instance.invalidate.reset_mock()

        # Test error message
        _update_ui_with_chunk(llm_response_index=llm_response_index, is_final=True, error_message="An error occurred")
        self.assertIn("[SYSTEM_ERROR: An error occurred]", conversation_messages[llm_response_index][1])
        self.mock_app_instance.invalidate.assert_called()

        # Test final metadata with error text
        conversation_messages[llm_response_index] = ("llm", "Partial ") # Reset text
        token_info_with_error = {"total_tokens": 5, "text": "Error in metadata", "is_final_metadata": True}
        _update_ui_with_chunk(llm_response_index=llm_response_index, is_final=True, token_info=token_info_with_error)
        self.assertIn("[Error in metadata]", conversation_messages[llm_response_index][1])
        self.assertIn("Partial ", conversation_messages[llm_response_index][1])


    # --- Existing command tests (should largely remain the same, ensure they still pass) ---
    def test_handle_input_submission_clear_command(self):
        conversation_messages.append(("user", "some message"))
        self.mock_buffer.text = "/clear"
        handle_input_submission(self.mock_buffer)
        self.assertEqual(len(conversation_messages), 1)
        self.assertEqual(conversation_messages[0], ("system", "Conversation cleared."))
        self.mock_buffer.reset.assert_called_once()
        self.mock_app_instance.invalidate.assert_called_once() # invalidate is called for commands too

    def test_handle_input_submission_help_command(self):
        self.mock_buffer.text = "/help"
        handle_input_submission(self.mock_buffer)
        self.assertTrue(any(msg[0] == "system" and "Available commands:" in msg[1] for msg in conversation_messages))
        self.mock_buffer.reset.assert_called_once()
        self.mock_app_instance.invalidate.assert_called_once()

    def test_handle_input_submission_api_switch_valid(self):
        self.mock_buffer.text = "/api mock_api_2"
        handle_input_submission(self.mock_buffer)
        self.patched_agent_mock.set_active_api.assert_called_once_with("mock_api_2")
        self.assertTrue(any(msg[0] == "system" and "Successfully switched to API: mock_api_2" in msg[1] for msg in conversation_messages))
        self.mock_buffer.reset.assert_called_once()
        self.mock_app_instance.invalidate.assert_called_once()

    def test_handle_input_submission_api_switch_invalid(self):
        self.patched_agent_mock.set_active_api.return_value = False # Simulate failure
        self.mock_buffer.text = "/api invalid_api"
        handle_input_submission(self.mock_buffer)
        self.patched_agent_mock.set_active_api.assert_called_once_with("invalid_api")
        self.assertTrue(any(msg[0] == "system" and "Error: Unknown API 'invalid_api'" in msg[1] for msg in conversation_messages))
        self.mock_buffer.reset.assert_called_once()
        self.mock_app_instance.invalidate.assert_called_once()

    def test_get_status_text(self):
        self.patched_agent_mock.message_count = 5
        self.patched_agent_mock.token_count = 123
        self.patched_agent_mock.active_api_name = "test_api"
        self.patched_agent_mock.active_llm_api.base_url = "http://test/url"
        status = get_status_text()
        self.assertIn("API: test_api", status)
        self.assertIn("Endpoint: http://test/url", status)
        self.assertIn("Msgs: 5", status)
        self.assertIn("Tokens: 123", status)

    def test_get_response_formatted_text(self):
        conversation_messages.clear()
        conversation_messages.append(("user", "User message 1"))
        conversation_messages.append(("llm", "LLM response 1"))
        conversation_messages.append(("system", "System message 1"))
        formatted_text = get_response_formatted_text()
        expected_text = "You: User message 1\nLLM: LLM response 1\nSystem: System message 1"
        self.assertEqual(formatted_text, expected_text)

    # test_handle_input_submission_exit_command uses the mock_get_app from setUp
    def test_handle_input_submission_exit_command(self):
        self.mock_buffer.text = "/exit"
        handle_input_submission(self.mock_buffer)
        self.mock_app_instance.exit.assert_called_once()
        self.mock_buffer.reset.assert_called_once()

if __name__ == '__main__':
    unittest.main()
