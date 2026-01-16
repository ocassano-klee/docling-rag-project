@echo off
REM Configuration pour éviter les timeouts HuggingFace

REM Augmenter le timeout de téléchargement (en secondes)
set HF_HUB_DOWNLOAD_TIMEOUT=600

REM Utiliser un seul worker pour éviter la surcharge
set HF_HUB_DOWNLOAD_MAX_WORKERS=1

REM Activer le mode verbose pour voir la progression
set HF_HUB_VERBOSITY=info

echo Configuration HuggingFace appliquée
echo Timeout: 600 secondes
echo Workers: 1
echo.
echo Vous pouvez maintenant lancer votre script Python
