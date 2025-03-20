import os
import sys
import json
import base64
import requests
from pathlib import Path
import keyring
import tkinter as tk
from tkinter import messagebox, simpledialog
import configparser
import time
from typing import List, Set

ASCII_LOGO = """
╔═══════════════════════════════════════════╗
║     🚀 Auto GitHub Uploader v1.0 🚀       ║
║         By Your Friendly AI 🤖            ║
╚═══════════════════════════════════════════╝
"""

DEFAULT_CONFIG = {
    'Repository': {
        'default_visibility': 'public',
        'always_use_default': 'no'
    },
    'Logging': {
        'show_detailed_logs': 'yes',
        'show_progress_bar': 'yes'
    },
    'Ignore': {
        'ignore_node_modules': 'yes',
        'use_gitignore': 'yes',
        'custom_ignores': '.env,.DS_Store,__pycache__,*.pyc'
    }
}

class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
        else:
            # Create default config
            for section, options in DEFAULT_CONFIG.items():
                if not self.config.has_section(section):
                    self.config.add_section(section)
                for key, value in options.items():
                    self.config.set(section, key, value)
            self.save_config()

    def save_config(self):
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)

    def get_value(self, section: str, key: str) -> str:
        return self.config.get(section, key)

    def set_value(self, section: str, key: str, value: str):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)
        self.save_config()

class GitHubUploader:
    def __init__(self):
        self.token = None
        self.config = Config()
        self.load_token()
        self.ignored_patterns: Set[str] = self.load_ignored_patterns()

    def load_ignored_patterns(self) -> Set[str]:
        patterns = set()
        
        # Add custom ignores
        custom_ignores = self.config.get_value('Ignore', 'custom_ignores').split(',')
        patterns.update(custom_ignores)

        # Add node_modules if configured
        if self.config.get_value('Ignore', 'ignore_node_modules') == 'yes':
            patterns.add('node_modules')

        # Add .gitignore patterns if configured
        if self.config.get_value('Ignore', 'use_gitignore') == 'yes':
            gitignore_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.gitignore')
            if os.path.exists(gitignore_path):
                with open(gitignore_path, 'r') as f:
                    patterns.update(line.strip() for line in f if line.strip() and not line.startswith('#'))

        return patterns

    def should_ignore_file(self, file_path: str) -> bool:
        for pattern in self.ignored_patterns:
            if pattern in file_path or pattern in Path(file_path).parts:
                return True
        return False

    def print_progress_bar(self, current: int, total: int, width: int = 40):
        if not self.config.get_value('Logging', 'show_progress_bar') == 'yes':
            return

        progress = current / total
        filled = int(width * progress)
        bar = '█' * filled + '░' * (width - filled)
        percent = int(progress * 100)
        print(f'\rProgress: |{bar}| {percent}% Complete', end='', flush=True)

    def load_token(self):
        try:
            self.token = keyring.get_password("github_uploader", "token")
            if self.token:
                headers = {
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                response = requests.get("https://api.github.com/user", headers=headers)
                if response.status_code == 200:
                    username = response.json()["login"]
                    print(f"✨ Logged in as: {username} ✨")
                else:
                    print("❌ GitHub token loaded but appears to be invalid.")
                    self.token = None
            else:
                print("ℹ️  No GitHub token found. Please run the script first to set up your token.")
        except Exception as e:
            print(f"❌ Error loading token: {e}")
            self.token = None

    def verify_token(self) -> bool:
        if not self.token:
            return False
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.get("https://api.github.com/user", headers=headers)
        return response.status_code == 200

    def get_username(self) -> str:
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.get("https://api.github.com/user", headers=headers)
        if response.status_code == 200:
            return response.json()["login"]
        raise Exception("Failed to get username from GitHub")

    def save_token(self, token: str) -> bool:
        try:
            keyring.set_password("github_uploader", "token", token)
            self.token = token
            return True
        except Exception as e:
            print(f"❌ Error saving token: {e}")
            return False

    def create_repo(self, repo_name: str) -> bool:
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Determine repository visibility
        is_private = True
        if self.config.get_value('Repository', 'always_use_default') == 'yes':
            is_private = self.config.get_value('Repository', 'default_visibility') == 'private'
        else:
            is_private = messagebox.askyesno("Repository Visibility", 
                                           f"Do you want the repository '{repo_name}' to be private?")

        data = {
            "name": repo_name,
            "auto_init": True,
            "private": is_private
        }

        response = requests.post("https://api.github.com/user/repos", headers=headers, json=data)
        
        if response.status_code == 201:
            print(f"✅ Successfully created repository: {repo_name} ({'private' if is_private else 'public'})")
            return True
        elif response.status_code == 422:
            error_msg = response.json().get('message', 'Unknown error')
            if "name already exists" in error_msg.lower():
                print(f"⚠️  Repository '{repo_name}' already exists. Please use a different name.")
            else:
                print(f"❌ Error creating repository: {error_msg}")
        else:
            print(f"❌ Error creating repository. Status code: {response.status_code}")
            try:
                error_details = response.json()
                print(f"❌ Error details: {error_details.get('message', 'No details available')}")
            except:
                print("Could not get detailed error information")
        return False

    def create_directory_structure(self, repo_name: str, username: str, path: str) -> bool:
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Create a dummy file to create the directory
        data = {
            "message": f"Create directory {path}",
            "content": base64.b64encode(b"").decode(),  # Empty content
        }

        url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{path}/.gitkeep"
        response = requests.put(url, headers=headers, json=data)
        return response.status_code in [201, 422]  # 422 means file already exists

    def upload_file(self, repo_name: str, username: str, file_path: Path, relative_path: Path) -> bool:
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        try:
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                print(f"\n⚠️  File {relative_path} is too large (>{file_size / 1024 / 1024:.1f}MB). Skipping...")
                return False

            with open(file_path, "rb") as f:
                content = base64.b64encode(f.read()).decode()
        except Exception as e:
            if self.config.get_value('Logging', 'show_detailed_logs') == 'yes':
                print(f"\n❌ Error reading file {file_path}: {e}")
            return False

        github_path = str(relative_path).replace(os.sep, '/')

        data = {
            "message": f"Upload {github_path}",
            "content": content
        }

        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{github_path}"
                response = requests.put(url, headers=headers, json=data)
                
                if response.status_code == 201:
                    return True
                elif response.status_code == 403 and "rate limit" in response.text.lower():
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                    wait_time = max(reset_time - time.time(), 0)
                    if wait_time > 0:
                        print(f"\n⏳ Rate limit reached. Waiting {int(wait_time)} seconds...")
                        time.sleep(wait_time + 1)
                        continue
                elif response.status_code != 201 and self.config.get_value('Logging', 'show_detailed_logs') == 'yes':
                    try:
                        error_msg = response.json().get('message', 'Unknown error')
                        print(f"\n❌ Error uploading {github_path}: {error_msg}")
                    except:
                        print(f"\n❌ Error uploading {github_path}: Status code {response.status_code}")
                
                if attempt < max_retries - 1:
                    print(f"\n🔄 Retrying upload of {github_path} in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                
            except Exception as e:
                print(f"\n❌ Network error while uploading {github_path}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
        
        return False

    def upload_folder(self, folder_path: str) -> bool:
        if not self.token:
            print("❌ No GitHub token found. Please run the script first to set up your token.")
            return False

        folder_path = Path(folder_path)
        repo_name = folder_path.name
        username = self.get_username()

        print(f"\n📁 Creating repository '{repo_name}'...")
        if not self.create_repo(repo_name):
            return False

        print("\n📤 Scanning files...")
        files_to_upload = []
        directories = set()
        
        for file_path in folder_path.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(folder_path)
                if not self.should_ignore_file(str(relative_path)):
                    # Add all parent directories to the set
                    parent = str(relative_path.parent).replace(os.sep, '/')
                    current = ""
                    for part in parent.split('/'):
                        if part:
                            current = f"{current}/{part}" if current else part
                            directories.add(current)
                    files_to_upload.append((file_path, relative_path))

        total_files = len(files_to_upload)
        if total_files == 0:
            print("⚠️  No files to upload after applying ignore patterns!")
            return False

        print(f"📦 Found {total_files} files to upload")
        
        # First create all directories
        if directories:
            print("\n📂 Creating directory structure...")
            for directory in sorted(directories):
                if directory != ".":
                    print(f"  Creating directory: {directory}")
                    self.create_directory_structure(repo_name, username, directory)
                    time.sleep(0.5)  # Add small delay between directory creations

        uploaded_files = 0

        # Sort files so that files in root directory are uploaded first
        files_to_upload.sort(key=lambda x: len(str(x[1]).split(os.sep)))
        
        print("\n📤 Uploading files...")
        for file_path, relative_path in files_to_upload:
            if self.config.get_value('Logging', 'show_detailed_logs') == 'yes':
                print(f"\n📄 Uploading: {relative_path}", end='', flush=True)
            
            if self.upload_file(repo_name, username, file_path, relative_path):
                if self.config.get_value('Logging', 'show_detailed_logs') == 'yes':
                    print(" ✅")
                uploaded_files += 1
            else:
                if self.config.get_value('Logging', 'show_detailed_logs') == 'yes':
                    print(" ❌")

            self.print_progress_bar(uploaded_files, total_files)
            time.sleep(0.5)  # Add small delay between file uploads

        print(f"\n\n📊 Upload Summary:")
        print(f"   • Total files: {total_files}")
        print(f"   • Successfully uploaded: {uploaded_files}")
        print(f"   • Failed: {total_files - uploaded_files}")
        
        repo_url = f"https://github.com/{username}/{repo_name}"
        print(f"\n🌟 Repository URL: {repo_url}")
        
        return uploaded_files == total_files

def setup_token():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    uploader = GitHubUploader()
    if uploader.verify_token():
        if messagebox.askyesno("Token Found", "A GitHub token is already saved. Would you like to update it?"):
            token = simpledialog.askstring("GitHub Token", "Please enter your new GitHub token:")
            if token:
                if uploader.save_token(token):
                    messagebox.showinfo("Success", "Token updated successfully!")
                else:
                    messagebox.showerror("Error", "Failed to update token!")
    else:
        token = simpledialog.askstring("GitHub Token", "Please enter your GitHub token:")
        if token:
            if uploader.save_token(token):
                messagebox.showinfo("Success", "Token saved successfully!")
            else:
                messagebox.showerror("Error", "Failed to save token!")
    root.destroy()

def show_config_menu():
    def print_menu():
        os.system('cls' if os.name == 'nt' else 'clear')
        print(ASCII_LOGO)
        print("\n🛠️  Configuration Menu:")
        print("1. Repository Settings")
        print("2. Logging Settings")
        print("3. Ignore Settings")
        print("4. GitHub Token Settings")
        print("5. Save and Exit")
        print("\n")

    config = Config()
    while True:
        print_menu()
        choice = input("Enter your choice (1-5): ")

        if choice == '1':
            print("\n📝 Repository Settings:")
            visibility = input("Default visibility (public/private) [current: " + 
                            config.get_value('Repository', 'default_visibility') + "]: ").lower()
            if visibility in ['public', 'private']:
                config.set_value('Repository', 'default_visibility', visibility)
            
            always_use = input("Always use default visibility (yes/no) [current: " + 
                             config.get_value('Repository', 'always_use_default') + "]: ").lower()
            if always_use in ['yes', 'no']:
                config.set_value('Repository', 'always_use_default', always_use)

        elif choice == '2':
            print("\n📊 Logging Settings:")
            detailed = input("Show detailed logs (yes/no) [current: " + 
                           config.get_value('Logging', 'show_detailed_logs') + "]: ").lower()
            if detailed in ['yes', 'no']:
                config.set_value('Logging', 'show_detailed_logs', detailed)

            progress = input("Show progress bar (yes/no) [current: " + 
                           config.get_value('Logging', 'show_progress_bar') + "]: ").lower()
            if progress in ['yes', 'no']:
                config.set_value('Logging', 'show_progress_bar', progress)

        elif choice == '3':
            print("\n🚫 Ignore Settings:")
            node = input("Ignore node_modules (yes/no) [current: " + 
                        config.get_value('Ignore', 'ignore_node_modules') + "]: ").lower()
            if node in ['yes', 'no']:
                config.set_value('Ignore', 'ignore_node_modules', node)

            gitignore = input("Use .gitignore (yes/no) [current: " + 
                            config.get_value('Ignore', 'use_gitignore') + "]: ").lower()
            if gitignore in ['yes', 'no']:
                config.set_value('Ignore', 'use_gitignore', gitignore)

            print("Current custom ignores: " + config.get_value('Ignore', 'custom_ignores'))
            custom = input("Enter custom ignores (comma-separated) or press Enter to keep current: ")
            if custom:
                config.set_value('Ignore', 'custom_ignores', custom)

        elif choice == '4':
            setup_token()

        elif choice == '5':
            print("\n✨ Configuration saved!")
            time.sleep(1)
            break

        input("\nPress Enter to continue...")

def main():
    if len(sys.argv) == 1:
        # No arguments provided, show configuration menu
        show_config_menu()
    else:
        # Handle drag and drop
        folder_path = sys.argv[1]
        if os.path.isdir(folder_path):
            print(ASCII_LOGO)
            uploader = GitHubUploader()
            if uploader.verify_token():
                if uploader.upload_folder(folder_path):
                    print("\n✨ Successfully uploaded folder to GitHub! ✨")
                else:
                    print("\n❌ Failed to upload folder to GitHub")
            else:
                print("\n❌ Invalid or expired GitHub token. Please run the script again to set up your token.")
        else:
            print("\n❌ Please provide a valid folder path")

if __name__ == "__main__":
    main() 