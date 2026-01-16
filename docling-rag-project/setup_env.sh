#!/bin/bash
# Configuration pour éviter les timeouts HuggingFace

# Augmenter le timeout de téléchargement (en secondes)
export HF_HUB_DOWNLOAD_TIMEOUT=600

# Utiliser un seul worker pour éviter la surcharge
export HF_HUB_DOWNLOAD_MAX_WORKERS=1

# Activer le mode verbose pour voir la progression
export HF_HUB_VERBOSITY=info

echo "Configuration HuggingFace appliquée"
echo "Timeout: 600 secondes"
echo "Workers: 1"
echo ""
echo "Vous pouvez maintenant lancer votre script Python"
