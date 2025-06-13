import pytest
import sys
from unittest.mock import patch, MagicMock, call

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

    # Simulate streaming response
    def mock_streaming_generate_text(prompt, stream=True):
        if stream:
            yield "LLM "
            yield "response "
            yield "to "
            yield "hello"
        else: # Fallback for non-streaming calls if any (though current code uses stream=True)
            return "LLM response to hello (non-streamed)"

    mock_llm_instance.generate_text.side_effect = mock_streaming_generate_text

    mock_screen_instance = MagicMock()
    mock_console_instance = mock_console.return_value
    mock_console_instance.screen.return_value.__enter__.return_value = mock_screen_instance

    # Check that Rich Panel was called with the expected content, including progressive updates
    # panel_call_args_list = mock_lib_ai_panel.call_args_list # Original approach

    captured_panel_plain_texts_at_call_time = []
    def capture_panel_text_on_call(*args, **kwargs):
        # This function will be the side_effect for mock_lib_ai_panel constructor
        # It captures the 'plain' text of the first argument if it's a Text object.
        if args and len(args) > 0:
            renderable = args[0]
            title = kwargs.get('title', '') # Capture title to differentiate panels if needed

            # We are interested in the main "LLM Response" panel's content progression
            # and also status panels.
            if title == "LLM Response":
                if hasattr(renderable, 'plain'):
                    captured_panel_plain_texts_at_call_time.append(renderable.plain)
                elif isinstance(renderable, str): # e.g. Panel("", title="LLM Response")
                    captured_panel_plain_texts_at_call_time.append(renderable)
            elif title == "Status": # Capture status texts as well
                 if hasattr(renderable, 'plain'):
                    captured_panel_plain_texts_at_call_time.append(renderable.plain)
        return MagicMock() # Each call to Panel() should return a new mock instance

    mock_lib_ai_panel.side_effect = capture_panel_text_on_call # **** SET SIDE_EFFECT HERE ****

    # Call the function under test
    run_interactive_mode(api_endpoint="dummy_api", model_name="dummy_model")

    actual_panel_renderable_texts = captured_panel_plain_texts_at_call_time

    # Assertions
    mock_prompt_session.assert_called_once()
    mock_session_instance.prompt.assert_any_call("> ")

    mock_openai_api.assert_called_with("dummy_api", "dummy_model")
    # Assert that generate_text was called with stream=True
    mock_llm_instance.generate_text.assert_called_once_with("hello llm", stream=True)

    # The side_effect defined above will populate captured_panel_plain_texts_at_call_time

    # Expected texts within Panel calls, including intermediate streamed content
    # These are now checked directly against actual_panel_renderable_texts
    # ... (expected_panel_contents list can be removed or used for reference) ...

    # print(f"DEBUG: Actual panel renderable texts from side_effect: {actual_panel_renderable_texts}")

    # Check for status updates and progressive response text
    # Note: The order of panel creation for status vs response might vary slightly depending on
    # how run_interactive_mode is structured. The key is that these texts appear.

    # Status panel texts that should appear
    assert "Status: Idle | LLM API: dummy_api | Model: dummy_model" in actual_panel_renderable_texts
    assert "Status: Processing... | LLM API: dummy_api | Model: dummy_model" in actual_panel_renderable_texts

    # Response panel texts, showing progression
    assert "" in actual_panel_renderable_texts # Initial empty response panel
    assert "LLM " in actual_panel_renderable_texts
    assert "LLM response " in actual_panel_renderable_texts
    assert "LLM response to " in actual_panel_renderable_texts
    assert "LLM response to hello" in actual_panel_renderable_texts

    # Verify screen was updated multiple times.
    # screen.update is called:
    #  1. Initial layout
    #  2. Status processing
    #  3. Initial empty response panel (after clearing, before streaming)
    #  4. For each chunk (4 chunks)
    #  5. Final status idle
    # Total expected: 1 + 1 + 1 + 4 + 1 = 8 updates.
    # Let's stick to a general check of >= 7 as before, as exact counts can be fragile.
    assert mock_screen_instance.update.call_count >= 7


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

@patch('lib.ai.Console') # Mock console to prevent actual screen rendering
@patch('lib.ai.PromptSession') # Mock session
@patch('lib.ai.OpenAiApi') # Mock LLM
def test_interactive_layout_structure(mock_openai_api, mock_prompt_session, mock_console):
    """Test that the Rich layout in interactive mode has the 'prompt_reserve' area."""

    # Need to allow run_interactive_mode to execute enough to set up the layout.
    # Mock session.prompt to immediately raise EOFError to exit the loop.
    mock_session_instance = mock_prompt_session.return_value
    mock_session_instance.prompt.side_effect = EOFError("Simulated exit for test")

    # Mock console.screen to avoid issues with non-terminal environment
    mock_screen_instance = MagicMock()
    mock_console_instance = mock_console.return_value
    mock_console_instance.screen.return_value.__enter__.return_value = mock_screen_instance

    # We need to capture the RichLayout instance.
    # The easiest way is to patch RichLayout itself, then inspect its instance.
    # However, run_interactive_mode creates RichLayout locally.
    # So, we'll patch 'lib.ai.RichLayout'

    with patch('lib.ai.RichLayout') as mock_rich_layout_constructor:
        mock_layout_instance = MagicMock()
        mock_rich_layout_constructor.return_value = mock_layout_instance

        try:
            run_interactive_mode(api_endpoint="dummy_api", model_name="dummy_model")
        except EOFError:
            pass # Expected due to prompt mock

        # The mock_rich_layout_constructor will be called multiple times:
        # 1. For RichLayout(name="root")
        # 2. For RichLayout(name="header", size=3)
        # 3. For RichLayout(name="main", ratio=1)
        # 4. For RichLayout(name="prompt_reserve", size=1)
        # We are interested in the instance created for "root" (mock_layout_instance)
        # and the arguments to the constructor when "prompt_reserve" is created.

        # Ensure the first call was for the root.
        assert mock_rich_layout_constructor.call_args_list[0] == call(name='root'), \
            "First call to RichLayout was not for name='root'"

        # Check the calls to split_column on the instance returned by the first call
        # (which we've set to mock_layout_instance)
        # The call we are interested in is:
        # rich_layout.split_column(
        #     RichLayout(name="header", size=3),
        #     RichLayout(name="main", ratio=1),
        #     RichLayout(name="prompt_reserve", size=1)
        # )
        # We need to check the arguments to the *method* split_column of the *instance*

        assert mock_layout_instance.split_column.call_count == 1
        args, kwargs = mock_layout_instance.split_column.call_args

        # Check the names and sizes/ratios of the created sub-layouts
        # These sub-layouts are themselves RichLayout objects, but they are created
        # *before* being passed to split_column. So we expect RichLayout constructor
        # to be called multiple times.
        # Instead, let's check the arguments passed to split_column.

        # The arguments to split_column are other RichLayout instances.
        # We need to ensure these instances have the correct names and sizes/ratios.
        # This is a bit tricky as they are created inline.

        # A simpler check: Verify that the mocked layout_instance (which is what's used in the code)
        # had its __setitem__ called to assign the sub-layouts and then .update() called on them.
        # This doesn't directly verify the structure of split_column's arguments as easily.

        # Alternative: Check the structure of the layout *after* it's been built.
        # The actual instance `rich_layout` inside `run_interactive_mode` is what we want to inspect.
        # Since we mocked the constructor, `mock_layout_instance` is that instance.

        # The names of the regions are 'header', 'main', 'prompt_reserve'
        # Accessing them via __getitem__ on the layout instance:
        # e.g. layout_instance['prompt_reserve']
        # We need to ensure that split_column was called with arguments that, when processed,
        # result in these named regions with correct properties.

        # Let's refine the check on split_column's arguments.
        # The arguments are RichLayout objects.
        # We can't easily access the arguments to *their* constructors if they were created inline.

        # Let's assume the structure based on the names and sizes given in the `split_column` call.
        # The `split_column` method itself would store these.
        # If we had access to the *actual* layout instance, we could inspect its `children` or similar.
        # Since `mock_layout_instance` is that instance, we can check its `children` if RichLayout populates that.
        # (This is an assumption about RichLayout's internal structure)

        # Let's assume the names are keys in the layout after split_column
        # The `split_column` method configures the layout instance.
        # We can check if the instance has regions with the expected names and properties.
        # This requires `RichLayout` to store its children in a way we can access by name,
        # and that these children store their size/ratio.

        # The `Layout` class in Rich allows access to its children maps.
        # `mock_layout_instance.children` might be a list.
        # `mock_layout_instance.map` might be a dict.

        # Let's check the call to split_column.
        # The arguments are other RichLayout objects.
        # We can check their `name`, `size`, `ratio` attributes *if they are set on construction*.

        # args is a tuple of RichLayout objects passed to split_column
        passed_layouts = args
        assert len(passed_layouts) == 3

        header_layout_arg, main_layout_arg, prompt_reserve_layout_arg = passed_layouts

        # These are mock objects if RichLayout was mocked *everywhere*.
        # If RichLayout is only mocked once (for the root), then these are real RichLayouts.
        # The current patch is `@patch('lib.ai.RichLayout')`, so all RichLayouts created
        # in run_interactive_mode will be `mock_layout_instance` if not careful.
        # This means `header_layout_arg` would be a *new* MagicMock if `RichLayout()` is called again.

        # Let's reset the mock for sub-layouts and check constructor calls for them.
        # This is getting too complex.

        # Simplest robust check for this specific change:
        # Ensure split_column was called and *assume* if the names are right, it's likely correct.
        # Or, more directly, that the instance `mock_layout_instance` *has* a child 'prompt_reserve'
        # and that child has the correct size. This requires `split_column` to populate named children.

        # Rich's Layout's __setitem__ is used to add children layouts, which are then updated.
        # Let's verify the calls to `update` on these children.
        # First, ensure split_column was called.
        mock_layout_instance.split_column.assert_called()

        # Now, how to get a reference to the 'prompt_reserve' layout child?
        # The code does: rich_layout["prompt_reserve"].update("")
        # So, we need to ensure that `mock_layout_instance.__getitem__` is called with 'prompt_reserve'
        # and the object it returns (the child layout) has `update("")` called on it.
        # And critically, that this child layout was created with size=1.

        # To check the size of "prompt_reserve", we need to capture how it was created.
        # This means we need to inspect the arguments to `split_column`.
        # The arguments to `split_column` are `RichLayout` instances.
        # Let's make `mock_rich_layout_constructor` return new mocks each time to differentiate.

        # Re-patching RichLayout to gain more control for this specific test.
        # This test is becoming more of an integration test for layout construction.

        # Let's assume the previous test for Panel calls covers the updates.
        # This test should focus on the structure: 'prompt_reserve' exists and has size 1.

        # If we can get the actual arguments to split_column:
        sl_args, sl_kwargs = mock_layout_instance.split_column.call_args

        assert len(sl_args) == 3 # header, main, prompt_reserve
        prompt_reserve_layout_obj = sl_args[2] # This is the RichLayout(name="prompt_reserve", size=1)

        # Now, assert properties of this object.
        # This object is an argument to a method of our main mock (mock_layout_instance).
        # It should be a RichLayout instance. If RichLayout is patched, it's a mock.
        # If we want to check its properties, it needs to have them.

        # If `lib.ai.RichLayout` is patched, then `RichLayout(name="prompt_reserve", size=1)`
        # would result in a call to the mock constructor.
        # We need to check the arguments of the *third* call to the main mock constructor,
        # assuming they happen in order (root, header, main, prompt_reserve).

        # Let's list all calls to the constructor
        constructor_calls = mock_rich_layout_constructor.call_args_list
        # Expected calls:
        # 1. RichLayout(name="root")
        # 2. RichLayout(name="header", size=3)
        # 3. RichLayout(name="main", ratio=1)
        # 4. RichLayout(name="prompt_reserve", size=1)

        assert len(constructor_calls) >= 4 # At least these four calls

        # Check the call for 'prompt_reserve'
        # This relies on the order of instantiation in the source code.
        prompt_reserve_call = None
        # Use a different loop variable name to avoid shadowing the imported 'call'
        for c_call in constructor_calls:
            if c_call.kwargs.get('name') == 'prompt_reserve':
                prompt_reserve_call = c_call
                break

        assert prompt_reserve_call is not None, "RichLayout(name='prompt_reserve', ...) was not called"
        assert prompt_reserve_call.kwargs.get('size') == 1, "prompt_reserve layout does not have size=1"

# Note on testing Rich/PromptToolkit UIs:
# Testing UIs built with libraries like Rich and PromptToolkit can be complex because they
