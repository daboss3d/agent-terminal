#!/usr/bin/env python3

import sys
import os
# Ensure 'lib' can be imported when run from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from prompt_toolkit.application import Application, get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import SearchToolbar, TextArea as PtkTextArea
from prompt_toolkit.buffer import Buffer

# Real Agent and API imports
from lib.agent import BaseAgent
from lib.llm.ollama import OllamaApi
from lib.llm.openai import OpenAiApi
import requests # For exception handling

# --- Global Variables ---
agent: BaseAgent = None
conversation_messages: list[tuple[str, str]] = []
input_area: PtkTextArea = None
response_window: Window = None

# --- API Initialization and Agent Setup ---
def initialize_agent_and_apis():
    global agent, conversation_messages
    try:
        ollama_api = OllamaApi(model_name="llama2")
        openai_api = OpenAiApi(model_name="local-model", base_url="http://localhost:1234/v1")

        llm_apis = {
            "ollama": ollama_api,
            "openai": openai_api
        }
        agent = BaseAgent(llm_apis=llm_apis, default_api_name="ollama")

        conversation_messages.clear()
        conversation_messages.append(("system", "Welcome to Interactive Mode! Type /help for commands or your prompt to chat."))

    except Exception as e:
        print(f"FATAL: Could not initialize APIs or Agent: {e}", file=sys.stderr)
        sys.exit(1)

# --- UI Update and Stream Processing Functions ---

def _update_ui_with_chunk(chunk_text=None, llm_response_index=None, is_final=False, error_message=None, token_info=None):
    """
    Updates the UI with a chunk of text, error message, or final token info.
    This function is intended to be called via app.loop.call_soon_threadsafe.
    """
    app = get_app()
    if not app.is_running or llm_response_index is None or llm_response_index >= len(conversation_messages):
        return # App closed or index out of bounds

    current_sender, current_text = conversation_messages[llm_response_index]

    if error_message:
        new_text = current_text + f"\n[SYSTEM_ERROR: {error_message}]"
        conversation_messages[llm_response_index] = (current_sender, new_text)
    elif isinstance(chunk_text, str):
        new_text = current_text + chunk_text
        conversation_messages[llm_response_index] = (current_sender, new_text)

    if is_final:
        if token_info: # This is the final_metadata dict
            # Update agent's token and message counts
            # This directly modifies the global agent state.
            # Consider if these updates should also be explicitly scheduled if they affect UI directly
            # via get_status_text, which they do.
            agent.message_count += 1
            agent.token_count += token_info.get("total_tokens", 0)

            # If the final metadata itself contains an error message (e.g. from API error dict)
            if token_info.get("text") and "Error" in token_info.get("text", ""):
                # Avoid appending if it's the same as already streamed error_message
                if not error_message or error_message not in token_info.get("text",""):
                     err_text_from_meta = token_info.get("text")
                     # Ensure new_text is defined; if only metadata came, current_text is from placeholder
                     final_text_base = conversation_messages[llm_response_index][1]
                     updated_text_with_meta_error = final_text_base + f"\n[{err_text_from_meta}]"
                     conversation_messages[llm_response_index] = (current_sender, updated_text_with_meta_error)

    if app.is_running:
        app.invalidate()

def _process_llm_stream(response_generator, llm_response_index):
    """
    Processes the LLM response generator in a separate thread.
    Schedules UI updates back to the main event loop.
    """
    app = get_app() # Get app instance for its event loop
    try:
        if response_generator:
            for item in response_generator:
                if isinstance(item, str):
                    app.loop.call_soon_threadsafe(_update_ui_with_chunk, item, llm_response_index)
                elif isinstance(item, dict) and item.get("is_final_metadata"):
                    # If the dict contains an error message (e.g. from a failed API call in streaming mode)
                    error_from_meta = item.get("text") if "Error" in item.get("text", "") else None # Check for error text
                    app.loop.call_soon_threadsafe(_update_ui_with_chunk,
                                                  llm_response_index=llm_response_index,
                                                  is_final=True,
                                                  error_message=error_from_meta, # Pass potential error from metadata
                                                  token_info=item) # Pass the whole dict for token counts
                    break
    except requests.exceptions.ConnectionError as e:
        app.loop.call_soon_threadsafe(_update_ui_with_chunk,
                                      llm_response_index=llm_response_index,
                                      is_final=True, # Treat as final to update counts if applicable
                                      error_message=f"ConnectionError: {e}")
    except Exception as e: # Catch any other exceptions from the generator
        app.loop.call_soon_threadsafe(_update_ui_with_chunk,
                                      llm_response_index=llm_response_index,
                                      is_final=True,
                                      error_message=f"Stream processing error: {type(e).__name__} - {e}")
    finally:
        # Ensure a final invalidate, e.g. if generator was empty or loop was exited abruptly
        if app.is_running:
            app.loop.call_soon_threadsafe(app.invalidate)


# --- Input Handler ---
def handle_input_submission(buffer: Buffer):
    user_input_text = buffer.text.strip()
    app = get_app() # Get app for run_in_executor and its loop

    if not user_input_text:
        buffer.reset()
        return

    # Command Handling
    if user_input_text == "/clear":
        conversation_messages.clear()
        conversation_messages.append(("system", "Conversation cleared."))
        if app.is_running: app.invalidate()
        buffer.reset()
        return

    if user_input_text == "/help":
        help_msg = """
Available commands:
  /api <name>  - Switch to API (e.g., /api ollama, /api openai)
  /clear       - Clear conversation history
  /help        - Show this help message
  /exit        - Exit the application
  PageUp/PageDown or Ctrl+Up/Ctrl+Down - Scroll response panel
"""
        conversation_messages.append(("system", help_msg.strip()))
        if app.is_running: app.invalidate()
        buffer.reset()
        return

    if user_input_text == "/exit":
        app.exit()
        buffer.reset()
        return

    if user_input_text.startswith("/api "):
        parts = user_input_text.split()
        if len(parts) == 2:
            api_name_to_switch = parts[1].lower()
            if agent.set_active_api(api_name_to_switch):
                conversation_messages.append(("system", f"Successfully switched to API: {agent.get_active_api_name()}"))
            else:
                available_apis = ", ".join(agent.llm_apis.keys())
                conversation_messages.append(("system", f"Error: Unknown API '{api_name_to_switch}'. Available: {available_apis}"))
        else:
            conversation_messages.append(("system", "Usage: /api <ollama|openai>"))
        if app.is_running: app.invalidate()
        buffer.reset()
        return

    # Regular prompt processing with streaming via executor
    conversation_messages.append(("user", user_input_text))
    buffer.reset() # Reset input buffer immediately

    if not agent.active_llm_api:
        conversation_messages.append(("system", "Error: No active LLM API. Please select one using /api <name>."))
        if app.is_running: app.invalidate()
        return

    llm_response_index = len(conversation_messages)
    conversation_messages.append(("llm", "")) # Placeholder
    if app.is_running: app.invalidate() # Show placeholder immediately

    try:
        response_generator = agent.generate_response(user_input_text, stream=True)
        if response_generator:
            app.run_in_executor(_process_llm_stream, response_generator, llm_response_index)
        else: # Should not happen if agent.generate_response is well-behaved
             _update_ui_with_chunk(llm_response_index=llm_response_index, is_final=True, error_message="Failed to get response generator.")

    except Exception as e: # Catch errors from agent.generate_response itself (before executor)
        # This might happen if active_llm_api is None *after* the check, or other immediate errors
        error_msg = f"Error starting LLM request: {type(e).__name__} - {e}"
        conversation_messages[llm_response_index] = ("llm", f"[SYSTEM_ERROR: {error_msg}]")
        if app.is_running: app.invalidate()


# --- Status Panel Function --- (remains the same)
def get_status_text() -> str:
    if not agent: return "Status: Initializing..."
    api_name = agent.get_active_api_name()
    endpoint = agent.active_llm_api.base_url if agent.active_llm_api else "N/A"
    msg_count = agent.message_count
    token_c = agent.token_count
    return f"API: {api_name} | Endpoint: {endpoint} | Msgs: {msg_count} | Tokens: {token_c}"

# --- Response Panel Function --- (remains the same)
def get_response_formatted_text() -> str:
    return "\n".join(
        f"You: {text}" if sender == "user" else
        f"LLM: {text}" if sender == "llm" else
        f"System: {text}" if sender == "system" else
        f"{sender.capitalize()}: {text}"
        for sender, text in conversation_messages
    )

# --- Main Application Setup --- (remains largely the same)
def start_interactive_mode():
    global input_area, response_window

    initialize_agent_and_apis()

    status_control = FormattedTextControl(text=get_status_text, focusable=False, show_cursor=False)
    status_window = Window(content=status_control, height=1, style="bg:#444444 #ffffff")

    response_control = FormattedTextControl(text=get_response_formatted_text, focusable=True, show_cursor=False)
    response_window = Window(content=response_control, wrap_lines=True)

    input_area = PtkTextArea(
        prompt=">>> ",
        multiline=False,
        wrap_lines=False,
        search_field=SearchToolbar(),
        accept_handler=handle_input_submission
    )

    root_container = HSplit([
        status_window, Window(height=1, char='-', style='class:separator'),
        response_window, Window(height=1, char='-', style='class:separator'),
        input_area,
    ])

    layout = Layout(root_container)
    layout.focus(input_area)

    kb = KeyBindings()
    @kb.add('pageup')
    def _scroll_page_up(event):
        if response_window and response_window.render_info:
            response_window.scroll_backward(count=response_window.render_info.window_height)
            event.app.invalidate()
    @kb.add('pagedown')
    def _scroll_page_down(event):
        if response_window and response_window.render_info:
            response_window.scroll_forward(count=response_window.render_info.window_height)
            event.app.invalidate()
    @kb.add('c-up')
    def _scroll_line_up(event):
        if response_window:
            response_window.scroll_backward(count=1)
            event.app.invalidate()
    @kb.add('c-down')
    def _scroll_line_down(event):
        if response_window:
            response_window.scroll_forward(count=1)
            event.app.invalidate()

    app = Application(
        layout=layout,
        key_bindings=kb,
        full_screen=True
    )

    app.run()

    print("Exited Interactive Mode.")

if __name__ == "__main__":
    start_interactive_mode()
