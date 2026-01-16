@echo off
REM Script de test pour traiter plusieurs PDFs en mode dry-run
REM Chaque PDF génère ses propres fichiers de sortie

echo ========================================
echo Test d'ingestion de plusieurs PDFs
echo ========================================
echo.

REM Traiter le premier PDF
echo [1/1] Traitement de doc.pdf...
python src/ingestion.py --input data/input/doc.pdf --dry-run

echo.
echo ========================================
echo Test terminé !
echo ========================================
echo.
echo Fichiers générés dans dry_run_output/ :
dir /B dry_run_output\*.csv
dir /B dry_run_output\*.png
echo.
echo Vous pouvez maintenant ajouter d'autres PDFs dans data/input/
echo et relancer ce script pour les traiter sans écraser les sorties.
pause
