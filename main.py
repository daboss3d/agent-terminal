from lib.llm.ollama import  hello , query_ollama_stream
from lib.llm.test import  hello_test 

def main():
    print("Hello from agent-terminal!")
    hello_test()
    hello()
    txt = query_ollama_stream("http://10.1.1.62:11434/api/generate", "how to list directories ?")
    print(txt)


if __name__ == "__main__":
    main()
