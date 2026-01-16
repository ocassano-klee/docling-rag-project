# Changelog

## Version 1.1.0 - Migration vers Cohere Embeddings

### 🎯 Changements majeurs

#### Modèle d'embeddings

**Avant** : sentence-transformers/all-MiniLM-L6-v2
- Dimension : 384
- Local (CPU/GPU)
- Gratuit
- Qualité moyenne pour le français

**Après** : Cohere embed-multilingual-v3
- Dimension : 1024
- API cloud
- ~$0.10 / 1000 embeddings
- Excellente qualité pour le français et 100+ langues

### 📝 Fichiers modifiés

#### requirements.txt
```diff
- sentence-transformers>=2.2.0
+ cohere>=5.0.0
```

#### config.yaml
```diff
  embeddings:
-   model: "sentence-transformers/all-MiniLM-L6-v2"
-   dimension: 384
-   batch_size: 32
+   provider: "cohere"
+   model: "embed-multilingual-v3"
+   dimension: 1024
+   batch_size: 96
+   api_key: ""
```

#### src/embeddings.py
- ✅ Ajout du support Cohere
- ✅ Gestion des input_types (`search_document` et `search_query`)
- ✅ Batch processing jusqu'à 96 textes
- ✅ Fallback sur sentence-transformers si besoin
- ✅ Gestion de la clé API (paramètre ou variable d'environnement)

#### src/ingestion.py
```diff
  self.embeddings = EmbeddingGenerator(
-     model_name=self.config['embeddings']['model']
+     provider=self.config['embeddings']['provider'],
+     model_name=self.config['embeddings']['model'],
+     api_key=self.config['embeddings'].get('api_key')
  )
```

#### src/query.py
```diff
  self.embeddings = EmbeddingGenerator(
-     model_name=self.config['embeddings']['model']
+     provider=self.config['embeddings']['provider'],
+     model_name=self.config['embeddings']['model'],
+     api_key=self.config['embeddings'].get('api_key')
  )
  
  # Utilisation de input_type pour les requêtes
- question_embedding = self.embeddings.generate_embedding(question)
+ question_embedding = self.embeddings.generate_embedding(question, input_type="search_query")
```

### 📚 Documentation ajoutée

#### Nouveaux fichiers
- ✅ **COHERE_SETUP.md** : Guide complet de configuration Cohere
  - Obtention de la clé API
  - Configuration (3 méthodes)
  - Tarification et coûts
  - Comparaison avec alternatives
  - Dépannage spécifique Cohere
  - Migration depuis sentence-transformers

- ✅ **QUICK_REFERENCE.md** : Référence rapide
  - Commandes essentielles
  - Configuration minimale
  - Vérifications rapides
  - Dépannage express

#### Fichiers mis à jour
- ✅ **README.md** : Mention de Cohere et lien vers COHERE_SETUP.md
- ✅ **ARCHITECTURE.md** : Section embeddings mise à jour avec Cohere
- ✅ **GETTING_STARTED.md** : Ajout de l'étape configuration Cohere
- ✅ **PROJECT_SUMMARY.md** : Mise à jour des caractéristiques

### 🔧 Nouvelles fonctionnalités

#### Input types Cohere
```python
# Pour l'ingestion (documents)
embeddings.generate_embedding(text, input_type="search_document")

# Pour les requêtes (questions)
embeddings.generate_embedding(text, input_type="search_query")
```

#### Support multi-provider
```yaml
# Cohere (par défaut)
embeddings:
  provider: "cohere"
  model: "embed-multilingual-v3"

# Ou sentence-transformers (fallback)
embeddings:
  provider: "sentence-transformers"
  model: "sentence-transformers/all-MiniLM-L6-v2"
```

### ⚙️ Configuration requise

#### Variables d'environnement
```bash
export COHERE_API_KEY="votre-cle-api"
```

#### Ou dans config.yaml
```yaml
embeddings:
  api_key: "votre-cle-api"
```

### 🔄 Migration depuis version 1.0.0

#### Étape 1 : Mettre à jour les dépendances
```bash
pip install cohere>=5.0.0
```

#### Étape 2 : Obtenir une clé API Cohere
1. Créer un compte sur [cohere.com](https://cohere.com/)
2. Obtenir une clé sur [dashboard.cohere.com/api-keys](https://dashboard.cohere.com/api-keys)
3. `export COHERE_API_KEY="votre-cle"`

#### Étape 3 : Mettre à jour config.yaml
```yaml
embeddings:
  provider: "cohere"
  model: "embed-multilingual-v3"
  dimension: 1024
  batch_size: 96
  api_key: ""
```

#### Étape 4 : Recréer l'index OpenSearch
```python
from opensearch_client import OpenSearchClient

client = OpenSearchClient(...)
client.client.indices.delete(index="document-chunks")
client.create_index(dimension=1024)
```

#### Étape 5 : Ré-ingérer les documents
```bash
# Tous les documents doivent être ré-ingérés
python src/ingestion.py --input data/input/document.pdf
```

### 📊 Comparaison des performances

| Métrique | v1.0.0 (sentence-transformers) | v1.1.0 (Cohere) |
|----------|-------------------------------|-----------------|
| Dimension | 384 | 1024 |
| Qualité (français) | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Vitesse | ~1000/sec (CPU) | ~100-200/sec (API) |
| Coût | Gratuit | ~$0.10 / 1000 |
| Infrastructure | Local (GPU recommandé) | Cloud (API) |
| Multilingue | Limité | Excellent (100+ langues) |

### 💰 Estimation des coûts

#### Ingestion
- 100 pages PDF → ~200 chunks → ~$0.02
- 1000 pages PDF → ~2000 chunks → ~$0.20

#### Interrogation
- 1000 questions → ~$0.10

#### Total exemple
- 10 documents (1000 pages) + 1000 questions → ~$0.30

### ⚠️ Breaking Changes

1. **Dimension des embeddings** : 384 → 1024
   - Nécessite de recréer l'index OpenSearch
   - Nécessite de ré-ingérer tous les documents

2. **Configuration** : Nouveau format
   - Ajout du champ `provider`
   - Ajout du champ `api_key`
   - Changement de `batch_size` (32 → 96)

3. **Dépendances** : Nouvelle bibliothèque
   - `sentence-transformers` → `cohere`

### ✅ Rétrocompatibilité

Le code supporte toujours sentence-transformers en fallback :

```yaml
embeddings:
  provider: "sentence-transformers"
  model: "sentence-transformers/all-MiniLM-L6-v2"
  dimension: 384
  batch_size: 32
```

### 🐛 Corrections

- Aucune correction de bug dans cette version (nouvelle fonctionnalité)

### 📖 Documentation

7 fichiers de documentation au total :
1. README.md (mis à jour)
2. GETTING_STARTED.md (mis à jour)
3. COHERE_SETUP.md (nouveau)
4. QUICK_REFERENCE.md (nouveau)
5. ARCHITECTURE.md (mis à jour)
6. EXAMPLES.md (inchangé)
7. TROUBLESHOOTING.md (inchangé)

### 🎓 Prochaines étapes recommandées

1. ✅ Lire [COHERE_SETUP.md](COHERE_SETUP.md)
2. ✅ Obtenir une clé API Cohere
3. ✅ Tester en mode dry-run
4. ✅ Migrer vos données existantes
5. ⬜ Évaluer la qualité des résultats
6. ⬜ Optimiser les paramètres si nécessaire

---

## Version 1.0.0 - Version initiale

### Fonctionnalités

- ✅ Ingestion de PDFs avec Docling
- ✅ Chunking intelligent
- ✅ Annotations contextuelles
- ✅ Stockage dans Neptune
- ✅ Embeddings avec sentence-transformers
- ✅ Indexation dans OpenSearch
- ✅ Recherche de similarité
- ✅ Génération de prompts augmentés
- ✅ Mode dry-run
- ✅ Documentation complète
