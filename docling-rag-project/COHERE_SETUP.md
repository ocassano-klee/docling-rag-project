# Configuration Cohere Embeddings

## Vue d'ensemble

Ce projet utilise **Cohere embed-multilingual-v3**, un modèle d'embeddings de haute qualité optimisé pour le multilinguisme, incluant le français.

### Avantages de Cohere embed-multilingual-v3

- ✅ **Multilingue** : Excellent support pour le français et 100+ langues
- ✅ **Haute qualité** : Performance supérieure aux modèles open-source
- ✅ **Dimension 1024** : Représentations vectorielles riches
- ✅ **Optimisé pour RAG** : Deux modes (search_document et search_query)
- ✅ **Scalable** : API cloud, pas besoin de GPU local

### Caractéristiques techniques

- **Modèle** : `embed-multilingual-v3`
- **Dimension** : 1024
- **Langues** : 100+ (dont français, anglais, espagnol, etc.)
- **Batch size** : Jusqu'à 96 textes par requête
- **Input types** :
  - `search_document` : Pour indexer les documents
  - `search_query` : Pour les requêtes utilisateur

## Installation

### 1. Installer la bibliothèque Cohere

```bash
pip install cohere>=5.0.0
```

### 2. Obtenir une clé API

1. Créer un compte sur [Cohere](https://cohere.com/)
2. Aller dans [Dashboard > API Keys](https://dashboard.cohere.com/api-keys)
3. Créer une nouvelle clé API (Production ou Trial)

### 3. Configurer la clé API

**Option A : Variable d'environnement (recommandé)**

```bash
# Linux/Mac
export COHERE_API_KEY="votre-cle-api"

# Windows CMD
set COHERE_API_KEY=votre-cle-api

# Windows PowerShell
$env:COHERE_API_KEY="votre-cle-api"
```

**Option B : Fichier de configuration**

Éditer `config.yaml` :

```yaml
embeddings:
  provider: "cohere"
  model: "embed-multilingual-v3"
  dimension: 1024
  batch_size: 96
  api_key: "votre-cle-api"  # ⚠️ Ne pas commiter ce fichier !
```

**Option C : Fichier .env**

Créer un fichier `.env` à la racine :

```bash
COHERE_API_KEY=votre-cle-api
```

Puis charger avec python-dotenv :

```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()
```

## Configuration

### Configuration de base

```yaml
# config.yaml
embeddings:
  provider: "cohere"
  model: "embed-multilingual-v3"
  dimension: 1024
  batch_size: 96
  api_key: ""  # Laisser vide si utilisation de variable d'environnement
```

### Configuration OpenSearch

Mettre à jour la dimension dans OpenSearch :

```yaml
opensearch:
  endpoint: "https://your-domain.es.amazonaws.com"
  index_name: "document-chunks"
```

L'index sera créé automatiquement avec la bonne dimension (1024).

## Utilisation

### Ingestion de documents

```bash
# Avec variable d'environnement
export COHERE_API_KEY="votre-cle"
python src/ingestion.py --input data/input/document.pdf

# Ou avec clé dans config.yaml
python src/ingestion.py --input data/input/document.pdf
```

Le système utilisera automatiquement `input_type="search_document"` pour l'indexation.

### Interrogation

```bash
python src/query.py --question "Qu'est-ce qu'un Data Fabric?"
```

Le système utilisera automatiquement `input_type="search_query"` pour les questions.

## Différences avec sentence-transformers

### Avant (sentence-transformers)

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode("texte")  # 384 dimensions
```

### Après (Cohere)

```python
import cohere

client = cohere.Client(api_key)
response = client.embed(
    texts=["texte"],
    model="embed-multilingual-v3",
    input_type="search_document"
)
embedding = response.embeddings.float[0]  # 1024 dimensions
```

## Tarification Cohere

### Plan gratuit (Trial)

- ✅ 100 requêtes API / minute
- ✅ Idéal pour développement et tests
- ✅ Pas de carte de crédit requise

### Plan Production

- 💰 ~$0.10 / 1000 embeddings
- 📊 Exemple : 10,000 chunks = ~$1.00
- 🚀 Rate limits plus élevés

### Estimation de coûts

```
Document de 100 pages
→ ~200 chunks
→ ~$0.02 pour l'ingestion

1000 questions
→ 1000 embeddings de requête
→ ~$0.10

Total pour un document + 1000 questions : ~$0.12
```

## Performance

### Vitesse

- **API Cohere** : ~100-200 embeddings/sec
- **Batch de 96** : Optimal pour throughput
- **Latence** : ~100-300ms par requête

### Qualité

Cohere embed-multilingual-v3 surpasse généralement :
- sentence-transformers/all-MiniLM-L6-v2
- sentence-transformers/paraphrase-multilingual-mpnet-base-v2

Particulièrement pour :
- ✅ Textes en français
- ✅ Textes multilingues
- ✅ Recherche sémantique cross-lingue

## Comparaison des modèles

| Modèle | Dimension | Langues | Qualité | Coût | Local |
|--------|-----------|---------|---------|------|-------|
| **Cohere embed-multilingual-v3** | 1024 | 100+ | ⭐⭐⭐⭐⭐ | API | ❌ |
| all-MiniLM-L6-v2 | 384 | EN | ⭐⭐⭐ | Gratuit | ✅ |
| paraphrase-multilingual-mpnet | 768 | 50+ | ⭐⭐⭐⭐ | Gratuit | ✅ |
| OpenAI text-embedding-ada-002 | 1536 | 100+ | ⭐⭐⭐⭐⭐ | API | ❌ |

## Dépannage

### Erreur : "API key not found"

**Solution** :

```bash
# Vérifier la variable d'environnement
echo $COHERE_API_KEY

# Si vide, définir
export COHERE_API_KEY="votre-cle"
```

### Erreur : "Rate limit exceeded"

**Cause** : Trop de requêtes

**Solutions** :

1. Réduire le batch_size :
```yaml
embeddings:
  batch_size: 48  # Au lieu de 96
```

2. Ajouter des pauses :
```python
import time
time.sleep(1)  # Entre les batchs
```

3. Passer au plan Production

### Erreur : "Invalid API key"

**Solutions** :

1. Vérifier la clé sur [dashboard.cohere.com](https://dashboard.cohere.com/api-keys)
2. Régénérer une nouvelle clé
3. Vérifier qu'il n'y a pas d'espaces dans la clé

### Embeddings de mauvaise qualité

**Solutions** :

1. Vérifier que vous utilisez bien `embed-multilingual-v3` (pas v2)
2. S'assurer que `input_type` est correct :
   - `search_document` pour l'ingestion
   - `search_query` pour les questions

## Migration depuis sentence-transformers

### Étape 1 : Mettre à jour requirements.txt

```bash
# Remplacer
sentence-transformers>=2.2.0

# Par
cohere>=5.0.0
```

### Étape 2 : Mettre à jour config.yaml

```yaml
embeddings:
  provider: "cohere"  # Ajouter
  model: "embed-multilingual-v3"  # Changer
  dimension: 1024  # Changer de 384 à 1024
  batch_size: 96  # Changer de 32 à 96
  api_key: ""  # Ajouter
```

### Étape 3 : Recréer l'index OpenSearch

```python
from opensearch_client import OpenSearchClient

client = OpenSearchClient(...)

# Supprimer l'ancien index
client.client.indices.delete(index="document-chunks")

# Créer le nouveau avec dimension 1024
client.create_index(dimension=1024)
```

### Étape 4 : Ré-ingérer les documents

```bash
# Tous les documents doivent être ré-ingérés avec les nouveaux embeddings
python src/ingestion.py --input data/input/document.pdf
```

## Alternatives

Si vous préférez rester en local (sans API) :

### Option 1 : sentence-transformers multilingue

```yaml
embeddings:
  provider: "sentence-transformers"
  model: "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
  dimension: 768
  batch_size: 32
```

### Option 2 : Modèle français spécialisé

```yaml
embeddings:
  provider: "sentence-transformers"
  model: "dangvantuan/sentence-camembert-large"
  dimension: 768
  batch_size: 32
```

## Ressources

- [Documentation Cohere Embed](https://docs.cohere.com/docs/embeddings)
- [Cohere Dashboard](https://dashboard.cohere.com/)
- [Cohere Pricing](https://cohere.com/pricing)
- [Guide des modèles d'embeddings](https://txt.cohere.com/introducing-embed-v3/)

## Support

Pour des questions sur Cohere :
- [Discord Cohere](https://discord.gg/cohere)
- [Support Cohere](https://cohere.com/support)
