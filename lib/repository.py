import os
import subprocess
import sys
import shutil

def download_github_repo(repo_url, destination_foler):
    #Check if repo exists
    print("Download Github repo..")
    