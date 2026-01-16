# Résumé du projet

## Vue d'ensemble

Ce projet implémente un système RAG (Retrieval-Augmented Generation) complet utilisant:
- **Docling** pour l'extraction et le chunking de PDFs
- **Cohere embed-multilingual-v3** pour les embeddings multilingues (1024 dimensions)
- **Neptune** pour le graphe de connaissances (métadonnées et annotations)
- **OpenSearch** pour la recherche vectorielle (embeddings)

## Structure créée

```
docling-rag-project/
├── README.md                    # Documentation principale avec architecture
├── GETTING_STARTED.md           # Guide de démarrage rapide
├── COHERE_SETUP.md              # Configuration Cohere détaillée
├── QUICK_REFERENCE.md           # Référence rapide des commandes
├── ARCHITECTURE.md              # Architecture détaillée du système
├── EXAMPLES.md                  # Exemples d'utilisation complets
├── TROUBLESHOOTING.md           # Guide de dépannage
├── PROJECT_SUMMARY.md           # Ce fichier
├── requirements.txt             # Dépendances Python
├── config.yaml                  # Configuration (à personnaliser)
├── .gitignore                   # Fichiers à ignorer
├── architecture_diagram.svg     # Diagramme d'architecture
├── quick_start.sh               # Script de démarrage (Linux/Mac)
├── quick_start.bat              # Script de démarrage (Windows)
│
├── src/                         # Code source
│   ├── __init__.py
│   ├── ingestion.py            # Script d'ingestion principal
│   ├── query.py                # Script d'interrogation principal
│   ├── docling_processor.py   # Traitement Docling
│   ├── neptune_client.py       # Client Neptune
│   ├── opensearch_client.py   # Client OpenSearch
│   └── embeddings.py           # Génération d'embeddings
│
├── data/
│   ├── input/                  # PDFs à traiter
│   │   └── README.md
│   └── output/                 # Prompts générés
│
└── dry_run_output/             # Fichiers CSV en mode dry-run
```

## Fonctionnalités implémentées

### Script d'ingestion (ingestion.py)

✅ **Étape 1** : Extraction et chunking avec Docling
- Parse les PDFs locaux (compatible S3 pour évolution future)
- Découpe intelligente en chunks sémantiques
- Préserve la structure du document (pages, types d'éléments)

✅ **Étape 2** : Annotations contextuelles
- Type d'élément (paragraph, title, table, etc.)
- Localisation (numéro de page)
- Catégorie de longueur
- Extraction de mots-clés

✅ **Étape 3** : Insertion dans Neptune
- Création de nœuds Document, Chunk, Annotation
- Relations HAS_CHUNK, HAS_ANNOTATION
- Support du mode dry-run (génération CSV)

✅ **Étape 4** : Génération d'embeddings
- Modèle Cohere embed-multilingual-v3 (1024 dimensions)
- Optimisé pour le français et 100+ langues
- Traitement par batch (jusqu'à 96 textes)
- Input type "search_document" pour l'indexation
- Vectorisation de tous les chunks

✅ **Étape 5** : Indexation dans OpenSearch
- Index KNN avec HNSW
- Métrique de similarité cosinus
- Support du mode dry-run (génération CSV)

### Script d'interrogation (query.py)

✅ **Étape 1** : Embedding de la question
- Même modèle Cohere que l'ingestion
- Input type "search_query" pour les requêtes
- Vectorisation de la question utilisateur

✅ **Étape 2** : Recherche de similarité
- Recherche KNN dans OpenSearch
- Top-K chunks les plus pertinents
- Scores de similarité cosinus

✅ **Étape 3** : Filtrage Neptune (optionnel)
- Réduction de l'espace de recherche via le graphe
- Identification des chunks liés

✅ **Étape 4** : Récupération des annotations
- Enrichissement avec contexte Neptune
- Annotations pour chaque chunk trouvé

✅ **Étape 5** : Construction du prompt augmenté
- Format structuré pour LLM
- Contexte + Annotations + Question
- Export dans fichier texte

✅ **Mode dry-run**
- Génération de CSV avec requêtes Cypher (Neptune)
- Génération de CSV avec requêtes API (OpenSearch)
- Pas d'exécution réelle

## Modules créés

### docling_processor.py
- Classe `DoclingProcessor`
- Méthodes :
  - `process_pdf()` : Parse un PDF
  - `create_chunks()` : Crée des chunks avec métadonnées
  - `_generate_annotations()` : Génère les annotations contextuelles

### embeddings.py
- Classe `EmbeddingGenerator`
- Support Cohere et sentence-transformers
- Méthodes :
  - `generate_embedding()` : Embedding d'un texte (avec input_type)
  - `generate_embeddings_batch()` : Batch d'embeddings (jusqu'à 96)
  - `compute_similarity()` : Similarité cosinus

### neptune_client.py
- Classe `NeptuneClient`
- Méthodes :
  - `connect()` : Connexion à Neptune
  - `insert_document()` : Insère un document
  - `insert_chunk()` : Insère un chunk avec relations
  - `insert_annotation()` : Insère une annotation
  - `get_chunk_annotations()` : Récupère les annotations
  - `get_related_chunks()` : Trouve les chunks liés

### opensearch_client.py
- Classe `OpenSearchClient`
- Méthodes :
  - `create_index()` : Crée l'index KNN
  - `index_chunk()` : Indexe un chunk
  - `search_similar()` : Recherche par similarité
  - `bulk_index()` : Indexation en batch

## Configuration

Le fichier `config.yaml` permet de configurer :
- Endpoints Neptune et OpenSearch
- Paramètres d'authentification (IAM ou credentials)
- Provider d'embeddings (Cohere ou sentence-transformers)
- Modèle d'embeddings et dimension (1024 pour Cohere)
- Clé API Cohere (ou variable d'environnement)
- Paramètres de chunking (taille, overlap)
- Paramètres de recherche (top_k, seuil)
- Chemins de sortie

## Mode dry-run

Le mode dry-run permet de tester le système sans connexion AWS :
- Génère des fichiers CSV avec toutes les requêtes
- Permet de valider la logique avant déploiement
- Utile pour le développement et le debugging

### Fichiers générés en dry-run

**Ingestion** :
- `dry_run_output/neptune_inserts.csv` : Requêtes Cypher
- `dry_run_output/opensearch_inserts.csv` : Requêtes API OpenSearch

**Interrogation** :
- `dry_run_output/neptune_queries.csv` : Requêtes Cypher
- `dry_run_output/opensearch_queries.csv` : Requêtes API OpenSearch

## Utilisation

### Installation
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configurer Cohere
export COHERE_API_KEY="votre-cle-api"
```

**Note** : Obtenez votre clé API sur [dashboard.cohere.com/api-keys](https://dashboard.cohere.com/api-keys)

### Configuration
Éditer `config.yaml` avec vos endpoints AWS et vérifier la configuration Cohere

### Ingestion
```bash
# Mode dry-run (test)
python src/ingestion.py --input data/input/document.pdf --dry-run

# Mode réel
python src/ingestion.py --input data/input/document.pdf
```

### Interrogation
```bash
# Mode dry-run (test)
python src/query.py --question "Votre question?" --dry-run

# Mode réel
python src/query.py --question "Votre question?"

# Avec filtrage Neptune
python src/query.py --question "Votre question?" --use-neptune-filter
```

## Documentation

- **README.md** : Documentation principale avec architecture visuelle
- **GETTING_STARTED.md** : Guide de démarrage rapide
- **COHERE_SETUP.md** : Configuration Cohere détaillée (clé API, tarifs, alternatives)
- **QUICK_REFERENCE.md** : Référence rapide des commandes
- **ARCHITECTURE.md** : Détails techniques (modèles de données, algorithmes)
- **EXAMPLES.md** : Exemples d'utilisation avec sorties console
- **TROUBLESHOOTING.md** : Guide de dépannage complet

## Évolutions futures

Le code est préparé pour :
- ✅ Support S3 (structure en place, à activer)
- ✅ Batch processing (méthodes bulk disponibles)
- ✅ Différents modèles d'embeddings (configurable)
- ✅ Filtrage Neptune avancé (méthode get_related_chunks)

## Points d'attention

1. **Configuration AWS** : Nécessite des endpoints Neptune et OpenSearch valides
2. **Clé API Cohere** : Requise pour les embeddings (gratuit pour tests, ~$0.10/1000 embeddings en production)
3. **Authentification** : IAM recommandé pour la production
4. **Coûts** : Neptune, OpenSearch et Cohere sont des services payants
5. **Dimension** : 1024 dimensions (Cohere) vs 384 (sentence-transformers)
6. **Sécurité** : Ne pas commiter config.yaml avec credentials ou clé API

## Tests

Pour tester sans AWS :
```bash
# Test complet en dry-run
python src/ingestion.py --input data/input/test.pdf --dry-run
python src/query.py --question "Test question?" --dry-run

# Vérifier les CSV générés
ls -la dry_run_output/
```

## Support

En cas de problème :
1. Consulter TROUBLESHOOTING.md
2. Vérifier les logs
3. Tester en mode dry-run
4. Vérifier la configuration AWS

## Licence

MIT
