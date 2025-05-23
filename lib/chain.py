import os
from operator import itemgetter

from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import PromptTemplate

from lib.models import MODELS_MAP
from lib.utils import format_docs, retrieve_answer, load_embeddings
from lib.entities import LLMEvalResult

def create_retriever(llm_name, db_path, docs, embeddings, collection_name="local-rag"):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=60)


def create_qa_chain(llm, retriever, prompts_text):
    initial_prompt_text = prompts_text["initial_prompt"]
    