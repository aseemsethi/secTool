#
# Learnings from BellaBe github code
# Using python 3.10.17
#
import argparse
import os, shutil
import re
from dotenv import load_dotenv
from lib.tools import tools, tool_functions
from lib.webui import webui_func
from tests.llmTests import test_llm

from langchain.globals import set_debug, set_verbose
from lib.repository import download_github_repo
from lib.loader import load_files
from lib.chain import create_retriever, create_qa_chain
from lib.utils import read_prompt, load_LLM, select_model, load_embeddings
from lib.models import MODELS_MAP
from lib.checkCve import cveLogic

from langchain_core.messages import AIMessage
from langchain_core.messages import HumanMessage

# Tool Invocation demo
#  Chat query - python main.py --CVE CVE-2024-22414 --clean
#    what is the CVE from the cvecontext
#    is the vulnerability mentioned in the CVE in cveContext found in the code in the context?
#    what is the product in the cve from cveContext
#  Tool Calling: python main.py --CVE CVE-2024-22414 --clean --chat
#     what is 2 times 10
#  Loop run: python main.py  --clean
#
#  Repo is picked from .env or paramter, and made into a RAG
#  Enter data in .env file - date from which CVEs need to be checked, repo URL etc.
#   python main.py --repo_url https://github.com/aseemsethi/scraper.git   (for running in a loop)
# or 
#  Use Chat interface to invole for a single CVE.
#   python main.py --chat                (chst interface)
#   python main.py --chat --CVE CVE-2025-5000 (this enabled a chat with repo and CVE input)
#   python main.py                       (skips chat interface, and CVE tests are run)
#   python main.py --clean                (add this in every run, so that the DB is recreated)
#
#  Enter "quit" or "exit" in the Chat interface to quit.

set_verbose(True)

def chatInterface(llm, qa_chain):
    print("\nAsk a question.. 'exit' to quit...")
    while True:
        question = input("Question: ")
        if question.lower() == "exit" or question.lower() == "quit" :
            break
        answer = qa_chain.invoke(question)
        Q1 = [HumanMessage(question)]
        #print(f"Q1-1:  {Q1}")
        print(f"Answer: {answer}")

        try:
            if answer["answer"].tool_calls:
                Q1.append(answer['answer'])
                #print(f"Q1-2:  {Q1}")
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
                        print(f"Answer..........: {answer.content}")
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
    parser.add_argument("--clean", help="deletes DB", action="store_true")
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
        cve_pattern = re.compile(r'^CVE-\d{4}-\d{4,}$')
        if not cve_pattern.match(cveid.upper()):
            parser.error("Invalid CVE format. Expected format: CVE-YYYY-NNNNN")        

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
    if args.clean:
        if os.path.exists(db_dir) and os.path.isdir(db_dir):
            shutil.rmtree(db_dir)
            print(f"Deleted DB {db_dir}........................")
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
        "chat_prompt": read_prompt(os.path.join(prompt_templates_dir, 'chat_prompt.txt')),
        "cve_prompt": read_prompt(os.path.join(prompt_templates_dir, 'cve_prompt.txt'))
    }
    
    # Load LLM
    llm = load_LLM(model_name, tools)
    # test_llm(llm)

    # Load Embeddings
    embeddings = load_embeddings(model_name)
    #print(f"Embeddings: ", {embeddings})

    # Create Retriever - this makes a DB sqlite and puts all data there
    retriever = create_retriever(db_dir, document_chunks, embeddings)

    # Chat Function Interface
    if args.chat:
        print("Initiating Chat Interface")
        # Make a LangChain
        qa_chain = create_qa_chain(llm, retriever, prompts_text, "chat_prompt", "")
        chatInterface(llm, qa_chain)
    else:
        # Execute CVE Logic
        cveLogic(cve_dir, llm, retriever, prompts_text, cveid, db_dir, embeddings)

if __name__ == "__main__":
    main()