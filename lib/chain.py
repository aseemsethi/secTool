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
    splits = text_splitter.split_documents(docs)
    #print(f"Splits: {splits} embeddings: {embeddings}")
    if not os.path.exists(db_path):
        print(f"DB Path not exist, {db_path}")
        vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, 
                            persist_directory=db_path, collection_name=collection_name)
    else:
        print(f"DB Path exists, {db_path}")
        vectorstore = Chroma(persist_directory=db_path, embedding_function=embeddings, 
                             collection_name=collection_name)
    retriever = vectorstore.as_retriever()
    #print(vectorstore.similarity_search("patent"))
    #print(vectorstore.get()['documents'])
    print(f"Retriver: {retriever}")
    return retriever

def create_qa_chain(llm, retriever, prompts_text):
    initial_prompt_text = prompts_text["initial_prompt"]
    qa_eval_prompt_text = prompts_text["evaluation_prompt"]
    qa_eval_prompt_with_context_text = prompts_text["evaluation_with_context_prompt"]

    initial_prompt = PromptTemplate(
        template=initial_prompt_text,
        input_variables=["question", "context"]
    )    
    json_parser = JsonOutputParser(pydantic_object=LLMEvalResult)

    qa_eval_prompt = PromptTemplate(
        template=qa_eval_prompt_text,
        input_variables=["question", "context"],
        partial_variables={"format_instructions":json_parser.get_format_instructions()}
    )

    qa_eval_prompt_with_context = PromptTemplate(
        template=qa_eval_prompt_text,
        input_variables=["question","answer","context"],
        partial_variables={"format_instructions": json_parser.get_format_instructions()},
    )

    chain = (
        RunnableParallel(context=retriever | format_docs, question = RunnablePassthrough()) |
        RunnableParallel(answer=initial_prompt | llm | retrieve_answer)
    )
    return chain

def create_cveqa_chain(llm, retriever, prompts_text):
    cve_prompt_text = prompts_text["cve_prompt"]

    cve_prompt = PromptTemplate(
        template=cve_prompt_text,
        input_variables=["question", "context"]
    )    
    chain = (
        RunnableParallel(context=retriever | format_docs, question = RunnablePassthrough()) |
        RunnableParallel(answer=cve_prompt | llm | retrieve_answer)
    )
    return chain