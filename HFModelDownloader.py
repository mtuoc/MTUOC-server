import os
import shutil
from typing import List, Optional
from huggingface_hub import snapshot_download
#from MTUOC_misc import printLOG

def printLOG(a,b="",c=""):
    print(a,b,c)

class HFModelDownloader:
    def __init__(self, repo_id: str, list_file_name: str = "filestomove.txt"):
        self.repo_id = repo_id
        self.list_file_name = list_file_name
        
        # 1. Determinar el nom del subdirectori (MODEL_SUBDIR)
        try:
            self.model_subdir = self.repo_id.split('/')[-1]
        except IndexError:
            self.model_subdir = self.repo_id.replace('/', '_')
            printLOG(1,f"Format of repo not valid '{self.model_subdir}' as a subfolder.")

        # 2. Determinar el directori arrel (ROOT_DIR) i local_dir
        self.root_dir = os.getcwd()
        self.local_dir = os.path.join(self.root_dir, self.model_subdir)
        self.destination_root = self.root_dir
        
        # S'ha d'assegurar la carpeta de descàrrega, però es farà dins de download_model 
        # només si la descàrrega es duu a terme.

    def download_model(self):
        if os.path.exists(self.local_dir) and os.path.isdir(self.local_dir):
            printLOG(1,"Model directory already exists.")            
            return self.local_dir
        printLOG(1,"Downloading model")
        # Assegura't que la carpeta de descàrrega existeix abans d'intentar descarregar-hi
        os.makedirs(self.local_dir, exist_ok=True)
        
        try:
            snapshot_download(
                repo_id=self.repo_id,
                local_dir=self.local_dir,
                local_dir_use_symlinks=False,
                tqdm_class=None
            )            
            return self.local_dir
        except Exception as e:
            printLOG(1, f"Error downloading model: {e}")
            
            if os.path.exists(self.local_dir):
                 shutil.rmtree(self.local_dir)            
            return None

    def _get_files_to_move(self) -> Optional[List[str]]:
        list_file_path = os.path.join(self.local_dir, self.list_file_name)
        
        if not os.path.exists(list_file_path):
            return None

        
        try:
            with open(list_file_path, 'r', encoding='utf-8') as f:
                files = [line.strip() for line in f if line.strip()]
            return files
        except Exception as e:
            print(f"error reading files to move file: {self.list_file_name}: {e}")
            return None

    def move_files_to_parent_directory(self):
        files_to_move = self._get_files_to_move()
       
        if not files_to_move:
            return
        copied_count = 0
        
        for filename in files_to_move:
            source_path = os.path.join(self.local_dir, filename)
            destination_path = os.path.join(self.destination_root, os.path.basename(filename))

            if os.path.exists(source_path):
                try:
                    shutil.copy(source_path, destination_path)
                    copied_count += 1
                except Exception as e:
                    print(f"Error moving model file {filename}: {e}")
            else:
                print(f"Error file to move not found ({self.local_dir}): {filename}")
        
