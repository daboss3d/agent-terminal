import sys
from enum import Enum



# from lib.llm.ollama import  hello , query_ollama_stream,list_ollama_models
# from lib.llm import ollama
# from lib.llm.test import  hello_test  
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
    openai_api.generate_text(prompt,stream=True)


def test_ollama(prompt: str, stream: bool = True):
    
    ollama_api = OllamaApi("http://10.1.1.62:11434","devstral:latest")
    # ollama_api.print_model()
    print("Models ->",ollama_api.list_models())
    txt = ollama_api.generate_text(prompt, stream)


def main():
    print("AI agent-terminal!")

    # test_openai("print some gamming emojis")
 

    args = sys.argv[1:]
    print("[AI] ------------------ parameters: ", len(sys.argv[1:]))
    print(args)
    print("[AI]---------------------------------")

    prompt = filter_commands(args)
    print("promt ->",prompt[0])

    is_streamming = contains_substring("--stream",args)

    # test_openai(prompt[0],is_streamming)
    test_ollama(prompt,is_streamming)



if __name__ == "__main__":
    main()