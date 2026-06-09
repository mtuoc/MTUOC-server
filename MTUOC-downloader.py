import os
import sys
import urllib.request
import argparse
import yaml
from huggingface_hub import snapshot_download

if sys.platform == 'darwin':
    import ssl
    try:
        # Intentem utilitzar el paquet de certificats oficial si està instal·lat
        import certifi
        ssl_context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        # Failsafe d'emergència si certifi no hi és: desactivem temporalment la verificació de context
        ssl_context = ssl._create_unverified_context()
    
    # Injectem el context de manera global a totes les crides d'urllib
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context)))
# -----------------------------------------------------

class RecipeDownloader:
    def __init__(self, recipe_path_or_url: str):
        self.target = recipe_path_or_url
        self.recipe = self.load_recipe()

    def load_recipe(self) -> dict:
        """
        Automatically detects if the target is a remote URL or a local file,
        then parses the YAML content.
        """
        # Check if the target is a remote URL
        if self.target.startswith("http://") or self.target.startswith("https://"):
            print(f"Remote recipe detected. Fetching from: {self.target}")
            try:
                req = urllib.request.Request(
                    self.target, 
                    headers={'User-Agent': 'Mozilla/5.0 (MTUOC Recipe Downloader)'}
                )
                with urllib.request.urlopen(req) as response:
                    return yaml.safe_load(response.read().decode('utf-8'))
            except Exception as e:
                print(f"Critical error downloading remote recipe: {e}")
                sys.exit(1)
        
        # Otherwise, handle it as a local file
        else:
            print(f"Local recipe detected. Reading file: {self.target}")
            if not os.path.exists(self.target):
                print(f"Error: Local recipe file '{self.target}' does not exist.")
                sys.exit(1)
            try:
                with open(self.target, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"Critical error reading or parsing local YAML recipe: {e}")
                sys.exit(1)

    def download_item(self, url: str, target_dir: str):
        """
        Determines if the URL is a direct file or a Hugging Face repo,
        and downloads it to the target directory.
        """
        # Ensure the directory exists
        os.makedirs(target_dir, exist_ok=True)

        # Case A: Direct file download (HTTP/HTTPS URL)
        if url.startswith("http://") or url.startswith("https://"):
            filename = url.split("/")[-1]
            destination_path = os.path.join(target_dir, filename)
            print(f"Downloading file from URL: {url} -> {destination_path}")
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(destination_path, 'wb') as out_file:
                out_file.write(response.read())
            print(f"✔ File [{filename}] downloaded successfully.")

        # Case B: Hugging Face Repository snapshot download
        else:
            print(f"Downloading Hugging Face repository snapshot: {url} -> {target_dir}")
            snapshot_download(
                repo_id=url,
                local_dir=target_dir
            )
            print(f"✔ Repository [{url}] downloaded successfully.")

    def run(self):
        """Processes the unlimited list of downloads defined in the recipe."""
        model_name = self.recipe.get("model_name", "unnamed_model")
        description = self.recipe.get("model_description", "No description provided.")
        download_list = self.recipe.get("Download", [])

        print(f"==================================================")
        print(f"STARTING RECIPE: {model_name}")
        print(f"Description: {description}")
        print(f"==================================================")

        if not download_list:
            print("⚠ Warning: 'Download' list is empty or missing in the recipe.")
            return

        for item in download_list:
            item_id = item.get("id", "?")
            url = item.get("url")
            sub_dir = item.get("subdirectory", ".").strip()
            is_optional = item.get("optional", False)

            if not url:
                print(f"⚠ Skipping item ID {item_id}: Missing 'url' field.")
                continue

            # Resolve the subdirectory path relative to the current working directory
            local_path = os.path.abspath(sub_dir)

            print(f"Processing item [{item_id}]...")

            try:
                self.download_item(url, local_path)
            except Exception as e:
                if is_optional:
                    print(f"Optional item [{item_id}] failed. Skipping... Error: {e}")
                else:
                    print(f"CRITICAL ERROR: Required item [{item_id}] failed to download.")
                    raise e

        print(f"==================================================")
        print(f"RECIPE '{model_name}' COMPLETED SUCCESSFULLY")
        print(f"==================================================")


if __name__ == "__main__":
    # Initialize the argument parser with a description in English
    parser = argparse.ArgumentParser(
        description="MTUOC Recipe Downloader: Download models and configuration files from local or remote YAML recipes."
    )
    
    # Define the recipe argument (can be a local path or a remote URL)
    parser.add_argument(
        "recipe",
        type=str,
        help="Path to a local YAML recipe file OR a remote raw YAML URL (e.g., from GitHub or Hugging Face)."
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # Initialize the downloader with the parsed recipe argument and run it
    downloader = RecipeDownloader(args.recipe)
    downloader.run()
