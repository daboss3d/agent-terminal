import sys
import argparse
from enum import Enum

from prompt_toolkit import PromptSession
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from rich.console import Console
from rich.layout import Layout as RichLayout
from rich.panel import Panel
from rich.text import Text
from rich.live import Live # Import Live

from lib.llm.prompts import explain_terminal, explain_question
from lib.utils.text import extract_quoted_text, remove_empty_or_whitespace_strings

from lib.llm.basellm import BaseApiLLM

from lib.llm.openai import OpenAiApi
from lib.llm.ollama import OllamaApi

class QuestionMode(str, Enum):
    state1 = 'explain_terminal'
    state2 = 'explain_question'


def contains_substring(text : str, aList : list):
    for element in aList:
        if text in element:
            return True
    return False

def filter_commands(input_list):
    return [s.strip() for s in input_list if not (s.startswith('-') or s.startswith('--'))]

# test


def test_openai(prompt: str, stream: bool = True):

    openai_api = OpenAiApi("http://127.0.0.1:12434","ai/gemma3:latest")
 
    print("Models ->",openai_api.list_models())
    openai_api.set_params({"system_prompt":"respond to the question the best you can in Arabic"})    
    openai_api.generate_text(prompt,stream=stream)




def test_ollama(prompt: str, stream: bool = True):
    
    ollama_api = OllamaApi("http://10.1.1.62:11434","devstral:latest")
    # ollama_api.print_model()
    print("Models ->",ollama_api.list_models())
    ollama_api.set_params({"system_prompt":"respond to the question the best you can in Portuguese"}) 
    txt = ollama_api.generate_text(prompt, stream)
    if (txt):
        print(txt)


# class Agent():
#     def __init__(self):
#         self.api_endpoint

def run_interactive_mode(api_endpoint, model_name):
    """Runs the interactive mode UI."""
    console = Console()
    session = PromptSession()

    status_panel = Panel(Text(f"Status: Idle | LLM API: {api_endpoint} | Model: {model_name}"), title="Status")
    response_area = Panel("", title="LLM Response")
    # input_line = Panel(session.app.layout, title="Input") # This might not be directly usable as a Panel content

    rich_layout = RichLayout(name="root")
    rich_layout.split_column(
        RichLayout(name="header", size=3),
        RichLayout(name="main", ratio=1), # Main content area, takes most space
        RichLayout(name="prompt_reserve", size=1) # Reserved space for prompt_toolkit input line
    )
    rich_layout["header"].update(status_panel)
    rich_layout["main"].update(response_area)
    # The "prompt_reserve" area is intentionally left blank or can have minimal content.
    # prompt_toolkit will draw over this line.
    rich_layout["prompt_reserve"].update("") # Explicitly make it blank

    with console.screen() as screen:
        while True:
            screen.update(rich_layout)
            try:
                prompt_text = session.prompt("> ")
                if prompt_text.lower() == "exit":
                    break

                # Update status panel
                status_panel = Panel(Text(f"Status: Processing... | LLM API: {api_endpoint} | Model: {model_name}"), title="Status")
                rich_layout["header"].update(status_panel)
                screen.update(rich_layout)

                # LLM interaction
                openai_api = OpenAiApi(api_endpoint, model_name)

                # Initialize for streaming
                accumulated_response_text = ""
                # Create a Text widget that can be updated for the response area
                response_text_widget = Text("")
                rich_layout["main"].update(Panel(response_text_widget, title="LLM Response"))
                screen.update(rich_layout) # Initial update with empty response area

                # Stream and update
                # TODO: Decide if stream=True should always be used in interactive, or based on args.
                # For now, let's assume we want to stream if possible.
                # The generate_text method now yields chunks for stream=True.
                for chunk in openai_api.generate_text(prompt_text, stream=True):
                    accumulated_response_text += chunk
                    response_text_widget.plain = accumulated_response_text # Update Text widget
                    # No need to call rich_layout["main"].update() again if response_text_widget is the Panel's renderable.
                    # However, Panel takes a renderable at init. So we might need to re-create the Panel or update its renderable.
                    # For simplicity and robustness with current Panel behavior:
                    rich_layout["main"].update(Panel(response_text_widget, title="LLM Response"))
                    screen.update(rich_layout) # Refresh screen with each new chunk

                # If generate_text stream=False was used, it would return the full string:
                # response_text = openai_api.generate_text(prompt_text, stream=False)
                # response_text_widget.plain = response_text if response_text else ""
                # rich_layout["main"].update(Panel(response_text_widget, title="LLM Response"))
                # screen.update(rich_layout)

                # Update status panel after streaming/generation is complete
                status_panel = Panel(Text(f"Status: Idle | LLM API: {api_endpoint} | Model: {model_name}"), title="Status")
                rich_layout["header"].update(status_panel)
                screen.update(rich_layout)

            except KeyboardInterrupt:
                continue # Allow Ctrl+C to clear the input line without exiting
            except EOFError:
                break # Allow Ctrl+D to exit


def main():
    parser = argparse.ArgumentParser(description="AI agent-terminal")
    parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("prompt", nargs="?", help="Prompt to send to the LLM")
    parser.add_argument("--stream", action="store_true", help="Enable streaming response")
    # Add other arguments as needed, e.g., for API endpoint, model selection
    parser.add_argument("--api-endpoint", default="http://127.0.0.1:12434", help="LLM API endpoint")
    parser.add_argument("--model", default="ai/gemma3:latest", help="LLM model name")


    args = parser.parse_args()

    if args.interactive:
        run_interactive_mode(args.api_endpoint, args.model)
    else:
        if not args.prompt:
            print("Error: Prompt is required when not in interactive mode.")
            parser.print_help()
            sys.exit(1)
            return # Ensure no further execution if prompt is missing

        print("AI agent-terminal!")
        # print("[AI] ------------------ parameters: ", len(sys.argv[1:]))
        # print(sys.argv[1:]) # This would print all args including -i etc.
        # print("[AI]---------------------------------")

        # prompt_text = filter_commands(sys.argv[1:]) # This needs to be adjusted for argparse
        # print("prompt ->", args.prompt)

        is_streamming = args.stream
        test_openai(args.prompt, is_streamming)
        # test_ollama(args.prompt,is_streamming)


if __name__ == "__main__":
    main()