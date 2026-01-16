# Exemples d'utilisation

## Exemple 1: Ingestion d'un document en mode dry-run

```bash
python src/ingestion.py --input data/input/architecture.pdf --dry-run
```

Résultat:
- Fichier `dry_run_output/neptune_inserts.csv` contenant les requêtes Cypher
- Fichier `dry_run_output/opensearch_inserts.csv` contenant les requêtes API OpenSearch

Exemple de contenu `neptune_inserts.csv`:
```csv
query_type,query,parameters
CREATE_DOCUMENT,"CREATE (d:Document {id: 'architecture', title: 'architecture.pdf', source: 'data/input/architecture.pdf'})","{'id': 'architecture', 'title': 'architecture.pdf'}"
CREATE_CHUNK,"CREATE (c:Chunk {id: 'architecture_chunk_0001', document_id: 'architecture', page: 1, type: 'paragraph'})","{'id': 'architecture_chunk_0001', ...}"
CREATE_ANNOTATION,"CREATE (a:Annotation {id: 'architecture_chunk_0001_ann_element_type', type: 'element_type', value: 'paragraph'})","{'type': 'element_type', ...}"
```

## Exemple 2: Ingestion réelle dans Neptune et OpenSearch

```bash
python src/ingestion.py --input data/input/architecture.pdf
```

Sortie console:
```
=== Initialisation du pipeline d'ingestion ===

Chargement du modèle d'embeddings: sentence-transformers/all-MiniLM-L6-v2
Connexion à Neptune: wss://your-cluster.neptune.amazonaws.com:8182/gremlin
✓ Connexion Neptune établie
✓ Index document-chunks créé

============================================================
Traitement du document: data/input/architecture.pdf
============================================================

Étape 1/5: Extraction et chunking avec Docling
Traitement du PDF: data/input/architecture.pdf
Créé 45 chunks pour le document architecture
✓ 45 chunks créés

Étape 2/5: Génération des embeddings
Batches: 100%|████████████████████| 2/2 [00:03<00:00,  1.50s/it]
✓ 45 embeddings générés

Étape 3/5: Insertion des métadonnées dans Neptune
✓ Document inséré: architecture
Insertion chunks Neptune: 100%|████████| 45/45 [00:12<00:00,  3.67it/s]
✓ 45 chunks insérés dans Neptune

Étape 4/5: Insertion des embeddings dans OpenSearch
Insertion OpenSearch: 100%|████████| 45/45 [00:08<00:00,  5.23it/s]
✓ 45 chunks indexés dans OpenSearch

============================================================
✓ Traitement terminé avec succès
============================================================
```

## Exemple 3: Interrogation en mode dry-run

```bash
python src/query.py --question "Qu'est-ce qu'un Data Fabric?" --dry-run
```

Résultat:
- Fichier `dry_run_output/neptune_queries.csv` avec les requêtes de récupération
- Fichier `dry_run_output/opensearch_queries.csv` avec les requêtes de recherche
- Fichier `data/output/prompt_YYYYMMDD_HHMMSS_Quest_ce_quun_Data_Fabric.txt`

Exemple de contenu `opensearch_queries.csv`:
```csv
query_type,query,parameters
SEARCH_SIMILAR,"{'size': 5, 'query': {'knn': {'embedding': {'vector': [0.123, -0.456, ...], 'k': 5}}}}","{'top_k': 5, 'embedding_dimension': 384}"
```

Exemple de contenu `neptune_queries.csv`:
```csv
query_type,query,parameters
GET_ANNOTATIONS,"MATCH (c:Chunk {id: 'doc1_chunk_0001'})-[:HAS_ANNOTATION]->(a:Annotation) RETURN a","{'chunk_id': 'doc1_chunk_0001'}"
GET_ANNOTATIONS,"MATCH (c:Chunk {id: 'doc1_chunk_0002'})-[:HAS_ANNOTATION]->(a:Annotation) RETURN a","{'chunk_id': 'doc1_chunk_0002'}"
```

## Exemple 4: Interrogation réelle

```bash
python src/query.py --question "Quelle est l'architecture du Data Fabric?"
```

Sortie console:
```
=== Initialisation du pipeline d'interrogation ===

Chargement du modèle d'embeddings: sentence-transformers/all-MiniLM-L6-v2
Connexion à Neptune: wss://your-cluster.neptune.amazonaws.com:8182/gremlin
✓ Connexion Neptune établie

============================================================
Question: Quelle est l'architecture du Data Fabric?
============================================================

Étape 1/5: Génération de l'embedding de la question
✓ Embedding généré (dimension: 384)

Étape 2/5: Recherche de similarité dans OpenSearch
✓ 5 chunks pertinents trouvés

Étape 3/5: Récupération des annotations depuis Neptune
✓ Chunks enrichis avec annotations

Étape 4/5: Construction du prompt augmenté
✓ Prompt augmenté construit (2847 caractères)

Étape 5/5: Export du résultat
✓ Prompt exporté: data/output/prompt_20250116_143022_Quelle_est_larchitecture_du.txt

============================================================
✓ Interrogation terminée avec succès
============================================================
```

Contenu du fichier de sortie `prompt_20250116_143022_Quelle_est_larchitecture_du.txt`:

```
================================================================================
PROMPT AUGMENTÉ POUR LLM
================================================================================

CONTEXTE RÉCUPÉRÉ:
--------------------------------------------------------------------------------

[CHUNK 1] (Score: 0.892)
Document: architecture
Page: 3
Type: paragraph

Annotations:
  • element_type: paragraph
    → Ce contenu est de type paragraph
  • location: page_3
    → Ce contenu se trouve à la page 3
  • keywords: data fabric, architecture
    → Contient les concepts: data fabric, architecture

Contenu:
Le Data Fabric est une architecture de données moderne qui permet d'intégrer,
de gérer et d'orchestrer les données à travers différents environnements...

--------------------------------------------------------------------------------

[CHUNK 2] (Score: 0.854)
Document: architecture
Page: 5
Type: title

Annotations:
  • element_type: title
    → Ce contenu est de type title
  • location: page_5
    → Ce contenu se trouve à la page 5

Contenu:
Architecture fonctionnelle du Data Fabric

--------------------------------------------------------------------------------

QUESTION:
--------------------------------------------------------------------------------
Quelle est l'architecture du Data Fabric?

================================================================================

INSTRUCTIONS:
En utilisant le contexte fourni ci-dessus, réponds à la question de manière
précise et détaillée. Si le contexte ne contient pas suffisamment d'informations,
indique-le clairement.

================================================================================
```

## Exemple 5: Interrogation avec filtrage Neptune

```bash
python src/query.py --question "Comment fonctionne l'ingestion?" --use-neptune-filter
```

Cette option utilise le graphe Neptune pour réduire l'espace de recherche en identifiant
les chunks liés sémantiquement avant la recherche vectorielle dans OpenSearch.

## Exemple 6: Workflow complet

```bash
# 1. Ingestion de plusieurs documents
python src/ingestion.py --input data/input/architecture.pdf
python src/ingestion.py --input data/input/guide_utilisateur.pdf
python src/ingestion.py --input data/input/specifications.pdf

# 2. Interrogations multiples
python src/query.py --question "Qu'est-ce qu'un Data Fabric?"
python src/query.py --question "Comment configurer l'ingestion de données?"
python src/query.py --question "Quelles sont les bonnes pratiques?"

# 3. Les prompts générés peuvent être envoyés à un LLM (GPT-4, Claude, etc.)
```

## Visualisation des données dans Neptune

Vous pouvez visualiser le graphe de connaissances avec Neptune Workbench:

```gremlin
// Voir tous les documents
g.V().hasLabel('Document').valueMap()

// Voir les chunks d'un document
g.V().has('Document', 'id', 'architecture')
  .out('HAS_CHUNK')
  .valueMap()

// Voir les annotations d'un chunk
g.V().has('Chunk', 'id', 'architecture_chunk_0001')
  .out('HAS_ANNOTATION')
  .valueMap()

// Trouver les chunks avec un mot-clé spécifique
g.V().hasLabel('Annotation')
  .has('type', 'keywords')
  .has('value', containing('data fabric'))
  .in('HAS_ANNOTATION')
  .valueMap()
```

## Requêtes OpenSearch

Vous pouvez interroger directement OpenSearch:

```bash
# Recherche par contenu
curl -X POST "https://your-domain.es.amazonaws.com/document-chunks/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "match": {
        "content": "data fabric"
      }
    }
  }'

# Recherche vectorielle
curl -X POST "https://your-domain.es.amazonaws.com/document-chunks/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "knn": {
        "embedding": {
          "vector": [0.123, -0.456, ...],
          "k": 5
        }
      }
    }
  }'
```
