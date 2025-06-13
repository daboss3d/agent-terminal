import sys
import argparse
from enum import Enum

 
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
            # print("--------------FOUND ",text," IN ",element)
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



def main():
    print("AI agent-terminal!")

    parser = argparse.ArgumentParser()
    parser.add_argument('prompt', nargs='?', default='', help='Main text prompt')
    parser.add_argument('-f', '--file', dest='filename', help='File path')
    parser.add_argument('--stream', action='store_true', help='Enable streaming')

    parsed_args = parser.parse_args()

    print("[AI] ------------------ parameters: ")
    print(f"Prompt: {parsed_args.prompt}")
    print(f"Filename: {parsed_args.filename}")
    print(f"Stream: {parsed_args.stream}")
    print("[AI]---------------------------------")

    file_content = ""
    if parsed_args.filename:
        try:
            with open(parsed_args.filename, 'r') as f:
                file_content = f.read()
        except FileNotFoundError:
            print(f"Error: File not found: {parsed_args.filename}")
        except IOError:
            print(f"Error: Could not read file: {parsed_args.filename}")

    final_prompt = parsed_args.prompt
    if file_content:
        if parsed_args.prompt:
            final_prompt = f"{file_content}\n\n{parsed_args.prompt}"
        else:
            final_prompt = file_content

    if final_prompt:
        test_openai(final_prompt, parsed_args.stream)
    elif parsed_args.filename: # File was specified but couldn't be read, and no prompt was given
        print(f"Proceeding without content from {parsed_args.filename} due to read error and no other prompt provided.")
    else: # No prompt and no file specified
        print("No prompt or file provided. Use -h for help.")

    # test_ollama(final_prompt, parsed_args.stream)



if __name__ == "__main__":
    main()