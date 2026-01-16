# Traitement en batch de plusieurs PDFs

## Vue d'ensemble

Le système supporte maintenant le traitement de plusieurs documents PDF sans écraser les sorties précédentes. Chaque document génère ses propres fichiers de sortie identifiés par le nom du document.

## Fichiers de sortie

En mode `--dry-run`, chaque document génère 3 fichiers dans `dry_run_output/` :

```
dry_run_output/
├── neptune_inserts_{doc_name}.csv      # Requêtes Neptune
├── opensearch_inserts_{doc_name}.csv   # Requêtes OpenSearch
└── neptune_graph_{doc_name}.png        # Visualisation du graphe
```

Où `{doc_name}` est le nom du fichier PDF sans l'extension (ex: `doc` pour `doc.pdf`).

## Méthode 1 : Traitement manuel

Traitez chaque PDF individuellement :

```bash
# Windows
python src/ingestion.py --input data/input/document1.pdf --dry-run
python src/ingestion.py --input data/input/document2.pdf --dry-run
python src/ingestion.py --input data/input/document3.pdf --dry-run

# Linux/Mac
python src/ingestion.py --input data/input/document1.pdf --dry-run
python src/ingestion.py --input data/input/document2.pdf --dry-run
python src/ingestion.py --input data/input/document3.pdf --dry-run
```

## Méthode 2 : Script de batch automatique

Utilisez le script fourni pour traiter automatiquement tous les PDFs du dossier `data/input/` :

### Windows

```cmd
batch_ingestion.bat
```

### Linux/Mac

```bash
chmod +x batch_ingestion.sh
./batch_ingestion.sh
```

Le script :
1. Compte le nombre de PDFs dans `data/input/`
2. Traite chaque PDF en mode dry-run
3. Affiche la progression
4. Liste tous les fichiers générés

## Exemple de sortie

Avec 3 PDFs (`doc.pdf`, `rapport.pdf`, `contrat.pdf`) :

```
dry_run_output/
├── neptune_inserts_doc.csv
├── opensearch_inserts_doc.csv
├── neptune_graph_doc.png
├── neptune_inserts_rapport.csv
├── opensearch_inserts_rapport.csv
├── neptune_graph_rapport.png
├── neptune_inserts_contrat.csv
├── opensearch_inserts_contrat.csv
└── neptune_graph_contrat.png
```

## Mode production (sans --dry-run)

En mode production, les graphes sont générés dans `data/output/` :

```bash
python src/ingestion.py --input data/input/document.pdf
```

Génère :
```
data/output/
└── neptune_graph_{doc_name}.png
```

## Conseils

### Nommage des fichiers

Utilisez des noms de fichiers descriptifs et sans espaces :
- ✅ `rapport_annuel_2024.pdf`
- ✅ `contrat_client_abc.pdf`
- ❌ `mon document.pdf` (espaces)
- ❌ `doc (1).pdf` (caractères spéciaux)

### Organisation

Pour traiter un grand nombre de documents :

1. Placez tous vos PDFs dans `data/input/`
2. Lancez `batch_ingestion.bat` (Windows) ou `batch_ingestion.sh` (Linux/Mac)
3. Vérifiez les sorties dans `dry_run_output/`
4. Si tout est correct, relancez sans `--dry-run` pour l'ingestion réelle

### Nettoyage

Pour nettoyer les sorties de test :

```bash
# Windows
del /Q dry_run_output\*

# Linux/Mac
rm -f dry_run_output/*
```

## Intégration dans un workflow

### Exemple : Pipeline CI/CD

```bash
#!/bin/bash
# Pipeline d'ingestion automatique

# 1. Télécharger les nouveaux documents depuis S3
aws s3 sync s3://mon-bucket/documents/ data/input/

# 2. Tester en dry-run
./batch_ingestion.sh

# 3. Vérifier les résultats
if [ $? -eq 0 ]; then
    echo "Dry-run réussi, lancement de l'ingestion réelle..."
    
    # 4. Ingestion réelle
    for pdf in data/input/*.pdf; do
        python src/ingestion.py --input "$pdf"
    done
else
    echo "Erreur lors du dry-run"
    exit 1
fi
```

### Exemple : Traitement planifié

```bash
# Cron job pour traiter les nouveaux documents chaque nuit
0 2 * * * cd /path/to/project && ./batch_ingestion.sh >> logs/batch_$(date +\%Y\%m\%d).log 2>&1
```

## Dépannage

### Problème : Fichiers écrasés

Si vos fichiers sont écrasés, vérifiez que :
- Vous utilisez la dernière version du code
- Les noms de vos PDFs sont différents
- Le nom du document est correctement extrait (visible dans les logs)

### Problème : Erreur de mémoire

Pour traiter de nombreux documents volumineux :
- Traitez-les par petits lots
- Augmentez la mémoire disponible pour Python
- Réduisez `chunk_size` dans `config.yaml`

### Problème : Caractères spéciaux dans les noms

Si vos noms de fichiers contiennent des caractères spéciaux, renommez-les :

```bash
# Remplacer les espaces par des underscores
for f in data/input/*.pdf; do
    mv "$f" "${f// /_}"
done
```

## Voir aussi

- [GETTING_STARTED.md](GETTING_STARTED.md) - Guide de démarrage
- [EXAMPLES.md](EXAMPLES.md) - Exemples d'utilisation
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Guide de dépannage
