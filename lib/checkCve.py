'''
CVSS Score - The Exploitability and Impact metrics produce sub-scores that are used 
to calculate the Base Score, which ranges from 0 to 10, with 10 being most severe. 
The Base Score represents the intrinsic qualities of a vulnerability that are constant 
over time and across environments.

CVSS is not a measure of risk. Its a measure of Severity. CVSS is from first.org - 
"The Forum of Incident Response and Security Teams"

Download CVEs in JSON 5.1.1 format from 
https://github.com/CVEProject/cvelistV5/tree/main/cves
CVE numbering scheme: CVE-YYYY-NNNN, where YYYY is the year and NNNN is a unique 
sequence number. This means that CVEs assigned in 2025 will follow format CVE-2025-XXXX

Logic:
Loop over all Critical/High CVEs (use metrics:cvss3_1:baseSeverity)
  For each CVE, extract affected:product field in CVE's JSON field
  Search affected:product field using the RAG LLM
  If product found, raise new field fix-priority
'''

import os, re, json
from langchain_chroma import Chroma
from lib.repository import download_github_repo
from lib.chain import create_qa_chain
from dotenv import load_dotenv
import requests
from lib.chain import update_retriever, create_retriever
from langchain_community.document_loaders.generic import GenericLoader
from langchain_core.messages import HumanMessage
from langchain_text_splitters import RecursiveJsonSplitter
from langchain_core.documents import Document
from lib.loader import load_files
from langchain_text_splitters import RecursiveCharacterTextSplitter

cveURL = "https://github.com/CVEProject/cvelistV5.git"

def parse_cve_id(cve):
    pattern = pattern = r"CVE-(\d{4})-(\d+)\.json"
    match = re.match(pattern, cve)
    if match:
        year = match.group(1)
        number = match.group(2)
        return year, number
    else:
        return None, None
    
def loadCve2025(cve_dir, fromDate, fromSev):
    cve_dir_2025 = os.path.join(cve_dir, "cves", "2025")
    products = []
    cveCount=0
    zeroScore=0
    ignoreSev=0

    print(f"Loading database from...{cve_dir_2025}")
    for root, dirnames, filenames in os.walk(cve_dir_2025):
        for filename in filenames:
            year, number = parse_cve_id(filename)
            #print(f"Filename: {filename} Year: {year}, Number: {number}")
            with open(os.path.join(root, filename)) as f:
                data = json.load(f)
                try:
                    datePublished = data.get('cveMetadata', {}).get(
                        'datePublished', {})
                    #print(f"Date pub: {datePublished}")
                    if fromDate < datePublished:
                        cveCount = cveCount+1
                    else:
                        continue
                    #v3.1: Critical 9-10, High 7 - 8.9, Med - 4 - 6.9, Low - .1 to 3.9
                    basescore = data.get('containers', {}).get(
                        'cna', {}).get('metrics',[{}])[0].get('cvssV4_0', {}).get(
                            'baseScore', {})
                    #print(f"V4.0 BaseScore: {basescore}")
                    if not basescore:
                        basescore = data.get('containers', {}).get(
                        'cna', {}).get('metrics',[{}])[0].get('cvssV3_1', {}).get(
                            'baseScore', {})
                        #print(f"V3.1 BaseScore: {basescore}")
                    if not basescore:
                        # is there is no basescore, we will skip this
                        # print(f"Base score is 0 for: {filename}")
                        zeroScore = zeroScore + 1
                        continue
                    if basescore < fromSev:
                        ignoreSev = ignoreSev +1
                        continue
                    description = data.get('containers', {}).get(
                        'cna', {}).get('descriptions', [{}])[0].get('value', 'N/A')
                    if "containers" in data:
                        if "cna" in data["containers"]:
                            if "affected" in data["containers"]["cna"]:
                                for x in data["containers"]["cna"]["affected"]:
                                    if x["product"] != "n/a" and fromDate < datePublished:
                                        #print(filename.split('.',1)[0])
                                        products.append(
                                            (filename.split('.',1)[0], 
                                             x["product"].lower(), description, basescore)
                                    )
                except KeyError:
                    pass
                except TypeError:
                    pass
    #print(f"CVE Database from {fromDate} loaded")
    # Total Product CVEs are more, since multiple products could be impacted in 1 CVE
    products_sorted = sorted(products, key=lambda product: product[1])
    print(f"CVEs from {fromDate} - Total CVEs: {cveCount}, "
          f"ZeroSev: {zeroScore}, IgnoreSev < fromSev: {ignoreSev}, "
          f"\nFinal CVE Count:  {str(len(products))}\n")  #22,061
    return products_sorted

def loadCve(cve_dir, cveid):
    products = []
    year = cveid.split('-')[1]
    cve_dir_year = os.path.join(cve_dir, "cves", year)
    cveid_filename = cveid+'.json'
    print(f"Searching {cveid_filename} in DB from...{cve_dir_year}")
    for root, dirnames, filenames in os.walk(cve_dir_year):
        for filename in filenames:
            #print(f"Filename: {filename} {cveid+'.json'}")
            if filename == cveid_filename:
                print(f"CVE found in DB: {filename}")
            else:
                continue     
            with open(os.path.join(root, filename)) as f:
                data = json.load(f)
                try:
                    datePublished = data.get('cveMetadata', {}).get(
                        'datePublished', {})
                    basescore = data.get('containers', {}).get(
                        'cna', {}).get('metrics',[{}])[0].get('cvssV4_0', {}).get(
                            'baseScore', {})
                    #print(f"V4.0 BaseScore: {basescore}")
                    if not basescore:
                        basescore = data.get('containers', {}).get(
                        'cna', {}).get('metrics',[{}])[0].get('cvssV3_1', {}).get(
                            'baseScore', {})
                    description = data.get('containers', {}).get(
                        'cna', {}).get('descriptions', [{}])[0].get('value', 'N/A')
                    if "containers" in data:
                        if "cna" in data["containers"]:
                            if "affected" in data["containers"]["cna"]:
                                for x in data["containers"]["cna"]["affected"]:
                                    if x["product"] != "n/a":
                                        #print(filename.split('.',1)[0])
                                        products.append(
                                            (filename.split('.',1)[0], 
                                             x["product"].lower(), description, basescore)
                                    )
                except KeyError:
                    pass
                except TypeError:
                    pass
    products_sorted = sorted(products, key=lambda product: product[1])
    return data, products_sorted


def checkCveforProduct(cves, llm, retriever, prompts_text):
    cveqa_chain = create_qa_chain(llm, retriever, prompts_text, "cve_prompt")

    # This is the 1st run of questions to get a draft list of Impacted CVEs
    impactedCVEs = []
    cnt = 1
    for cve in cves:
        cnt = cnt+1
        if cnt % 20 == 0 :
            print(f"{cnt} with {len(impactedCVEs)} positives")
            print(impactedCVEs)
        question = "Does this code use " + cve[1] + " product ?"
        print(question)
        answer = cveqa_chain.invoke(question)
        if "Yes" in answer['answer']:
            impactedCVEs.append((cve, "Yes"))
            print(f"Answer: {answer}")

    print(f"Number of CVEs affecting the code {len(impactedCVEs)}")
    return impactedCVEs

# what is the cveId in the cveContext
def cveChecker(cve_dir, cveid, db_dir, embeddings, llm, prompts_text):
    # data is dict type
    data, products = loadCve(cve_dir, cveid)
    print(f"Products impacted:  {str(len(products))}")
    for product in products:
        print(f"Product: {product[1]}, BaseScore: {product[3]}")
    # Load Document
    vectorstore = Chroma(persist_directory=db_dir, embedding_function=embeddings, 
                             collection_name="local-rag")
    retriever = vectorstore.as_retriever()
    qa_chain = create_qa_chain(llm, retriever, prompts_text, "chat_prompt", data)
    print("\nAsk a question.. 'exit' to quit...")
    while True:
        question = input("Question: ")
        if question.lower() == "exit" or question.lower() == "quit" :
            break
        answer = qa_chain.invoke(question)
        Q1 = [HumanMessage(question)]
        print(f"Answer: {answer}")

def cveLogic(cve_dir, llm, retriever, prompts_text, cveid, db_dir, embeddings):
    if cveid != "":
        print("-----------------------")
        print(f"Return info on 1 CVEID only")
        cveChecker(cve_dir, cveid, db_dir, embeddings, llm, prompts_text)
        return
    
    print(f"Download CVE DB to {cve_dir}")
    download_github_repo(cveURL, cve_dir, True) # True means "git pull" to update
    #fromDate = "2025-05-20T00:00:00.000Z"
    fromDate = os.getenv('fromDate')
    fromSev = int(os.getenv('fromSev'))
    print(f"fromDate, fromSev from env: {fromDate, fromSev} ..............")
    cves = loadCve2025(cve_dir, fromDate, fromSev)  
    # We have a list of 22061 entries in a list of the format
    # print(f"CVEs: {cves[0]}")
    # Analyze the CVEs for Product with the RAG github
    impactedCVEs = checkCveforProduct(cves, llm, retriever, prompts_text)
    # Analyze the impacted CVEs

