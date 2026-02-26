from MTUOC_misc import printLOG
from huggingface_hub import snapshot_download
def download_aina_model(aina_repo,AinaTranslator_revision,alignment_repo,truecaser_repo,AinaTranslator_model_path):
        printLOG(1,"Downloading translation model.")
        model_dir = snapshot_download(repo_id=aina_repo,revision=AinaTranslator_revision, local_dir=AinaTranslator_model_path)
        printLOG(1,"Downloading alignment model.")                           
        ali_model_dir = snapshot_download(repo_id=alignment_repo, revision="main", local_dir=AinaTranslator_model_path)
        if not truecaser_repo==None:
            try:
                printLOG(1,"Downloading truecaser model.")
                truecaser_repo_dir = snapshot_download(repo_id=truecaser_repo, revision="main", local_dir=AinaTranslator_model_path) 
            except:
                printLOG(1,"Error  downloading truecaser model from ",truecaser_repo,sys.exec_info())
