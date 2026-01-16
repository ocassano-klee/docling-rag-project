# Projet RAG avec Docling, Neptune et OpenSearch

## Vue d'ensemble

Ce projet implémente un système RAG (Retrieval-Augmented Generation) complet qui utilise Docling pour extraire et chunker des documents PDF, Neptune pour stocker les métadonnées et annotations contextuelles, et OpenSearch pour la recherche vectorielle.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INGESTION PIPELINE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐      ┌──────────┐      ┌─────────────┐              │
│  │   PDF    │─────▶│ Docling  │─────▶│   Chunks    │              │
│  │ (Local/  │      │ Parser   │      │ + Metadata  │              │
│  │   S3)    │      └──────────┘      └─────────────┘              │
│  └──────────┘                               │                      │
│                                              │                      │
│                        ┌─────────────────────┴──────────────┐      │
│                        │                                     │      │
│                        ▼                                     ▼      │
│              ┌──────────────────┐                 ┌──────────────┐ │
│              │  Neptune Graph   │                 │  OpenSearch  │ │
│              │  (Annotations +  │                 │  (Embeddings │ │
│              │   Contexte)      │                 │   Vectoriels)│ │
│              └──────────────────┘                 └──────────────┘ │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         QUERY PIPELINE                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐      ┌──────────┐      ┌─────────────┐              │
│  │ Question │─────▶│ Embedding│─────▶│ OpenSearch  │              │
│  │          │      │ Model    │      │ Similarity  │              │
│  └──────────┘      └──────────┘      └──────┬──────┘              │
│                                              │                      │
│                                              ▼                      │
│                                    ┌──────────────────┐            │
│                                    │ Top-K Chunks     │            │
│                                    └────────┬─────────┘            │
│                                             │                       │
│                                             ▼                       │
│                                    ┌──────────────────┐            │
│                                    │ Neptune Query    │            │
│                                    │ (Annotations)    │            │
│                                    └────────┬─────────┘            │
│                                             │                       │
│                                             ▼                       │
│                                    ┌──────────────────┐            │
│                                    │ Augmented Prompt │            │
│                                    │ (Question +      │            │
│                                    │  Context)        │            │
│                                    └────────┬─────────┘            │
│                                             │                       │
│                                             ▼                       │
│                                    ┌──────────────────┐            │
│                                    │ Output File      │            │
│                                    │ (prompt.txt)     │            │
│                                    └──────────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

## Structure du projet

```
docling-rag-project/
├── README.md
├── requirements.txt
├── config.yaml
├── src/
│   ├── __init__.py
│   ├── ingestion.py          # Script d'ingestion des documents
│   ├── query.py              # Script d'interrogation
│   ├── docling_processor.py  # Traitement Docling
│   ├── neptune_client.py     # Client Neptune
│   ├── opensearch_client.py  # Client OpenSearch
│   └── embeddings.py         # Génération d'embeddings
├── data/
│   ├── input/                # PDFs à traiter
│   └── output/               # Résultats
└── dry_run_output/           # Fichiers CSV en mode dry-run
```

## Fonctionnalités

## Fonctionnalités

### Script d'ingestion (`ingestion.py`)

1. **Extraction PDF avec Docling** : Parse les PDFs locaux (compatible S3 pour évolution future)
2. **Extraction de tables** : Détecte et extrait automatiquement les tables
3. **Chunking intelligent** : Découpe le document en chunks sémantiques
4. **🆕 Extraction de topics** : Identifie automatiquement les concepts métier et mots-clés
5. **🆕 Graphe interconnecté** : Crée des nœuds Topic partagés entre documents
6. **Annotations contextuelles** : Enrichit chaque chunk avec métadonnées (page, section, type)
7. **Stockage Neptune** : Insère les annotations, topics et relations dans le graphe
8. **Embeddings vectoriels** : Génère les représentations vectorielles des chunks (Cohere)
9. **Indexation OpenSearch** : Stocke les embeddings pour recherche de similarité
10. **Visualisation du graphe** : Génère une image PNG du graphe Neptune
11. **Mode Dry-Run** : Génère des fichiers CSV avec les requêtes sans exécution

### Script d'interrogation (`query.py`)

1. **Embedding de la question** : Vectorise la question utilisateur
2. **Recherche de similarité** : Trouve les chunks pertinents dans OpenSearch (cosinus)
3. **Filtrage Neptune (optionnel)** : Réduit l'espace de recherche via le graphe
4. **Récupération annotations** : Enrichit avec le contexte Neptune
5. **Augmentation du prompt** : Combine question + contexte + chunks
6. **Export** : Génère un fichier texte avec le prompt augmenté
7. **Mode Dry-Run** : Génère des CSV avec les requêtes Cypher et OpenSearch

## Installation

```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer la clé API Cohere
export COHERE_API_KEY="votre-cle-api"
```

**Note** : Obtenez votre clé API Cohere sur [dashboard.cohere.com](https://dashboard.cohere.com/api-keys). Voir [COHERE_SETUP.md](COHERE_SETUP.md) pour plus de détails.

## Configuration

Éditer `config.yaml` avec vos paramètres AWS :

```yaml
# Neptune
neptune:
  endpoint: "your-neptune-cluster.cluster-xxxxx.region.neptune.amazonaws.com"
  port: 8182
  use_iam: true

# OpenSearch
opensearch:
  endpoint: "https://your-opensearch-domain.region.es.amazonaws.com"
  index_name: "document-chunks"
  
# Embeddings (Cohere)
embeddings:
  provider: "cohere"
  model: "embed-multilingual-v3"
  dimension: 1024
  api_key: ""  # Ou via variable d'environnement COHERE_API_KEY

# S3 (pour évolution future)
s3:
  bucket: "your-bucket-name"
  prefix: "documents/"
```

## Utilisation

### Ingestion de documents

```bash
# Mode normal (insertion réelle)
python src/ingestion.py --input data/input/document.pdf

# Mode dry-run (génération CSV)
python src/ingestion.py --input data/input/document.pdf --dry-run

# Depuis S3 (futur)
python src/ingestion.py --s3-uri s3://bucket/path/document.pdf
```

### Interrogation

```bash
# Mode normal
python src/query.py --question "Quelle est la définition de Data Fabric?"

# Mode dry-run
python src/query.py --question "Quelle est la définition de Data Fabric?" --dry-run

# Avec filtrage Neptune
python src/query.py --question "..." --use-neptune-filter
```

## Modèle de données

### Neptune (Graphe de connaissances)

```
┌─────────────┐
│  Document   │
│  - id       │
│  - title    │
│  - source   │
└──────┬──────┘
       │ HAS_CHUNK
       ▼
┌─────────────┐       ┌──────────────┐
│   Chunk     │──────▶│  Annotation  │
│  - id       │ HAS   │  - type      │
│  - content  │       │  - value     │
│  - page     │       │  - context   │
│  - position │       └──────────────┘
└─────────────┘
       │ FOLLOWS
       ▼
┌─────────────┐
│   Chunk     │
│  (suivant)  │
└─────────────┘
```

### OpenSearch (Index vectoriel)

```json
{
  "chunk_id": "doc1_chunk_001",
  "document_id": "doc1",
  "content": "Le Data Fabric est...",
  "embedding": [0.123, -0.456, ...],
  "metadata": {
    "page": 5,
    "section": "Introduction",
    "type": "paragraph"
  }
}
```

## Mode Dry-Run

En mode dry-run, les fichiers suivants sont générés dans `dry_run_output/` :

- `neptune_inserts_{doc_name}.csv` : Requêtes Cypher pour Neptune
- `opensearch_inserts_{doc_name}.csv` : Requêtes API OpenSearch
- `neptune_graph_{doc_name}.png` : Visualisation du graphe

Chaque document génère ses propres fichiers (identifiés par `{doc_name}`), permettant le traitement de plusieurs PDFs sans écraser les sorties.

Format CSV Neptune :
```csv
query_type,query,parameters
CREATE_DOCUMENT,"CREATE (d:Document {id: $id, title: $title})","{""id"": ""doc1"", ""title"": ""...""}
MERGE_TOPIC,"MERGE (t:Topic {id: $id, name: $name})","{""id"": ""topic_assurance"", ""name"": ""assurance""}"
CREATE_CHUNK,"CREATE (c:Chunk {id: $id, content: $content})","{""id"": ""chunk1"", ...}"
CREATE_RELATIONSHIP,"MATCH (c:Chunk), (t:Topic) CREATE (c)-[:ABOUT]->(t)",{}
```

Format CSV OpenSearch :
```csv
action,index,document_id,body
index,document-chunks,doc1_chunk_001,"{""content"": ""..."", ""embedding"": [...]}"
```

## Dépendances principales

- `docling` : Extraction et parsing de PDF avec détection de tables
- `cohere` : Génération d'embeddings multilingues (1024 dimensions)
- `opensearch-py` : Client OpenSearch
- `gremlinpython` : Client Neptune (Gremlin)
- `boto3` : SDK AWS (pour S3, IAM)
- `networkx` : Création et manipulation de graphes
- `matplotlib` : Visualisation du graphe Neptune

## Documentation complète

### Démarrage rapide
- **[START_HERE.md](START_HERE.md)** - Point de départ (5 min)
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Guide de démarrage complet
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Commandes essentielles
- **[COHERE_SETUP.md](COHERE_SETUP.md)** - Configuration Cohere

### Concepts avancés
- **[TOPICS_LINKING.md](TOPICS_LINKING.md)** - 🆕 Liaison des documents via topics
- **[BATCH_PROCESSING.md](BATCH_PROCESSING.md)** - 🆕 Traitement de plusieurs PDFs
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Détails techniques
- **[EXAMPLES.md](EXAMPLES.md)** - Exemples d'utilisation

### Support
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Guide de dépannage
- **[MIGRATION_COHERE.md](MIGRATION_COHERE.md)** - Migration depuis v1.0.0
- **[CHANGELOG.md](CHANGELOG.md)** - Historique des versions

## Nouveautés v2.0

### 🎯 Graphe de connaissances interconnecté

Les documents sont maintenant automatiquement liés via des **topics partagés** :

```python
# Document 1 : Remboursement dentaire
Topics extraits : ["assurance", "dentaire", "remboursement", "santé"]

# Document 2 : Contrat d'assurance
Topics extraits : ["assurance", "contrat", "mutuelle"]

# Résultat : Les deux documents sont liés via le topic "assurance" !
```

**Avantages** :
- Découverte automatique de documents connexes
- Navigation contextuelle entre documents similaires
- Analyse thématique de collections de documents
- Recommandations basées sur les concepts partagés

Voir [TOPICS_LINKING.md](TOPICS_LINKING.md) pour plus de détails.

### 📊 Visualisation du graphe

Chaque ingestion génère automatiquement une image PNG du graphe Neptune :
- Nœuds rouges : Documents
- Nœuds bleus : Chunks
- Nœuds jaunes : Topics (partagés entre documents)
- Nœuds verts : Annotations

### 🌐 Visualisation interactive (Graph Viewer)

Un outil de visualisation HTML interactif permet d'explorer comment vos documents sont liés :

```bash
cd dry_run_output/viewer
python generate_graph_viewer.py
# Ouvrir graph_viewer.html dans votre navigateur
```

**Fonctionnalités** :
- Navigation interactive dans le graphe complet
- Identification visuelle des topics partagés entre documents
- Layouts multiples (hiérarchique, force-directed, circulaire)
- Statistiques en temps réel
- Zoom et focus sur les connexions importantes

Voir [dry_run_output/viewer/README.md](dry_run_output/viewer/README.md) et [dry_run_output/viewer/USAGE_GUIDE.md](dry_run_output/viewer/USAGE_GUIDE.md) pour plus de détails.

### 🔄 Traitement batch

Traitez plusieurs PDFs sans écraser les sorties :

```bash
# Traiter tous les PDFs du dossier
./batch_ingestion.sh  # Linux/Mac
batch_ingestion.bat   # Windows
```

Voir [BATCH_PROCESSING.md](BATCH_PROCESSING.md) pour plus de détails.

## Évolutions futures

- [x] Support complet extraction de tables
- [x] Batch processing pour ingestion massive
- [x] Graphe de connaissances interconnecté via topics
- [x] Visualisation du graphe Neptune (PNG + HTML interactif)
- [ ] Support complet S3 pour lecture de documents
- [ ] Cache des embeddings
- [ ] Interface web pour interrogation
- [ ] Support multi-langues avancé
- [ ] Métriques et monitoring
- [ ] Extraction d'entités nommées (personnes, organisations)
- [ ] Liens de similarité sémantique entre chunks

## Licence

MIT
