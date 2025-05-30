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
    
def loadCve2025(cve_dir, fromDate):
    cve_dir_2025 = os.path.join(cve_dir, "cves", "2025")
    products = []
    cveCount=0

    print(f"Loading database from...{cve_dir_2025}")
    for root, dirnames, filenames in os.walk(cve_dir_2025):
        for filename in filenames:
            year, number = parse_cve_id(filename)
            #print(f""Filename: " {filename} Year: {year}, Number: {number}")
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
                                             x["product"].lower(), description)
                                    )
                except KeyError:
                    pass
                except TypeError:
                    pass
    #print(f"CVE Database from {fromDate} loaded")
    products_sorted = sorted(products, key=lambda product: product[1])
    print(f"CVEs from {fromDate} - CVE count: {cveCount}, Product count:  {str(len(products))}")  #22,061
    return products_sorted

def checkCve(cves, llm, retriever, prompts_text):
    cveqa_chain = create_qa_chain(llm, retriever, prompts_text, "cve_prompt")
    uniqueCve = list(set(cves))
    print("checkCve: 2025 CVE Product count: " + str(len(uniqueCve)))  #cves - 22,061, uniqueCves - 20717

    # This is the 1st run of questions to get a draft list of Impacted CVEs
    # Seeing lots of hullucinations in responses, and need to again run the
    # impactedCVEs list throught another round of questions to get a better list
    # Run 1
    impactedCVEs = []
    cnt = 1
    for cve in uniqueCve:
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
    #print(impactedCVEs)

    # Run 2


def cveLogic(cve_dir):
    print(f"Download CVE DB to {cve_dir}")
    download_github_repo(cveURL, cve_dir, True) # True means "git pull" to update
    fromDate = "2025-05-20T00:00:00.000Z"
    cves = loadCve2025(cve_dir, fromDate)  
    # We have a list of 22061 entries in a list of the format
    # print(f"CVEs: {cves[0]}")
    # Analyze the CVEs with the RAG github
    # checkCve(cves, llm, retriever, prompts_text)
