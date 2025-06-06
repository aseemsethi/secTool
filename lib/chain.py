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

globalId = "1"
def update_retriever(db_path, docs, embeddings, collection_name="local-rag"):
    global globalId
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=60)
    splits = text_splitter.split_documents(docs)
    print(f"DB Path exists, {db_path}")
    vectorstore = Chroma(persist_directory=db_path, embedding_function=embeddings, 
                            collection_name=collection_name)
    vectorstore.add_documents(documents=splits, ids=[globalId])
    globalId = str(int(globalId)+1)
    retriever = vectorstore.as_retriever()
    print(f"Update Retriver: {retriever}")
    return retriever

def create_retriever(db_path, docs, embeddings, collection_name="local-rag"):
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

def create_qa_chain(llm, retriever, prompts_text, prompt_file):
    promptText = prompts_text[prompt_file]

    initial_prompt = PromptTemplate(
        template=promptText,
        input_variables=["question", "context"]
    )    

    chain = (
        RunnableParallel(context=retriever | format_docs, question = RunnablePassthrough()) |
        RunnableParallel(answer=initial_prompt | llm | retrieve_answer)
    )
    return chain