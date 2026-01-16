#!/bin/bash

# Script de démarrage rapide pour le projet RAG Docling

echo "=========================================="
echo "Quick Start - Projet RAG Docling"
echo "=========================================="
echo ""

# Vérification de Python
if ! command -v python &> /dev/null; then
    echo "❌ Python n'est pas installé"
    exit 1
fi

echo "✓ Python détecté: $(python --version)"
echo ""

# Création de l'environnement virtuel
if [ ! -d "venv" ]; then
    echo "Création de l'environnement virtuel..."
    python -m venv venv
    echo "✓ Environnement virtuel créé"
else
    echo "✓ Environnement virtuel existe déjà"
fi

echo ""

# Activation de l'environnement virtuel
echo "Activation de l'environnement virtuel..."
source venv/bin/activate
echo "✓ Environnement activé"
echo ""

# Installation des dépendances
echo "Installation des dépendances..."
pip install -r requirements.txt
echo "✓ Dépendances installées"
echo ""

# Vérification de la configuration
if [ ! -f "config.yaml" ]; then
    echo "❌ Fichier config.yaml manquant"
    echo "   Veuillez créer config.yaml avec vos paramètres AWS"
    exit 1
fi

echo "✓ Configuration trouvée"
echo ""

# Test en mode dry-run
echo "=========================================="
echo "Test en mode DRY-RUN"
echo "=========================================="
echo ""

# Vérification d'un PDF de test
if [ ! -f "data/input/test.pdf" ]; then
    echo "⚠️  Aucun PDF de test trouvé dans data/input/"
    echo "   Placez un fichier PDF dans data/input/ pour tester"
    echo ""
    echo "Pour tester avec vos propres fichiers:"
    echo "  1. Copiez un PDF dans data/input/"
    echo "  2. Lancez: python src/ingestion.py --input data/input/votre_fichier.pdf --dry-run"
    echo "  3. Lancez: python src/query.py --question 'Votre question?' --dry-run"
else
    echo "Test d'ingestion..."
    python src/ingestion.py --input data/input/test.pdf --dry-run
    echo ""
    
    echo "Test d'interrogation..."
    python src/query.py --question "Qu'est-ce qu'un Data Fabric?" --dry-run
    echo ""
fi

echo "=========================================="
echo "✓ Quick Start terminé"
echo "=========================================="
echo ""
echo "Prochaines étapes:"
echo "  1. Configurez vos endpoints AWS dans config.yaml"
echo "  2. Placez vos PDFs dans data/input/"
echo "  3. Lancez l'ingestion: python src/ingestion.py --input data/input/votre_fichier.pdf"
echo "  4. Interrogez: python src/query.py --question 'Votre question?'"
echo ""
