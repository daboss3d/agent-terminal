#!/usr/bin/env python3

import sys
import os
# Ensure 'lib' can be imported when run from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from prompt_toolkit.application import Application, get_app # Added get_app
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
input_area: PtkTextArea = None # Still needed for layout.focus, though not for dummy run

# --- API Initialization and Agent Setup ---
def initialize_agent_and_apis():
    global agent, conversation_messages # Ensure conversation_messages is also global here
    try:
        ollama_api = OllamaApi(model_name="llama2")
        openai_api = OpenAiApi(model_name="local-model", base_url="http://localhost:1234/v1")

        llm_apis = {
            "ollama": ollama_api,
            "openai": openai_api
        }
        agent = BaseAgent(llm_apis=llm_apis, default_api_name="ollama")

        # Clear any previous messages and set initial welcome message
        conversation_messages.clear()
        conversation_messages.append(("system", "Welcome to Interactive Mode! Type /help for commands or your prompt to chat."))

    except Exception as e:
        print(f"FATAL: Could not initialize APIs or Agent: {e}", file=sys.stderr)
        sys.exit(1)


# --- Input Handler ---
def handle_input_submission(buffer: Buffer):
    user_input_text = buffer.text.strip()
    # Buffer is reset after processing, regardless of command or prompt

    if not user_input_text:
        buffer.reset()
        return

    # Command Handling
    if user_input_text == "/clear":
        conversation_messages.clear()
        conversation_messages.append(("system", "Conversation cleared."))
        buffer.reset()
        return

    if user_input_text == "/help":
        help_msg = """
Available commands:
  /api <name>  - Switch to API (e.g., /api ollama, /api openai)
  /clear       - Clear conversation history
  /help        - Show this help message
  /exit        - Exit the application
"""
        conversation_messages.append(("system", help_msg.strip()))
        buffer.reset()
        return

    if user_input_text == "/exit":
        get_app().exit()
        buffer.reset() # Reset buffer even on exit, though app will close
        return

    if user_input_text.startswith("/api "):
        parts = user_input_text.split()
        if len(parts) == 2:
            api_name_to_switch = parts[1].lower()
            if agent.set_active_api(api_name_to_switch):
                # agent.set_active_api already prints a confirmation
                # We can add another one to the conversation history if desired
                conversation_messages.append(("system", f"Successfully switched to API: {agent.get_active_api_name()}"))
            else:
                available_apis = ", ".join(agent.llm_apis.keys())
                conversation_messages.append(("system", f"Error: Unknown API '{api_name_to_switch}'. Available: {available_apis}"))
        else:
            conversation_messages.append(("system", "Usage: /api <ollama|openai>"))
        buffer.reset()
        return

    # Regular prompt processing
    conversation_messages.append(("user", user_input_text))

    if not agent.active_llm_api:
        conversation_messages.append(("system", "Error: No active LLM API. Please select one using /api <name>."))
        buffer.reset()
        return

    try:
        llm_response_text = agent.generate_response(user_input_text)
        if llm_response_text is None:
             conversation_messages.append(("system", f"Error: No response from {agent.get_active_api_name()}. Check API status."))
        elif llm_response_text.strip() == "": # Handle empty string responses
            conversation_messages.append(("system", f"Warning: Received empty response from {agent.get_active_api_name()}."))
        else:
            conversation_messages.append(("llm", llm_response_text))
    except requests.exceptions.ConnectionError:
        error_msg = f"Error: Could not connect to {agent.get_active_api_name()} at {agent.active_llm_api.base_url}. Ensure it's running."
        conversation_messages.append(("system", error_msg))
    except Exception as e:
        error_msg = f"Error generating response from {agent.get_active_api_name()}: {type(e).__name__} - {e}"
        conversation_messages.append(("system", error_msg))

    buffer.reset() # Ensure buffer is reset after processing


# --- Status Panel Function ---
def get_status_text() -> str:
    if not agent: return "Status: Initializing..."
    api_name = agent.get_active_api_name()
    endpoint = agent.active_llm_api.base_url if agent.active_llm_api else "N/A"
    msg_count = agent.message_count
    token_c = agent.token_count
    return f"API: {api_name} | Endpoint: {endpoint} | Msgs: {msg_count} | Tokens: {token_c}"

# --- Response Panel Function ---
def get_response_formatted_text() -> str:
    formatted_lines = []
    for sender, text in conversation_messages:
        if sender == "user": formatted_lines.append(f"You: {text}")
        elif sender == "llm": formatted_lines.append(f"LLM: {text}")
        elif sender == "system": formatted_lines.append(f"System: {text}") # Ensure system messages are clearly prefixed
        else: formatted_lines.append(f"{sender.capitalize()}: {text}")
    return "\n".join(formatted_lines)

def start_interactive_mode():
    global input_area

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

    app = Application(
        layout=layout,
        full_screen=True
    )

    # No "Attempting to start..." print here, as it's immediately overwritten by full_screen app.
    # If initialization fails, it prints to stderr and exits.

    app.run()

    print("Exited PyMath Interactive Mode.")

if __name__ == "__main__":
    start_interactive_mode()
