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

### Script d'ingestion (`ingestion.py`)

1. **Extraction PDF avec Docling** : Parse les PDFs locaux (compatible S3 pour évolution future)
2. **Chunking intelligent** : Découpe le document en chunks sémantiques
3. **Annotations contextuelles** : Enrichit chaque chunk avec métadonnées (page, section, type)
4. **Stockage Neptune** : Insère les annotations et relations dans le graphe
5. **Embeddings vectoriels** : Génère les représentations vectorielles des chunks
6. **Indexation OpenSearch** : Stocke les embeddings pour recherche de similarité
7. **Mode Dry-Run** : Génère des fichiers CSV avec les requêtes sans exécution

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

En mode dry-run, les fichiers suivants sont générés :

- `dry_run_output/neptune_inserts.csv` : Requêtes Cypher pour Neptune
- `dry_run_output/opensearch_inserts.csv` : Requêtes API OpenSearch

Format CSV Neptune :
```csv
query_type,query,parameters
CREATE_DOCUMENT,"CREATE (d:Document {id: $id, title: $title})","{""id"": ""doc1"", ""title"": ""...""}
CREATE_CHUNK,"CREATE (c:Chunk {id: $id, content: $content})","{""id"": ""chunk1"", ...}"
```

Format CSV OpenSearch :
```csv
action,index,document_id,body
index,document-chunks,doc1_chunk_001,"{""content"": ""..."", ""embedding"": [...]}"
```

## Dépendances principales

- `docling` : Extraction et parsing de PDF
- `cohere` : Génération d'embeddings multilingues (1024 dimensions)
- `opensearch-py` : Client OpenSearch
- `gremlinpython` : Client Neptune (Gremlin)
- `boto3` : SDK AWS (pour S3, IAM)

## Évolutions futures

- [ ] Support complet S3 pour lecture de documents
- [ ] Batch processing pour ingestion massive
- [ ] Cache des embeddings
- [ ] Interface web pour interrogation
- [ ] Support multi-langues
- [ ] Métriques et monitoring

## Licence

MIT
