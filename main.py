#
# Learnings from BellaBe github code
#
import streamlit as st
import argparse
import os
from dotenv import load_dotenv

from langchain.globals import set_debug, set_verbose
from lib.repository import download_github_repo
from lib.loader import load_files
from lib.chain import create_retriever, create_qa_chain
from lib.utils import read_prompt, load_LLM, select_model
from lib.models import MODELS_MAP

set_verbose(True)
load_dotenv()

def main():
    print("\nSectool........", flush=True)
    #Parse command line args
    # args - github URL that we would like to check
    parser = argparse.ArgumentParser(description="GitHub Repo QA CLI Application")
    parser.add_argument("repo_url", type=str, help="URL of GitHub repo")
    args = parser.parse_args()
    print(f"Github URL : {args.repo_url}")

    # Prompt the user to select a model
    # Our models are locally behind ollama. Run ollama run <model>
    # to run the models and access using REST API
    model_name = select_model()
    model_info = MODELS_MAP[model_name]

    # Extract the repo name from the GitHub URL passed as params
    repo_name = args.repo_url.split("/")[-1].replace(".git","")
    print(f"repo_name: {repo_name}")


    # We have data/ in the .ignore files, so these downloads do not get committed.
    # Get path to data folder from URL https://github.com/aseemsethi/scraper.git
    base_dir = os.path.dirname(os.path.abspath(__file__))
    #/Users/aseemsethi/aseem/secTool
    repo_dir = os.path.join(base_dir, "data", repo_name) 
    # /Users/aseemsethi/aseem/secTool/data/scraper
    db_dir = os.path.join(base_dir, "data", "db") 
    # /Users/aseemsethi/aseem/secTool/data/db
    print (repo_dir, db_dir)
    prompt_templates_dir = os.path.join(base_dir, "prompt_templates")
    #/Users/aseemsethi/aseem/secTool/prompt_templates

    # Download the github repo
    print(f"Downloading repo from {args.repo_url}")
    download_github_repo(args.repo_url, repo_dir)

    # Load Docs into Loader
    print(f"Loading Docs into GenericLoader")
    document_chunks = load_files(repository_path=repo_dir)
    print(f"Created chunks len is: {len(document_chunks)}")

    # Load prompt templates
    prompts_text = {
        "initial_prompt": read_prompt(os.path.join(prompt_templates_dir, 'initial_prompt.txt')),
        "evaluation_prompt": read_prompt(os.path.join(prompt_templates_dir, 'evaluation_prompt.txt')),
        "evaluation_with_context_prompt": read_prompt(os.path.join(prompt_templates_dir, 'evaluation_with_context_prompt.txt'))
    }
    print(f"\nInitial Prompt Loaded: {prompts_text["initial_prompt"]}")
    print(f"Eval Prompt Loaded: {prompts_text["evaluation_prompt"]}")
    print(f"Eval Prompt w/Context Loaded: {prompts_text["evaluation_with_context_prompt"]}")

if __name__ == "__main__":
    main()