@echo off
REM Script de démarrage rapide pour Windows

echo ==========================================
echo Quick Start - Projet RAG Docling
echo ==========================================
echo.

REM Vérification de Python
python --version >nul 2>&1
if errorlevel 1 (
    echo X Python n'est pas installe
    exit /b 1
)

echo + Python detecte
python --version
echo.

REM Création de l'environnement virtuel
if not exist "venv" (
    echo Creation de l'environnement virtuel...
    python -m venv venv
    echo + Environnement virtuel cree
) else (
    echo + Environnement virtuel existe deja
)

echo.

REM Activation de l'environnement virtuel
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
echo + Environnement active
echo.

REM Installation des dépendances
echo Installation des dependances...
pip install -r requirements.txt
echo + Dependances installees
echo.

REM Vérification de la configuration
if not exist "config.yaml" (
    echo X Fichier config.yaml manquant
    echo    Veuillez creer config.yaml avec vos parametres AWS
    exit /b 1
)

echo + Configuration trouvee
echo.

REM Test en mode dry-run
echo ==========================================
echo Test en mode DRY-RUN
echo ==========================================
echo.

if not exist "data\input\test.pdf" (
    echo ! Aucun PDF de test trouve dans data\input\
    echo    Placez un fichier PDF dans data\input\ pour tester
    echo.
    echo Pour tester avec vos propres fichiers:
    echo   1. Copiez un PDF dans data\input\
    echo   2. Lancez: python src\ingestion.py --input data\input\votre_fichier.pdf --dry-run
    echo   3. Lancez: python src\query.py --question "Votre question?" --dry-run
) else (
    echo Test d'ingestion...
    python src\ingestion.py --input data\input\test.pdf --dry-run
    echo.
    
    echo Test d'interrogation...
    python src\query.py --question "Qu'est-ce qu'un Data Fabric?" --dry-run
    echo.
)

echo ==========================================
echo + Quick Start termine
echo ==========================================
echo.
echo Prochaines etapes:
echo   1. Configurez vos endpoints AWS dans config.yaml
echo   2. Placez vos PDFs dans data\input\
echo   3. Lancez l'ingestion: python src\ingestion.py --input data\input\votre_fichier.pdf
echo   4. Interrogez: python src\query.py --question "Votre question?"
echo.

pause
