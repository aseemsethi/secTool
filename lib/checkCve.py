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

from lib.repository import download_github_repo

cveURL = "https://github.com/CVEProject/cvelistV5.git"
def checkCve(cve_dir):
    print(f"Checking CVE DB...")
    download_github_repo(cveURL, cve_dir, True)




