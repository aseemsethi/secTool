import os
import subprocess
import sys
import shutil

def download_github_repo(repo_url, destination_folder, forceDownload):
    #Check if repo exists
    cmd = "clone"
    
    # Check if the repository already exists
    if os.path.exists(destination_folder):
        if forceDownload == False:
            print(f"Repository already exists at {destination_folder}...Skipping download.")
            return
        print(f"Repository already exists at {destination_folder}...update with pull")

    if os.path.exists(destination_folder) and  "cve" in destination_folder:
        print(f"CVE filder exists...do a Git pull")
        cmd = "pull"

    # Ensure git is installed
    if not shutil.which("git"):
        print("Git is not installed. Please install Git and try again.")
        sys.exit(1)
    
    os.makedirs(destination_folder, exist_ok=True)
    
    # Construct the git clone command
    command1 = ["git", "config", "--global", "http.postBuffer", "157286400"]
    try:
        subprocess.run(command1, check=True)
    except:
        print(f"git increase buffer size for large CVE repo failed")

    # Construct the git clone or a pull command
    if cmd == "clone":
        command = ["git", cmd, repo_url, destination_folder]
    else:
        command = ["git", cmd, "origin", "main"]
    try:
        # Execute the git clone command
        subprocess.run(command, check=True)
        print(f"Repository cloned into {destination_folder}")
        #init_git_command = ["cd", destination_folder, "&&", "git", "init"]
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while cloning the repository: {e}")
        sys.exit(1)

#Clones a specific subdirectory from a Git repository.
def git_clone_subdirectory(repo_url, subdirectory, destination_path):
    try:
        os.makedirs(destination_path, exist_ok=True)
        # Clone the repository with no checkout
        subprocess.run(['git', 'clone', '--no-checkout', repo_url, destination_path], check=True)
        # Navigate into the repo
        os.chdir(destination_path)
        # Initialize sparse-checkout
        subprocess.run(['git', 'sparse-checkout', 'init', '--cone'], check=True)
        # Add the desired subdirectory to sparse-checkout
        subprocess.run(['git', 'sparse-checkout', 'add', subdirectory], check=True)
        # Checkout the specified subdirectory
        subprocess.run(['git', 'checkout'], check=True)
        print(f"Successfully cloned '{subdirectory}' from '{repo_url}' to '{destination_path}'")
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e}")