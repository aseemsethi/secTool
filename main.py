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
    print("Sectool...", flush=True)
    #prompt the user to select a model
    model_name = select_model()
    model_info = MODELS_MAP[model_name]
    
if __name__ == "__main__":
    main()