"""
Script pour télécharger manuellement les modèles Docling
Utile en cas de timeout ou restrictions réseau
"""

import os
import time
from huggingface_hub import snapshot_download, hf_hub_download

def download_with_retry(repo_id, max_retries=3, timeout=600):
    """
    Télécharge un modèle avec retry automatique
    
    Args:
        repo_id: ID du repository HuggingFace
        max_retries: Nombre de tentatives
        timeout: Timeout en secondes
    """
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    
    for attempt in range(1, max_retries + 1):
        print(f"\n{'='*60}")
        print(f"Tentative {attempt}/{max_retries} pour {repo_id}")
        print(f"{'='*60}")
        
        try:
            # Configuration des variables d'environnement
            os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = str(timeout)
            os.environ['HF_HUB_DOWNLOAD_MAX_WORKERS'] = '1'
            
            print(f"Timeout configuré: {timeout}s")
            print(f"Cache directory: {cache_dir}")
            print("Téléchargement en cours...")
            
            snapshot_download(
                repo_id=repo_id,
                cache_dir=cache_dir,
                resume_download=True,
                max_workers=1,
                local_files_only=False
            )
            
            print(f"\n✓ {repo_id} téléchargé avec succès!")
            return True
            
        except Exception as e:
            print(f"\n✗ Erreur: {e}")
            
            if attempt < max_retries:
                wait_time = 10 * attempt
                print(f"Nouvelle tentative dans {wait_time} secondes...")
                time.sleep(wait_time)
            else:
                print(f"\n✗ Échec après {max_retries} tentatives")
                return False

def download_docling_models():
    """Télécharge les modèles Docling depuis HuggingFace"""
    
    print("="*60)
    print("TÉLÉCHARGEMENT DES MODÈLES DOCLING")
    print("="*60)
    
    models = [
        "docling-project/docling-layout-heron",
    ]
    
    success_count = 0
    
    for model in models:
        if download_with_retry(model, max_retries=3, timeout=600):
            success_count += 1
    
    print("\n" + "="*60)
    print(f"RÉSUMÉ: {success_count}/{len(models)} modèles téléchargés")
    print("="*60)
    
    if success_count == len(models):
        print("\n✓ Tous les modèles sont prêts!")
        print("Vous pouvez maintenant utiliser Docling avec layout detection.")
    else:
        print("\n⚠ Certains modèles n'ont pas pu être téléchargés.")
        print("Vérifiez votre connexion internet ou essayez:")
        print("  - D'augmenter le timeout")
        print("  - De configurer un proxy si nécessaire")
        print("  - De télécharger depuis un autre réseau")

if __name__ == "__main__":
    download_docling_models()
