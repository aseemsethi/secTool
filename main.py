#
# Learnings from BellaBe github code
# Using python 3.10.17
#
import streamlit as st
import argparse
import os
from dotenv import load_dotenv

from langchain.globals import set_debug, set_verbose
from lib.repository import download_github_repo
from lib.loader import load_files
from lib.chain import create_retriever, create_qa_chain
from lib.utils import read_prompt, load_LLM, select_model, load_embeddings
from lib.models import MODELS_MAP
from lib.checkCve import cveLogic

from langchain.prompts import PromptTemplate  #test
from langchain.chains.llm import LLMChain #test
from langchain_core.tools import tool
from langchain_core.messages import AIMessage
from langchain_core.messages import HumanMessage

# invoke with URL to run CVE check on the repo
#   Repo is picked from .env or paramter, and made into a RAG
#   python main.py --repo_url https://github.com/aseemsethi/scraper.git
# or 
#   Repo is picked from .env or paramter, and made into a RAG
#   python main.py --chat                (chst interface)
#   python main.py --chat --CVE CVE-1234 (this enabled a chat with repo and CVE input)
#   python main.py                       (skips chat interface, and CVE tests are run)

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers.
    Args:
        a: first int
        b: second int
    """
    print(f"Tool called..multiply {a} and {b}")
    return (a * b)

@tool
def divide(a: int, b: int) -> int:
    """Divide two numbers."""
    print(f"Tool called..divide {a} by {b}")
    return a / b

@tool
def HowIsWeather() -> str:
    """Get the Weather."""
    print(f"Tool called..Weather")
    return "Good Weather"

tools = [multiply, divide, HowIsWeather]
tool_functions = {
    "multiply": multiply,
    "divide": divide,
    "HowIsWeather": HowIsWeather,
}

set_verbose(True)

@st.fragment(run_every=None)
def webui_func(qa_chain):
    st.write("This is inside of a fragment!")
    st.title("CVE Check")
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    st.caption("A Streamlit powered chatbot powered by Ollama")
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])
    if prompt := st.chat_input("What is the code written in"):
        print("..............")
        answer = qa_chain.invoke(prompt)
        #print(f"Answer: {answer}")
        st.chat_message("assistant").write(answer)

def chatInterface(llm, qa_chain):
    print("\nAsk a question.. 'exit' to quit...")
    while True:
        question = input("Question: ")
        if question.lower() == "exit":
            break
        answer = qa_chain.invoke(question)
        Q1 = [HumanMessage(question)]
        #print(f"Q1-1:  {Q1}")
        print(f"Answer: {answer}")

        try:
            if answer["answer"].tool_calls:
                Q1.append(answer['answer'])
                print(f"Q1-2:  {Q1}")
                for tool in answer["answer"].tool_calls:
                    print(f"tool call for = {tool}")
                    if function_to_call := tool_functions.get(tool["name"]):
                        print('Calling function:', tool["name"])
                        print('Arguments:', tool["args"])
                        output = function_to_call.invoke(tool)
                        Q1.append(output)
                        print('Function output:', output)
                        print(f"Q1-3:  {Q1}")
                        answer = llm.invoke(Q1)
                        print(f"Answer-: {answer.content}")
                    else:
                        print('Function', tool["name"], 'not found')
        except:
            print(f"No tool calls made..")

def main():
    print("\nSectool........", flush=True)
    #Parse command line args
    # args - github URL that we would like to check
    parser = argparse.ArgumentParser(description="GitHub Repo Security Application")
    parser.add_argument("--repo_url", type=str, help="URL of GitHub repo", default="")
    parser.add_argument("--CVE", type=str, help="CVE ID as CVE-xxxx", default="")
    # If action param is used, --chat is a flag and needs no value
    parser.add_argument("--chat", help="provides a chat interface", action="store_true")
    args = parser.parse_args()
    print(f"Github URL : {args.repo_url}")
    repo_url = args.repo_url

    load_dotenv()
    ##### Repo URL #####
    if (args.repo_url == ""):
        repo_url = os.getenv('GITHUB_URL')
        print(f"Repo name null, picking from env - {repo_url}")
    # Extract the repo name from the GitHub URL passed as params
    repo_name = repo_url.split("/")[-1].replace(".git","")
    print(f"repo_name: {repo_name}")
    ##### CVE ID #####
    cveid = args.CVE
    if cveid == "":
        print(f"No CVE ID given")
    else:
        print (f"CVE ID: {cveid}")


    # Prompt the user to select a model
    # Our models are locally behind ollama. Run ollama run <model>
    # to run the models and access using REST API
    model_name = select_model()
    selection = MODELS_MAP[model_name]["name"]
    print(f"Model selected: {selection}")

    # We have data/ in the .ignore files, so these downloads do not get committed.
    # Get path to data folder from URL https://github.com/aseemsethi/scraper.git
    base_dir = os.path.dirname(os.path.abspath(__file__))
    #/Users/aseemsethi/aseem/secTool
    repo_dir = os.path.join(base_dir, "data", repo_name) 
    # /Users/aseemsethi/aseem/secTool/data/scraper
    db_dir = os.path.join(base_dir, "data", "db")
    cve_dir = os.path.join(base_dir, "data", "cve") 
    # /Users/aseemsethi/aseem/secTool/data/db
    print (repo_dir, db_dir, cve_dir)
    prompt_templates_dir = os.path.join(base_dir, "prompt_templates")
    #/Users/aseemsethi/aseem/secTool/prompt_templates

    # Download the github repo
    print(f"Downloading repo from {repo_url}")
    download_github_repo(repo_url, repo_dir, False)

    # Load Docs into Loader
    print(f"Loading Docs into GenericLoader")
    document_chunks = load_files(repository_path=repo_dir)
    print(f"Created chunks len is: {len(document_chunks)}")

    # Load prompt templates
    prompts_text = {
        "initial_prompt": read_prompt(os.path.join(prompt_templates_dir, 'initial_prompt.txt')),
        "cve_prompt": read_prompt(os.path.join(prompt_templates_dir, 'cve_prompt.txt'))
    }
    
    # Load LLM
    llm = load_LLM(model_name, tools)

    # Run a test to see if everything working ok
    # print(llm.invoke("Tell me a joke"))
    # prompt = PromptTemplate.from_template("Give {number} names for a {domain} startup?")
    # chain = LLMChain(llm=llm, prompt=prompt)
    # print(chain.invoke({'number': 2, 'domain': 'Medical'}))
    print("-----------------------")

    # Load Embeddings
    embeddings = load_embeddings(model_name)
    #print(f"Embeddings: ", {embeddings})

    # Create Retriever - this makes a DB sqlite and puts all data there
    retriever = create_retriever(model_name, db_dir, document_chunks, embeddings)

    # The following call was to test Streamlit UI
    #webui_func(qa_chain)

    # Chat Function Interface
    if args.chat:
        print("Initiating Chat Interface")
        # Make a LangChain
        qa_chain = create_qa_chain(llm, retriever, prompts_text, "initial_prompt")
        chatInterface(llm, qa_chain)
    else:
        # Execute CVE Logic
        cveLogic(cve_dir, llm, retriever, prompts_text, cveid)

if __name__ == "__main__":
    main()