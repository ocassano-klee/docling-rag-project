# Référence rapide

## 🚀 Commandes essentielles

### Installation

```bash
# Créer l'environnement
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer
pip install -r requirements.txt

# Configurer Cohere
export COHERE_API_KEY="votre-cle-api"
```

### Ingestion

```bash
# Mode dry-run (test sans AWS)
python src/ingestion.py --input data/input/doc.pdf --dry-run

# Mode réel
python src/ingestion.py --input data/input/doc.pdf

# Plusieurs documents
for file in data/input/*.pdf; do
    python src/ingestion.py --input "$file"
done
```

### Interrogation

```bash
# Mode dry-run
python src/query.py --question "Votre question?" --dry-run

# Mode réel
python src/query.py --question "Votre question?"

# Avec filtrage Neptune
python src/query.py --question "Votre question?" --use-neptune-filter
```

## ⚙️ Configuration rapide

### config.yaml minimal

```yaml
neptune:
  endpoint: "cluster.neptune.amazonaws.com"
  port: 8182
  region: "eu-west-1"

opensearch:
  endpoint: "https://domain.es.amazonaws.com"
  index_name: "document-chunks"
  region: "eu-west-1"

embeddings:
  provider: "cohere"
  model: "embed-multilingual-v3"
  dimension: 1024
  batch_size: 96
  api_key: ""  # Ou via COHERE_API_KEY

docling:
  chunk_size: 512
  chunk_overlap: 50
  min_chunk_size: 100

query:
  top_k: 5
  similarity_threshold: 0.7
```

## 📊 Modèle Cohere

### Caractéristiques

- **Modèle** : embed-multilingual-v3
- **Dimension** : 1024
- **Langues** : 100+ (excellent français)
- **Batch max** : 96 textes
- **Tarif** : ~$0.10 / 1000 embeddings

### Obtenir une clé API

1. [cohere.com](https://cohere.com/) → Créer un compte
2. [dashboard.cohere.com/api-keys](https://dashboard.cohere.com/api-keys) → Nouvelle clé
3. `export COHERE_API_KEY="votre-cle"`

### Input types

```python
# Pour indexer les documents
input_type="search_document"

# Pour les requêtes utilisateur
input_type="search_query"
```

## 🗂️ Structure des fichiers

```
docling-rag-project/
├── src/
│   ├── ingestion.py          # Script principal d'ingestion
│   ├── query.py              # Script principal d'interrogation
│   ├── docling_processor.py  # Traitement PDF
│   ├── embeddings.py         # Embeddings Cohere
│   ├── neptune_client.py     # Client Neptune
│   └── opensearch_client.py  # Client OpenSearch
├── data/
│   ├── input/                # PDFs à traiter
│   └── output/               # Prompts générés
├── dry_run_output/           # CSV en mode dry-run
└── config.yaml               # Configuration
```

## 🔍 Vérifications rapides

### Tester la connexion Cohere

```python
import cohere
import os

client = cohere.Client(os.getenv("COHERE_API_KEY"))
response = client.embed(
    texts=["test"],
    model="embed-multilingual-v3",
    input_type="search_document"
)
print(f"Dimension: {len(response.embeddings.float[0])}")  # 1024
```

### Vérifier Neptune

```bash
aws neptune describe-db-clusters --query 'DBClusters[*].[DBClusterIdentifier,Endpoint,Status]'
```

### Vérifier OpenSearch

```bash
curl -X GET "https://your-domain.es.amazonaws.com/_cat/indices?v"
```

## 🐛 Dépannage express

### Erreur : "API key not found"

```bash
export COHERE_API_KEY="votre-cle"
echo $COHERE_API_KEY  # Vérifier
```

### Erreur : "Connection refused" (Neptune)

```bash
# Vérifier endpoint
aws neptune describe-db-clusters

# Vérifier security group (port 8182)
```

### Erreur : "Index not found" (OpenSearch)

```python
from opensearch_client import OpenSearchClient
client = OpenSearchClient(...)
client.create_index(dimension=1024)
```

### Erreur : "Rate limit exceeded" (Cohere)

```yaml
# Réduire batch_size dans config.yaml
embeddings:
  batch_size: 48  # Au lieu de 96
```

## 📈 Workflow typique

```
1. Configuration
   └─ Configurer config.yaml + COHERE_API_KEY

2. Test (dry-run)
   ├─ python src/ingestion.py --input doc.pdf --dry-run
   └─ python src/query.py --question "test?" --dry-run

3. Ingestion
   └─ python src/ingestion.py --input doc.pdf

4. Interrogation
   └─ python src/query.py --question "Votre question?"

5. Utilisation du prompt
   └─ Copier data/output/prompt_*.txt → Envoyer au LLM
```

## 📚 Documentation

| Fichier | Description |
|---------|-------------|
| [README.md](README.md) | Vue d'ensemble + architecture |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Guide de démarrage |
| [COHERE_SETUP.md](COHERE_SETUP.md) | Configuration Cohere détaillée |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Architecture technique |
| [EXAMPLES.md](EXAMPLES.md) | Exemples d'utilisation |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Guide de dépannage |

## 💡 Astuces

### Performance

```bash
# Traiter en parallèle (attention aux rate limits Cohere)
parallel -j 2 python src/ingestion.py --input {} ::: data/input/*.pdf
```

### Coûts Cohere

```
100 pages PDF → ~200 chunks → ~$0.02
1000 questions → ~$0.10
Total : ~$0.12 pour un document + 1000 questions
```

### Qualité des résultats

```yaml
# Augmenter pour plus de contexte
query:
  top_k: 10
  
# Augmenter pour plus de précision
docling:
  chunk_size: 256
```

## 🔗 Liens utiles

- [Cohere Dashboard](https://dashboard.cohere.com/)
- [Cohere Docs](https://docs.cohere.com/docs/embeddings)
- [AWS Neptune Docs](https://docs.aws.amazon.com/neptune/)
- [AWS OpenSearch Docs](https://docs.aws.amazon.com/opensearch-service/)
