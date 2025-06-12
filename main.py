
import sys
from lib.llm.ollama import query_ollama_stream, query_ollama 
from lib.llm.test import  hello_test 

from lib.ai import main as agent


def contains_substring(text : str, aList : list):
    for element in aList:
        if text in element:
            # print("--------------FOUND ",text," IN ",element)
            return True
    return False


def main():

    agent()
    return

    # print("[Main] ------------------ parameters: ", len(sys.argv[1:]))
    # print(sys.argv[1:])
    # print("[Main]---------------------------------")

    # args = sys.argv[1:]

    # if contains_substring("--stream",args):
    #     query_ollama_stream("http://10.1.1.62:11434/api/generate", "how to list directories ?")
    # else :
    #     txt = query_ollama("http://10.1.1.62:11434/api/generate", "how to list directories ?")
    #     print(txt)

    # print("Hello from agent-terminal!")
    # hello_test()
    # hello()
    # txt = query_ollama_stream("http://10.1.1.62:11434/api/generate", "how to list directories ?")
    # print(txt)


if __name__ == "__main__":
    main()
