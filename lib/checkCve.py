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
from lib.repository import download_github_repo
from lib.chain import create_qa_chain
from dotenv import load_dotenv

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


def checkCveforX(cves, llm, retriever, prompts_text):
    cveqa_chain = create_qa_chain(llm, retriever, prompts_text, "cve_prompt")
    # Run 2


def cveLogic(cve_dir, llm, retriever, prompts_text):
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
    checkCveforX(impactedCVEs, llm, retriever, prompts_text)

