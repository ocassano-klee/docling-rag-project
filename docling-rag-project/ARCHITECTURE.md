# Architecture détaillée du système RAG

## Vue d'ensemble

Le système implémente un pipeline RAG (Retrieval-Augmented Generation) complet avec trois composants principaux:

1. **Docling** : Extraction et chunking intelligent de documents PDF
2. **Neptune** : Graphe de connaissances pour métadonnées et annotations
3. **OpenSearch** : Index vectoriel pour recherche de similarité

## Architecture des données

### Flux d'ingestion

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          PIPELINE D'INGESTION                           │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────┐
    │   PDF    │
    │  Local   │
    │  ou S3   │
    └────┬─────┘
         │
         ▼
    ┌──────────────────────────────────────────┐
    │         DOCLING PROCESSOR                │
    │  • Parse PDF structure                   │
    │  • Extract text, tables, images          │
    │  • Identify sections, paragraphs         │
    │  • Preserve document hierarchy           │
    └────┬─────────────────────────────────────┘
         │
         ▼
    ┌──────────────────────────────────────────┐
    │         CHUNKING ENGINE                  │
    │  • Split by semantic units               │
    │  • Maintain context overlap              │
    │  • Preserve metadata (page, type, bbox)  │
    │  • Generate unique chunk IDs             │
    └────┬─────────────────────────────────────┘
         │
         ▼
    ┌──────────────────────────────────────────┐
    │      ANNOTATION GENERATOR                │
    │  • Element type (paragraph, title, etc.) │
    │  • Location (page number)                │
    │  • Length category                       │
    │  • Keyword extraction                    │
    │  • Contextual descriptions               │
    └────┬─────────────────────────────────────┘
         │
         ├─────────────────────┬────────────────────────┐
         │                     │                        │
         ▼                     ▼                        ▼
    ┌─────────┐         ┌──────────┐           ┌──────────────┐
    │ NEPTUNE │         │ EMBEDDING│           │  OPENSEARCH  │
    │  GRAPH  │         │ GENERATOR│           │    INDEX     │
    │         │         │          │           │              │
    │ Stores: │         │ Creates: │           │   Stores:    │
    │ • Docs  │         │ • Vector │───────────▶│ • Vectors    │
    │ • Chunks│         │   (384d) │           │ • Content    │
    │ • Annot.│         │ • Batch  │           │ • Metadata   │
    │ • Rels  │         │   process│           │ • KNN index  │
    └─────────┘         └──────────┘           └──────────────┘
```

### Flux d'interrogation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PIPELINE D'INTERROGATION                         │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │   Question   │
    │ utilisateur  │
    └──────┬───────┘
           │
           ▼
    ┌──────────────────────────────────────────┐
    │      EMBEDDING GENERATOR                 │
    │  • Vectorize question                    │
    │  • Same model as ingestion               │
    │  • Output: 384-dim vector                │
    └──────┬───────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────┐
    │      OPENSEARCH KNN SEARCH               │
    │  • Cosine similarity                     │
    │  • Top-K retrieval (default: 5)          │
    │  • Optional: filter by chunk IDs         │
    └──────┬───────────────────────────────────┘
           │
           │  ┌────────────────────────────────┐
           │  │  OPTIONAL: NEPTUNE FILTER      │
           │  │  • Extract entities from Q     │
           │  │  • Find related chunks in graph│
           │  │  • Reduce search space         │
           │  └────────────┬───────────────────┘
           │               │
           ▼◀──────────────┘
    ┌──────────────────────────────────────────┐
    │      TOP-K SIMILAR CHUNKS                │
    │  • Chunk IDs                             │
    │  • Content                               │
    │  • Similarity scores                     │
    │  • Basic metadata                        │
    └──────┬───────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────┐
    │      NEPTUNE ANNOTATION RETRIEVAL        │
    │  For each chunk:                         │
    │  • Query: MATCH (c)-[:HAS_ANN]->(a)      │
    │  • Retrieve all annotations              │
    │  • Enrich chunk with context             │
    └──────┬───────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────┐
    │      PROMPT AUGMENTATION                 │
    │  • Format context sections               │
    │  • Include annotations                   │
    │  • Add original question                 │
    │  • Add LLM instructions                  │
    └──────┬───────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────┐
    │      OUTPUT FILE                         │
    │  • Timestamp-based filename              │
    │  • Structured prompt format              │
    │  • Ready for LLM consumption             │
    └──────────────────────────────────────────┘
```

## Modèle de données Neptune

### Structure du graphe

```
                    ┌─────────────────┐
                    │    Document     │
                    │─────────────────│
                    │ id: string      │
                    │ title: string   │
                    │ source: string  │
                    └────────┬────────┘
                             │
                             │ HAS_CHUNK
                             │
                    ┌────────▼────────┐
                    │     Chunk       │
                    │─────────────────│
                    │ id: string      │
                    │ document_id: str│
                    │ content: text   │
                    │ page: int       │
                    │ type: string    │
                    └────┬────────┬───┘
                         │        │
          HAS_ANNOTATION │        │ FOLLOWS
                         │        │ (séquence)
                    ┌────▼────┐   │
                    │Annotation│  │
                    │──────────│  │
                    │id: string│  │
                    │type: str │  │
                    │value: str│  │
                    │context:  │  │
                    │  string  │  │
                    └──────────┘  │
                                  │
                         ┌────────▼────────┐
                         │   Next Chunk    │
                         │─────────────────│
                         │ (même structure)│
                         └─────────────────┘
```

### Types d'annotations

1. **element_type** : Type d'élément (paragraph, title, table, list, etc.)
2. **location** : Position dans le document (page_X)
3. **length** : Catégorie de longueur (court, moyen, long)
4. **keywords** : Mots-clés détectés dans le contenu
5. **section** : Section du document (introduction, conclusion, etc.)

### Requêtes Cypher typiques

```cypher
// Créer un document
g.addV('Document')
 .property('id', 'doc1')
 .property('title', 'Architecture Guide')
 .property('source', 's3://bucket/doc.pdf')

// Créer un chunk avec relation
g.V().has('Document', 'id', 'doc1')
 .addE('HAS_CHUNK')
 .to(g.addV('Chunk')
     .property('id', 'doc1_chunk_001')
     .property('content', 'Le Data Fabric...')
     .property('page', 5))

// Créer une annotation
g.V().has('Chunk', 'id', 'doc1_chunk_001')
 .addE('HAS_ANNOTATION')
 .to(g.addV('Annotation')
     .property('type', 'keywords')
     .property('value', 'data fabric, architecture'))

// Trouver tous les chunks d'un document
g.V().has('Document', 'id', 'doc1')
 .out('HAS_CHUNK')
 .valueMap()

// Trouver les chunks avec un mot-clé
g.V().hasLabel('Annotation')
 .has('value', containing('data fabric'))
 .in('HAS_ANNOTATION')
 .valueMap()

// Trouver les chunks liés (contexte)
g.V().has('Chunk', 'id', 'doc1_chunk_001')
 .repeat(both().simplePath())
 .times(2)
 .hasLabel('Chunk')
 .dedup()
```

## Modèle de données OpenSearch

### Structure de l'index

```json
{
  "settings": {
    "index": {
      "knn": true,
      "knn.algo_param.ef_search": 100
    }
  },
  "mappings": {
    "properties": {
      "chunk_id": {
        "type": "keyword"
      },
      "document_id": {
        "type": "keyword"
      },
      "content": {
        "type": "text",
        "analyzer": "standard"
      },
      "embedding": {
        "type": "knn_vector",
        "dimension": 1024,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesimil",
          "engine": "nmslib",
          "parameters": {
            "ef_construction": 128,
            "m": 16
          }
        }
      },
      "metadata": {
        "properties": {
          "page": {"type": "integer"},
          "type": {"type": "keyword"},
          "length": {"type": "integer"},
          "bbox": {"type": "object"}
        }
      }
    }
  }
}
```

### Exemple de document indexé

```json
{
  "chunk_id": "architecture_chunk_0042",
  "document_id": "architecture",
  "content": "Le Data Fabric est une architecture de données moderne qui permet d'intégrer, de gérer et d'orchestrer les données à travers différents environnements cloud et on-premise. Il s'appuie sur des technologies comme les graphes de connaissances, l'IA et l'automatisation pour créer une couche d'abstraction unifiée.",
  "embedding": [
    0.0234, -0.1234, 0.5678, -0.2345, 0.8901, ...
    // 1024 dimensions au total (Cohere embed-multilingual-v3)
  ],
  "metadata": {
    "page": 3,
    "type": "paragraph",
    "length": 287,
    "bbox": {
      "x": 72,
      "y": 156,
      "width": 468,
      "height": 84
    }
  }
}
```

### Requêtes OpenSearch typiques

```json
// Recherche KNN (similarité cosinus)
{
  "size": 5,
  "query": {
    "knn": {
      "embedding": {
        "vector": [0.123, -0.456, ...],
        "k": 5
      }
    }
  }
}

// Recherche hybride (KNN + filtres)
{
  "size": 5,
  "query": {
    "bool": {
      "must": [
        {
          "knn": {
            "embedding": {
              "vector": [0.123, -0.456, ...],
              "k": 10
            }
          }
        }
      ],
      "filter": [
        {
          "term": {
            "document_id": "architecture"
          }
        },
        {
          "range": {
            "metadata.page": {
              "gte": 1,
              "lte": 10
            }
          }
        }
      ]
    }
  }
}

// Recherche textuelle classique
{
  "query": {
    "match": {
      "content": "data fabric architecture"
    }
  }
}
```

## Algorithme de chunking

### Stratégie de découpage

```
Document PDF
    │
    ├─ Page 1
    │   ├─ Title (élément complet = 1 chunk)
    │   ├─ Paragraph 1 (< 512 chars = 1 chunk)
    │   ├─ Paragraph 2 (> 512 chars = split en N chunks)
    │   │   ├─ Chunk 1 (512 chars)
    │   │   ├─ Chunk 2 (512 chars, overlap 50 chars)
    │   │   └─ Chunk 3 (reste)
    │   └─ Table (élément complet = 1 chunk)
    │
    ├─ Page 2
    │   └─ ...
    │
    └─ Page N
```

### Paramètres de chunking

- **chunk_size** : 512 caractères (configurable)
- **chunk_overlap** : 50 caractères (préserve le contexte)
- **min_chunk_size** : 100 caractères (évite les chunks trop petits)

### Préservation du contexte

Chaque chunk conserve:
- Numéro de page
- Type d'élément (paragraph, title, table, etc.)
- Position dans le document (bbox)
- Relation avec le chunk précédent (FOLLOWS)
- Relation avec le document parent (HAS_CHUNK)

## Génération d'embeddings

### Modèle utilisé

**Cohere embed-multilingual-v3**
- Dimension : 1024
- Multilingue : Oui (100+ langues, excellent pour le français)
- Vitesse : ~100-200 embeddings/sec via API
- Qualité : Supérieure aux modèles open-source
- Input types :
  - `search_document` : Pour indexer les documents
  - `search_query` : Pour les requêtes utilisateur

### Avantages de Cohere

- ✅ Pas besoin de GPU local
- ✅ Qualité supérieure pour le français
- ✅ Optimisé pour RAG (deux modes distincts)
- ✅ Scalable via API cloud
- ✅ Batch processing jusqu'à 96 textes

### Alternatives possibles

- **sentence-transformers/paraphrase-multilingual-mpnet-base-v2** : Gratuit, local (768 dim)
- **OpenAI text-embedding-ada-002** : Très haute qualité (1536 dim, API payante)
- **sentence-transformers/all-MiniLM-L6-v2** : Rapide mais anglais uniquement (384 dim)

### Processus de vectorisation

```python
import cohere

client = cohere.Client(api_key)

# Pour l'ingestion (documents)
response = client.embed(
    texts=[chunk1, chunk2, ..., chunkN],
    model="embed-multilingual-v3",
    input_type="search_document",
    embedding_types=["float"]
)
embeddings = response.embeddings.float

# Pour les requêtes (questions)
response = client.embed(
    texts=["question utilisateur"],
    model="embed-multilingual-v3",
    input_type="search_query",
    embedding_types=["float"]
)
query_embedding = response.embeddings.float[0]
```

## Recherche de similarité

### Algorithme HNSW (Hierarchical Navigable Small World)

OpenSearch utilise HNSW pour la recherche KNN:
- Complexité : O(log N) au lieu de O(N)
- Précision : ~95-99% (configurable)
- Paramètres :
  - **ef_construction** : 128 (qualité de l'index)
  - **m** : 16 (nombre de connexions par nœud)
  - **ef_search** : 100 (qualité de la recherche)

### Métrique de similarité

**Similarité cosinus** :
```
similarity = (A · B) / (||A|| × ||B||)
```

Valeurs :
- 1.0 : Identiques
- 0.0 : Orthogonaux (non liés)
- -1.0 : Opposés

## Mode Dry-Run

### Fichiers générés

#### neptune_inserts.csv (ingestion)
```csv
query_type,query,parameters
CREATE_DOCUMENT,"g.addV('Document')...","{'id': 'doc1', ...}"
CREATE_CHUNK,"g.addV('Chunk')...","{'id': 'chunk1', ...}"
CREATE_ANNOTATION,"g.addV('Annotation')...","{'type': 'keywords', ...}"
```

#### opensearch_inserts.csv (ingestion)
```csv
action,index,document_id,body
index,document-chunks,chunk1,"{""content"": ""..."", ""embedding"": [...]}"
```

#### neptune_queries.csv (interrogation)
```csv
query_type,query,parameters
GET_ANNOTATIONS,"MATCH (c)-[:HAS_ANN]->(a)...","{'chunk_id': 'chunk1'}"
```

#### opensearch_queries.csv (interrogation)
```csv
query_type,query,parameters
SEARCH_SIMILAR,"{""query"": {""knn"": {...}}}","{'top_k': 5}"
```

## Performances

### Ingestion

- **Parsing PDF** : ~2-5 sec/page (selon complexité)
- **Chunking** : ~0.1 sec/page
- **Embeddings** : ~0.01 sec/chunk (API Cohere, batch de 96)
- **Insertion Neptune** : ~0.1 sec/chunk
- **Indexation OpenSearch** : ~0.05 sec/chunk

**Total** : ~100-200 chunks/minute (avec API Cohere)

### Interrogation

- **Embedding question** : ~0.05 sec
- **Recherche OpenSearch** : ~0.1-0.5 sec (selon taille index)
- **Requêtes Neptune** : ~0.05 sec/chunk
- **Construction prompt** : ~0.01 sec

**Total** : ~1-2 secondes par question

## Scalabilité

### Limites actuelles

- Neptune : Millions de nœuds
- OpenSearch : Milliards de documents
- Embeddings : Limité par RAM/GPU

### Optimisations possibles

1. **Batch processing** : Traiter plusieurs documents en parallèle
2. **Cache** : Mettre en cache les embeddings fréquents
3. **Sharding** : Distribuer l'index OpenSearch
4. **GPU** : Accélérer la génération d'embeddings
5. **Compression** : Réduire la dimension des vecteurs (PCA, quantization)
