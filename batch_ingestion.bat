@echo off
REM Script pour traiter tous les PDFs du dossier data/input en mode dry-run
REM Chaque PDF génère ses propres fichiers de sortie

echo ========================================
echo Ingestion batch de tous les PDFs
echo ========================================
echo.

REM Compter les PDFs
set count=0
for %%f in (data\input\*.pdf) do set /a count+=1

if %count%==0 (
    echo Aucun fichier PDF trouvé dans data/input/
    echo Veuillez placer vos PDFs dans ce dossier.
    pause
    exit /b
)

echo Nombre de PDFs trouvés : %count%
echo.

REM Traiter chaque PDF
set current=0
for %%f in (data\input\*.pdf) do (
    set /a current+=1
    echo [!current!/%count%] Traitement de %%~nxf...
    python src/ingestion.py --input "%%f" --dry-run
    echo.
)

echo ========================================
echo Traitement terminé !
echo ========================================
echo.
echo Fichiers générés dans dry_run_output/ :
dir /B dry_run_output\*.csv
echo.
dir /B dry_run_output\*.png
pause
