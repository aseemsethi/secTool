import os
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import Language

def load_files_old(repository_path):
    loader = GenericLoader.from_filesystem(
        repository_path,
        glob="**/*",
        suffixes=[".go"],
        parser=LanguageParser(
            language=Language.GO
        )
    )
    docs = loader.load()
    
    loader = GenericLoader.from_filesystem(
        repository_path,
        glob="**/*",
        suffixes=[".py"],
        parser=LanguageParser(
            language=Language.PYTHON
        )
    )
    docs.extend(loader.load())
    return docs

def load_files(repository_path):
    loader = GenericLoader.from_filesystem(
        repository_path,
        glob="**/*",
        suffixes=[".go", ".py", ".json"],
        parser=LanguageParser()
    )
    docs = loader.load()
    return docs