#!/bin/bash
# Script pour traiter tous les PDFs du dossier data/input en mode dry-run
# Chaque PDF génère ses propres fichiers de sortie

echo "========================================"
echo "Ingestion batch de tous les PDFs"
echo "========================================"
echo ""

# Compter les PDFs
count=$(ls -1 data/input/*.pdf 2>/dev/null | wc -l)

if [ $count -eq 0 ]; then
    echo "Aucun fichier PDF trouvé dans data/input/"
    echo "Veuillez placer vos PDFs dans ce dossier."
    exit 1
fi

echo "Nombre de PDFs trouvés : $count"
echo ""

# Traiter chaque PDF
current=0
for pdf in data/input/*.pdf; do
    current=$((current + 1))
    filename=$(basename "$pdf")
    echo "[$current/$count] Traitement de $filename..."
    python src/ingestion.py --input "$pdf" --dry-run
    echo ""
done

echo "========================================"
echo "Traitement terminé !"
echo "========================================"
echo ""
echo "Fichiers générés dans dry_run_output/ :"
ls -1 dry_run_output/*.csv
echo ""
ls -1 dry_run_output/*.png
