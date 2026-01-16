# Guide de démarrage rapide

## 🚀 Installation en 5 minutes

### Prérequis

- Python 3.8 ou supérieur
- Compte AWS avec accès à Neptune et OpenSearch
- 2 Go d'espace disque libre

### Étape 1 : Cloner et installer

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### Étape 2 : Configuration

**A. Obtenir une clé API Cohere**

1. Créer un compte sur [cohere.com](https://cohere.com/)
2. Aller sur [dashboard.cohere.com/api-keys](https://dashboard.cohere.com/api-keys)
3. Créer une nouvelle clé API

**B. Configurer la clé API**

```bash
# Linux/Mac
export COHERE_API_KEY="votre-cle-api"

# Windows CMD
set COHERE_API_KEY=votre-cle-api

# Windows PowerShell
$env:COHERE_API_KEY="votre-cle-api"
```

**C. Éditer config.yaml avec vos paramètres AWS**

```yaml
neptune:
  endpoint: "votre-cluster.neptune.amazonaws.com"
  port: 8182
  region: "eu-west-1"

opensearch:
  endpoint: "https://votre-domaine.es.amazonaws.com"
  index_name: "document-chunks"
  region: "eu-west-1"

embeddings:
  provider: "cohere"
  model: "embed-multilingual-v3"
  dimension: 1024
  api_key: ""  # Laisser vide si variable d'environnement définie
```

📖 **Voir [COHERE_SETUP.md](COHERE_SETUP.md) pour plus de détails sur la configuration Cohere**

### Étape 3 : Test en mode dry-run

```bash
# Placer un PDF dans data/input/
cp votre_document.pdf data/input/

# Tester l'ingestion (sans connexion AWS)
python src/ingestion.py --input data/input/votre_document.pdf --dry-run

# Tester l'interrogation (sans connexion AWS)
python src/query.py --question "Qu'est-ce qu'un Data Fabric?" --dry-run
```

Résultat : Des fichiers CSV sont générés dans `dry_run_output/`

### Étape 4 : Ingestion réelle

```bash
# Ingérer le document dans Neptune et OpenSearch
python src/ingestion.py --input data/input/votre_document.pdf
```

Sortie attendue :
```
=== Initialisation du pipeline d'ingestion ===
✓ Connexion Neptune établie
✓ Index document-chunks créé

Étape 1/5: Extraction et chunking avec Docling
✓ 45 chunks créés

Étape 2/5: Génération des embeddings
✓ 45 embeddings générés

Étape 3/5: Insertion des métadonnées dans Neptune
✓ 45 chunks insérés dans Neptune

Étape 4/5: Insertion des embeddings dans OpenSearch
✓ 45 chunks indexés dans OpenSearch

✓ Traitement terminé avec succès
```

### Étape 5 : Interrogation

```bash
# Poser une question
python src/query.py --question "Quelle est l'architecture du système?"
```

Résultat : Un fichier texte est créé dans `data/output/` avec le prompt augmenté

## 📊 Workflow typique

```
┌─────────────────────────────────────────────────────────────┐
│                    WORKFLOW COMPLET                         │
└─────────────────────────────────────────────────────────────┘

1. PRÉPARATION
   ├─ Configurer config.yaml
   ├─ Placer PDFs dans data/input/
   └─ Vérifier connexions AWS

2. INGESTION (une fois par document)
   ├─ python src/ingestion.py --input data/input/doc1.pdf
   ├─ python src/ingestion.py --input data/input/doc2.pdf
   └─ python src/ingestion.py --input data/input/doc3.pdf

3. INTERROGATION (autant de fois que nécessaire)
   ├─ python src/query.py --question "Question 1?"
   ├─ python src/query.py --question "Question 2?"
   └─ python src/query.py --question "Question 3?"

4. UTILISATION DES PROMPTS
   ├─ Ouvrir data/output/prompt_*.txt
   ├─ Copier le contenu
   └─ Envoyer à un LLM (GPT-4, Claude, etc.)
```

## 🎯 Cas d'usage

### Cas 1 : Documentation technique

```bash
# Ingérer la documentation
python src/ingestion.py --input data/input/technical_doc.pdf

# Poser des questions
python src/query.py --question "Comment configurer le système?"
python src/query.py --question "Quelles sont les dépendances requises?"
python src/query.py --question "Comment résoudre l'erreur X?"
```

### Cas 2 : Analyse de contrats

```bash
# Ingérer plusieurs contrats
python src/ingestion.py --input data/input/contrat_2024.pdf
python src/ingestion.py --input data/input/contrat_2025.pdf

# Rechercher des clauses spécifiques
python src/query.py --question "Quelles sont les clauses de résiliation?"
python src/query.py --question "Quel est le montant total des engagements?"
```

### Cas 3 : Base de connaissances

```bash
# Ingérer toute la documentation
for file in data/input/*.pdf; do
    python src/ingestion.py --input "$file"
done

# Interroger la base
python src/query.py --question "Qu'est-ce qu'un Data Fabric?"
python src/query.py --question "Comment fonctionne l'architecture?"
```

## 🔧 Options avancées

### Utiliser le filtrage Neptune

```bash
python src/query.py \
    --question "Comment fonctionne l'ingestion?" \
    --use-neptune-filter
```

Avantage : Réduit l'espace de recherche en utilisant le graphe de connaissances

### Personnaliser la configuration

```yaml
# Ajuster les paramètres de chunking
docling:
  chunk_size: 1024      # Plus grand = plus de contexte
  chunk_overlap: 100    # Plus grand = meilleure continuité
  min_chunk_size: 50    # Plus petit = plus de chunks

# Ajuster la recherche
query:
  top_k: 10             # Plus grand = plus de résultats
  similarity_threshold: 0.7  # Plus haut = plus strict
```

### Utiliser un meilleur modèle d'embeddings

Le projet utilise déjà **Cohere embed-multilingual-v3**, un des meilleurs modèles pour le français.

Si vous souhaitez utiliser un modèle local (sans API) :

```yaml
embeddings:
  provider: "sentence-transformers"
  model: "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
  dimension: 768
  batch_size: 32
```

**Note** : Nécessite de ré-ingérer tous les documents et recréer l'index OpenSearch.

## 📈 Monitoring

### Vérifier les données dans Neptune

```bash
# Via AWS CLI
aws neptune describe-db-clusters

# Via Neptune Workbench (Gremlin)
g.V().hasLabel('Document').count()
g.V().hasLabel('Chunk').count()
g.V().hasLabel('Annotation').count()
```

### Vérifier l'index OpenSearch

```bash
# Via AWS CLI
aws opensearch describe-domain --domain-name votre-domaine

# Via API
curl -X GET "https://votre-domaine.es.amazonaws.com/document-chunks/_count"
```

## 🐛 Dépannage rapide

### Problème : "Connection refused" (Neptune)

```bash
# Vérifier l'endpoint
aws neptune describe-db-clusters --query 'DBClusters[*].Endpoint'

# Vérifier les security groups (port 8182 doit être ouvert)
```

### Problème : "Index not found" (OpenSearch)

```python
# Créer l'index manuellement
from opensearch_client import OpenSearchClient
client = OpenSearchClient(...)
client.create_index(dimension=384)
```

### Problème : Chunks de mauvaise qualité

```yaml
# Ajuster les paramètres dans config.yaml
docling:
  chunk_size: 256       # Réduire pour plus de précision
  chunk_overlap: 50
  min_chunk_size: 100   # Augmenter pour éviter les petits chunks
```

### Problème : Résultats non pertinents

```bash
# Augmenter top_k et le seuil
python src/query.py \
    --question "..." \
    --use-neptune-filter  # Activer le filtrage
```

## 📚 Ressources

### Documentation

- [README.md](README.md) - Vue d'ensemble et architecture
- [ARCHITECTURE.md](ARCHITECTURE.md) - Détails techniques
- [EXAMPLES.md](EXAMPLES.md) - Exemples complets
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Guide de dépannage

### Diagrammes

- [architecture_diagram.svg](architecture_diagram.svg) - Schéma visuel

### Scripts

- `quick_start.sh` (Linux/Mac) - Installation automatique
- `quick_start.bat` (Windows) - Installation automatique

## 💡 Conseils

### Performance

1. **GPU** : Utiliser un GPU pour les embeddings (10x plus rapide)
2. **Batch** : Traiter plusieurs documents en parallèle
3. **Cache** : Réutiliser les embeddings quand possible

### Qualité

1. **Chunking** : Ajuster chunk_size selon le type de document
2. **Modèle** : Utiliser un modèle adapté à votre langue
3. **Annotations** : Personnaliser les annotations selon vos besoins

### Coûts

1. **Neptune** : Arrêter le cluster quand non utilisé
2. **OpenSearch** : Utiliser des instances adaptées à votre charge
3. **Dry-run** : Tester en mode dry-run avant déploiement

## 🎓 Prochaines étapes

1. ✅ Installer et tester en mode dry-run
2. ✅ Configurer AWS (Neptune + OpenSearch)
3. ✅ Ingérer vos premiers documents
4. ✅ Tester des questions
5. ⬜ Personnaliser les annotations
6. ⬜ Optimiser les paramètres
7. ⬜ Intégrer avec votre LLM préféré
8. ⬜ Déployer en production

## 🤝 Support

En cas de problème :
1. Consulter [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Vérifier les logs
3. Tester en mode dry-run
4. Vérifier la configuration AWS

Bon démarrage ! 🚀
