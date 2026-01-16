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


---

## Version 2.0.0 - Graphe de connaissances interconnecté

### 🎯 Nouveautés majeures

#### 1. Extraction automatique de topics
- **Identification de concepts** : Extraction automatique de concepts métier et mots-clés depuis chaque chunk
- **17 concepts métier prédéfinis** : assurance, remboursement, dentaire, santé, intervention, mutuelle, contrat, plafond, prestation, bénéficiaire, facture, paiement, compte, client, document, période, montant
- **Scoring intelligent** : Les concepts métier ont un score plus élevé que les mots-clés simples
- **Normalisation** : Les topics sont normalisés pour éviter les doublons (accents, casse, etc.)

#### 2. Graphe interconnecté via topics partagés
- **Nœuds Topic partagés** : Utilisation de `MERGE` au lieu de `CREATE` dans Neptune
- **Relations ABOUT** : Chaque chunk est lié aux topics qu'il contient
- **Liaison automatique** : Les documents partageant des topics sont automatiquement connectés
- **Navigation contextuelle** : Possibilité de naviguer entre documents via concepts communs

#### 3. Extraction de tables
- **Détection automatique** : Docling identifie les tables dans les PDFs
- **Extraction du contenu** : Le texte des cellules est extrait et formaté
- **Chunking des tables** : Les tables sont traitées comme des chunks spéciaux
- **Support multi-pages** : Gestion des tables réparties sur plusieurs pages

#### 4. Visualisation du graphe Neptune
- **Image PNG automatique** : Génération d'une visualisation à chaque ingestion
- **Couleurs par type** :
  - Rouge : Documents
  - Bleu : Chunks
  - Jaune : Topics (partagés)
  - Vert : Annotations
- **Layout hiérarchique** : Organisation claire sur 4 niveaux
- **Statistiques** : Affichage du nombre de nœuds et relations
- **Haute résolution** : Export en 300 DPI

#### 5. Visualisation interactive (Graph Viewer)
- **Outil HTML interactif** : `dry_run_output/viewer/generate_graph_viewer.py`
- **Lecture multi-CSV** : Parse tous les fichiers `neptune_inserts_*.csv`
- **Identification des topics partagés** : Détecte automatiquement les topics liés à plusieurs documents
- **Navigation interactive** : Zoom, pan, sélection de nœuds avec vis.js
- **Layouts multiples** : Hiérarchique, force-directed, circulaire
- **Statistiques en temps réel** : Nombre de documents, chunks, topics, relations
- **Focus automatique** : Bouton pour zoomer sur les topics partagés
- **Documentation complète** : README.md et USAGE_GUIDE.md dans le dossier viewer

#### 6. Traitement batch de plusieurs PDFs
- **Nommage intelligent** : Chaque document génère ses propres fichiers (`{doc_name}.csv`, `{doc_name}.png`)
- **Scripts batch** : `batch_ingestion.sh` (Linux/Mac) et `batch_ingestion.bat` (Windows)
- **Pas d'écrasement** : Les sorties précédentes sont préservées
- **Progression** : Affichage de la progression (1/N, 2/N, etc.)

### 🔧 Améliorations techniques

#### Extraction PDF
- **Correction majeure** : Utilisation de `doc.iterate_items()` au lieu de `for item in doc.body`
- **Fallback robuste** : Si `iterate_items()` ne retourne rien, utilisation de `export_to_text()`
- **Support des tables** : Méthode `_extract_table_text()` pour extraire le contenu des tables
- **Gestion des pages** : Meilleure détection du numéro de page via `prov_item.page_no`

#### Pipeline d'ingestion
- **6 étapes** au lieu de 5 :
  1. Extraction et chunking avec Docling
  2. Génération des embeddings
  3. **🆕 Extraction des topics et concepts**
  4. Insertion dans Neptune
  5. Insertion dans OpenSearch
  6. Export/Visualisation
- **Logs améliorés** : Affichage du nombre de topics identifiés

#### Configuration
- **Modèle Cohere corrigé** : `embed-multilingual-v3.0` au lieu de `embed-multilingual-v3`
- **Dépendances ajoutées** : `networkx>=3.0` et `matplotlib>=3.7.0`

### 📚 Documentation

#### Nouveaux fichiers
- **TOPICS_LINKING.md** : Guide complet sur la liaison des documents via topics (exemples, requêtes Cypher, cas d'usage)
- **BATCH_PROCESSING.md** : Guide pour le traitement de plusieurs PDFs (scripts, organisation, dépannage)
- **WHATS_NEW_V2.md** : Résumé convivial des nouveautés de la v2.0
- **src/topic_extractor.py** : Module d'extraction de topics (300+ lignes)
- **dry_run_output/viewer/generate_graph_viewer.py** : Générateur de visualisation interactive (600+ lignes)
- **dry_run_output/viewer/README.md** : Documentation du Graph Viewer
- **dry_run_output/viewer/USAGE_GUIDE.md** : Guide d'utilisation détaillé du viewer

#### Fichiers mis à jour
- **README.md** : Ajout section "Nouveautés v2.0", mise à jour architecture et modèle de données
- **START_HERE.md** : Mise à jour des fonctionnalités et points forts
- **CHANGELOG.md** : Ce fichier

### 🐛 Corrections de bugs

1. **0 chunks générés** : Le code utilisait une mauvaise méthode pour itérer sur `doc.body`
   - Avant : `for item in doc.body` → retournait des tuples
   - Après : `for item, level in doc.iterate_items()` → retourne les vrais éléments

2. **Tables non extraites** : Les tables de la page 2 n'étaient pas traitées
   - Ajout de la détection et extraction des tables via `doc.tables`
   - Méthode `_extract_table_text()` pour formater le contenu

3. **Import manquant** : `NameError: name 'Set' is not defined`
   - Ajout de `Set` dans les imports de `typing`

4. **Fichiers écrasés** : En mode dry-run, les fichiers étaient écrasés
   - Ajout du nom du document dans les noms de fichiers

### 📊 Statistiques

- **Fichiers ajoutés** : 3
  - `src/topic_extractor.py` (300+ lignes)
  - `TOPICS_LINKING.md` (200+ lignes)
  - `BATCH_PROCESSING.md` (150+ lignes)

- **Fichiers modifiés** : 7
  - `src/ingestion.py` (+200 lignes)
  - `src/docling_processor.py` (+50 lignes)
  - `config.yaml` (1 ligne)
  - `requirements.txt` (+2 lignes)
  - `README.md` (+100 lignes)
  - `START_HERE.md` (+30 lignes)
  - `CHANGELOG.md` (ce fichier)

- **Lignes de code ajoutées** : ~800
- **Topics extraits (exemple)** : 17 topics uniques depuis un document de 2 pages
- **Chunks générés (exemple)** : 6 chunks (4 texte + 2 tables)

### 🎓 Exemples de requêtes Neptune

#### Trouver tous les documents sur un topic
```cypher
MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)-[:ABOUT]->(t:Topic {name: 'assurance'})
RETURN DISTINCT d.title
```

#### Trouver les documents similaires
```cypher
MATCH (d1:Document)-[:HAS_CHUNK]->(c1:Chunk)-[:ABOUT]->(t:Topic)<-[:ABOUT]-(c2:Chunk)<-[:HAS_CHUNK]-(d2:Document)
WHERE d1 <> d2
WITH d1, d2, COUNT(DISTINCT t) as common_topics
WHERE common_topics >= 3
RETURN d1.title, d2.title, common_topics
ORDER BY common_topics DESC
```

#### Trouver les topics les plus populaires
```cypher
MATCH (c:Chunk)-[:ABOUT]->(t:Topic)
RETURN t.name, t.type, COUNT(c) as chunk_count
ORDER BY chunk_count DESC
LIMIT 10
```

### 🚀 Migration depuis v1.x

1. Mettre à jour les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

2. Mettre à jour `config.yaml` :
   ```yaml
   embeddings:
     model: "embed-multilingual-v3.0"  # Ajouter .0
   ```

3. Réingérer les documents existants pour bénéficier des topics :
   ```bash
   python src/ingestion.py --input data/input/document.pdf --dry-run
   ```

4. Les anciens documents dans Neptune ne seront pas automatiquement liés aux nouveaux topics. Pour une migration complète, il faudrait :
   - Supprimer les anciens documents de Neptune
   - Réingérer tous les documents avec la v2.0

### ⚠️ Breaking Changes

- **Aucun** : La v2.0 est rétrocompatible avec la v1.x
- Les anciens documents continuent de fonctionner
- Les nouveaux documents bénéficient automatiquement des topics

### 🔮 Prochaines étapes

- [ ] Extraction d'entités nommées (personnes, organisations, lieux)
- [ ] Liens de similarité sémantique entre chunks
- [ ] Interface web pour visualiser le graphe
- [ ] Support de plus de types de documents (Word, Excel, etc.)
- [ ] Amélioration de l'extraction de topics avec NLP avancé
- [ ] Cache des embeddings pour éviter les recalculs

---

**Date de release** : 16 janvier 2026  
**Contributeurs** : Équipe de développement  
**Compatibilité** : Python 3.8+, Neptune, OpenSearch, Cohere API
