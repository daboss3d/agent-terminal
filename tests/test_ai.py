import pytest
import sys
from unittest.mock import patch, MagicMock

# Assuming lib.ai is importable and OpenAiApi is in lib.llm.openai
# Adjust the import path if your project structure is different.
from lib.ai import main, run_interactive_mode
from lib.llm.openai import OpenAiApi


@patch('lib.ai.run_interactive_mode')
def test_interactive_mode_triggered_by_i_argument(mock_run_interactive):
    """Test that interactive mode is triggered by the -i argument."""
    sys.argv = ['lib/ai.py', '-i']
    main()
    mock_run_interactive.assert_called_once()

@patch('lib.ai.run_interactive_mode')
def test_interactive_mode_triggered_by_interactive_argument(mock_run_interactive):
    """Test that interactive mode is triggered by the --interactive argument."""
    sys.argv = ['lib/ai.py', '--interactive']
    main()
    mock_run_interactive.assert_called_once()

@patch('lib.ai.OpenAiApi')
@patch('lib.ai.PromptSession')
@patch('lib.ai.Panel') # Mock Panel where it is used in lib.ai
@patch('lib.ai.Console')
def test_interactive_mode_input_handling_and_response_display(mock_console, mock_lib_ai_panel, mock_prompt_session, mock_openai_api): # Renamed mock_rich_panel
    """Test input handling and response display in interactive mode."""
    # Configure mocks
    mock_session_instance = mock_prompt_session.return_value
    mock_session_instance.prompt.side_effect = ["hello llm", "exit"]

    mock_llm_instance = mock_openai_api.return_value
    mock_llm_instance.generate_text.return_value = "LLM response to hello"

    mock_screen_instance = MagicMock()
    mock_console_instance = mock_console.return_value
    mock_console_instance.screen.return_value.__enter__.return_value = mock_screen_instance

    # Call the function under test
    run_interactive_mode(api_endpoint="dummy_api", model_name="dummy_model")

    # Assertions
    mock_prompt_session.assert_called_once()
    mock_session_instance.prompt.assert_any_call("> ")

    mock_openai_api.assert_called_with("dummy_api", "dummy_model")
    mock_llm_instance.generate_text.assert_called_once_with("hello llm", stream=False)

    # Check that Rich Panel was called with the expected content
    panel_call_args_list = mock_lib_ai_panel.call_args_list # Use the renamed mock

    # Expected texts within Panel calls
    expected_texts_in_panels = [
        "Status: Idle | LLM API: dummy_api | Model: dummy_model", # Initial status
        "Status: Processing... | LLM API: dummy_api | Model: dummy_model", # Processing status
        "LLM response to hello", # LLM Response
        "Status: Idle | LLM API: dummy_api | Model: dummy_model"  # Final status
    ]

    # Extract text from Text objects passed to Panel
    found_texts_in_panels = []
    for call_args in panel_call_args_list:
        args, kwargs = call_args
        if args and hasattr(args[0], 'plain'): # Check if the first arg is a Rich Text object
            found_texts_in_panels.append(args[0].plain)
        elif kwargs and 'renderable' in kwargs and hasattr(kwargs['renderable'], 'plain'):
             found_texts_in_panels.append(kwargs['renderable'].plain)
        elif args and isinstance(args[0], str): # For simple string cases like Panel("", title="LLM Response")
            found_texts_in_panels.append(args[0])


    # print(f"DEBUG: Found texts in Panel calls: {found_texts_in_panels}") # For debugging

    for expected_text in expected_texts_in_panels:
        assert any(expected_text in found_text for found_text in found_texts_in_panels), \
            f"Expected text '{expected_text}' not found in any Panel."

    # Verify screen was updated multiple times (initial, processing, after response)
    assert mock_screen_instance.update.call_count >= 3


@patch('lib.ai.test_openai')
def test_non_interactive_mode_preservation(mock_test_openai):
    """Test that non-interactive mode is preserved."""
    sys.argv = ['lib/ai.py', 'test prompt']
    main()
    mock_test_openai.assert_called_once_with('test prompt', False)

@patch('lib.ai.test_openai')
def test_non_interactive_mode_with_stream(mock_test_openai):
    """Test non-interactive mode with stream argument."""
    sys.argv = ['lib/ai.py', 'test prompt', '--stream']
    main()
    mock_test_openai.assert_called_once_with('test prompt', True)

@patch('builtins.print') # Mock print to check help message
@patch('sys.exit')      # Mock sys.exit to prevent test termination
def test_non_interactive_mode_no_prompt(mock_exit, mock_print):
    """Test non-interactive mode without a prompt."""
    sys.argv = ['lib/ai.py']
    main()
    mock_print.assert_any_call("Error: Prompt is required when not in interactive mode.")
    mock_exit.assert_called_once_with(1)

# Further tests could include:
# - Testing different LLM responses (empty, long, errors from LLM)
# - Testing status panel updates more directly if Rich provides a way to inspect Panel content easily.
# - Testing graceful exit with Ctrl+D (EOFError) - this is harder to simulate without a real PTY.

# Note on testing Rich/PromptToolkit UIs:
# Testing UIs built with libraries like Rich and PromptToolkit can be complex because they
# often involve terminal manipulation and event loops.
# - For Rich, you might need to capture output or use specific testing utilities if available.
# - For PromptToolkit, mocking the PromptSession is usually the way to go, as done above.
# The test_interactive_mode_input_handling_and_response_display is a good example of the complexities.
# It tries to assert that the UI *would* display correctly by checking calls to underlying methods.
# A more advanced approach might involve a "headless" terminal emulator or specific test drivers
# for these libraries, but that's often beyond the scope of typical unit tests.
