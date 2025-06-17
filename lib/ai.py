import argparse
# Removed Enum, sys, and some specific local imports that are no longer used directly in main
# from lib.llm.prompts import explain_terminal, explain_question # No longer used here
# from lib.utils.text import extract_quoted_text, remove_empty_or_whitespace_strings # No longer used here
# from lib.llm.basellm import BaseApiLLM # No longer used directly here

from lib.llm.openai import OpenAiApi
from lib.llm.ollama import OllamaApi
from lib.agent import BaseAgent


def main():
    print("AI agent-terminal!")

    parser = argparse.ArgumentParser(description="CLI AI Agent")
    parser.add_argument('prompt', nargs='?', default='', help='Main text prompt')
    parser.add_argument('-f', '--file', dest='filename', help='File path to prepend to the prompt')
    parser.add_argument('--stream', action='store_true', help='Enable streaming response')
    parser.add_argument('--api', type=str, default='ollama', choices=['ollama', 'openai'],
                        help='Select the AI API to use (ollama or openai)')

    parsed_args = parser.parse_args()

    # Print parsed arguments (optional, for debugging)
    # print("[AI] ------------------ parameters: ")
    # print(f"Prompt: {parsed_args.prompt}")
    # print(f"Filename: {parsed_args.filename}")
    # print(f"Stream: {parsed_args.stream}")
    # print(f"API: {parsed_args.api}")
    # print("[AI]---------------------------------")

    # Define LLM API configurations
    llm_configs = {
        "ollama": {"base_url": "http://10.1.1.62:11434", "model": "devstral:latest"},
        "openai": {"base_url": "http://127.0.0.1:12434", "model": "ai/gemma3:latest"}
    }

    # Create API instances
    try:
        ollama_api = OllamaApi(llm_configs["ollama"]["base_url"], llm_configs["ollama"]["model"])
        openai_api = OpenAiApi(llm_configs["openai"]["base_url"], llm_configs["openai"]["model"])
    except Exception as e:
        print(f"Error initializing LLM APIs: {e}")
        return

    available_llms = {
        "ollama": ollama_api,
        "openai": openai_api
    }

    # Instantiate the agent
    agent = BaseAgent(available_llms, default_api_name=parsed_args.api)
    if not agent.active_llm_api:
        print(f"Failed to activate API: {parsed_args.api}. Please check configurations.")
        return

    agent.set_active_api("openai")

    file_content = ""
    if parsed_args.filename:
        try:
            with open(parsed_args.filename, 'r') as f:
                file_content = f.read()
            print(f"--- Content from {parsed_args.filename} prepended to prompt ---")
        except FileNotFoundError:
            print(f"Error: File not found: {parsed_args.filename}")
        except IOError:
            print(f"Error: Could not read file: {parsed_args.filename}")

    final_prompt = parsed_args.prompt
    if file_content:
        if parsed_args.prompt: # Both file and direct prompt
            final_prompt = f"{file_content}\n\n{parsed_args.prompt}"
        else: # Only file content
            final_prompt = file_content

    # Ensure final_prompt is not just whitespace
    if not final_prompt.strip():
        if parsed_args.filename and not file_content: # File was specified but could not be read
            print("Prompt is empty and file could not be read or was empty.")
        else:
            print("Prompt is empty. Use -h for help or provide a prompt/file.")
        return

    print(f"\nUsing API: {agent.get_active_api_name()}")
    print(f"Sending prompt (length: {len(final_prompt)} chars)...")
    # For brevity, you might choose to print only a part of a very long prompt
    # print(f"Prompt content: \n{final_prompt[:200]}{'...' if len(final_prompt) > 200 else ''}\n")


    response = agent.generate_response(final_prompt, stream=parsed_args.stream)

    # If not streaming, and response is actual text (not None), print it.
    # If streaming, generate_response in BaseAgent handles printing chunks.
    # The current BaseAgent's generate_response returns the full string for non-streamed
    # and also for streamed (after printing chunks). So we only print if not streaming.
    if not parsed_args.stream and response:
        print(f"\nAI Response:\n{response}")

    agent.print_status()


if __name__ == "__main__":
    main()