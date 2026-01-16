# 🚀 Commencez ici !

Bienvenue dans le projet **RAG avec Docling, Cohere, Neptune et OpenSearch** !

## 📋 Ce que fait ce projet

Ce système permet de :

1. **Ingérer** des documents PDF
2. **Extraire** et découper le contenu intelligemment
3. **Enrichir** avec des annotations contextuelles
4. **Vectoriser** avec Cohere (embeddings multilingues haute qualité)
5. **Stocker** dans Neptune (graphe) et OpenSearch (vecteurs)
6. **Interroger** en langage naturel
7. **Générer** des prompts augmentés pour LLM

## 🎯 Démarrage rapide (5 minutes)

### 1️⃣ Obtenir une clé API Cohere

👉 [dashboard.cohere.com/api-keys](https://dashboard.cohere.com/api-keys)

```bash
export COHERE_API_KEY="L2sMb6fIeWfmLqzpDwe0PpScCBdpAINVODGNC7IK"
```

### 2️⃣ Installer

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3️⃣ Tester (sans AWS)

```bash
# Placer un PDF dans data/input/
python src/ingestion.py --input data/input/doc.pdf --dry-run
python src/query.py --question "Test?" --dry-run
```

### 4️⃣ Configurer AWS

Éditer `config.yaml` avec vos endpoints Neptune et OpenSearch.

### 5️⃣ Utiliser

```bash
# Ingérer
python src/ingestion.py --input data/input/doc.pdf

# Interroger
python src/query.py --question "Qu'est-ce qu'un Data Fabric?"

# Le prompt généré est dans data/output/
```

## 📚 Documentation

### Pour commencer

| Fichier | Description | Temps de lecture |
|---------|-------------|------------------|
| **[GETTING_STARTED.md](GETTING_STARTED.md)** | Guide de démarrage complet | 10 min |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Commandes essentielles | 5 min |
| **[COHERE_SETUP.md](COHERE_SETUP.md)** | Configuration Cohere | 5 min |

### Pour approfondir

| Fichier | Description | Temps de lecture |
|---------|-------------|------------------|
| **[README.md](README.md)** | Vue d'ensemble + architecture | 15 min |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Détails techniques | 20 min |
| **[EXAMPLES.md](EXAMPLES.md)** | Exemples d'utilisation | 10 min |

### En cas de problème

| Fichier | Description |
|---------|-------------|
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Guide de dépannage complet |
| **[MIGRATION_COHERE.md](MIGRATION_COHERE.md)** | Migration depuis v1.0.0 |
| **[CHANGELOG.md](CHANGELOG.md)** | Historique des versions |

## 🏗️ Architecture

```
PDF → Docling → Chunks → Cohere → Neptune + OpenSearch
                                      ↓
Question → Cohere → OpenSearch → Neptune → Prompt augmenté
```

Voir [architecture_diagram.svg](architecture_diagram.svg) pour le schéma complet.

## 💡 Cas d'usage

### Documentation technique
```bash
python src/ingestion.py --input data/input/technical_doc.pdf
python src/query.py --question "Comment configurer le système?"
```

### Base de connaissances
```bash
# Ingérer tous les documents
for file in data/input/*.pdf; do
    python src/ingestion.py --input "$file"
done

# Interroger
python src/query.py --question "Qu'est-ce qu'un Data Fabric?"
```

### Analyse de contrats
```bash
python src/ingestion.py --input data/input/contrat.pdf
python src/query.py --question "Quelles sont les clauses de résiliation?"
```

## 🔧 Technologies utilisées

- **Docling** : Extraction PDF intelligente
- **Cohere embed-multilingual-v3** : Embeddings haute qualité (1024 dim)
- **AWS Neptune** : Graphe de connaissances (Gremlin)
- **AWS OpenSearch** : Recherche vectorielle (KNN)
- **Python 3.8+** : Langage de programmation

## 💰 Coûts

### Cohere (Embeddings)
- 🆓 Plan gratuit : 100 requêtes/min
- 💰 Production : ~$0.10 / 1000 embeddings
- 📊 Exemple : 10 documents + 1000 questions = ~$0.30

### AWS
- Neptune : Variable selon instance
- OpenSearch : Variable selon instance

## ✨ Fonctionnalités

✅ Extraction PDF avec structure préservée  
✅ Chunking intelligent avec overlap  
✅ Annotations contextuelles automatiques  
✅ Embeddings multilingues haute qualité  
✅ Graphe de connaissances (relations)  
✅ Recherche vectorielle (similarité cosinus)  
✅ Filtrage Neptune optionnel  
✅ Mode dry-run (test sans AWS)  
✅ Prompts augmentés pour LLM  
✅ Support S3 (préparé)  

## 🎓 Parcours d'apprentissage

### Débutant (1 heure)
1. Lire [GETTING_STARTED.md](GETTING_STARTED.md)
2. Tester en mode dry-run
3. Lire [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

### Intermédiaire (2 heures)
1. Configurer AWS
2. Ingérer vos premiers documents
3. Tester des questions
4. Lire [EXAMPLES.md](EXAMPLES.md)

### Avancé (4 heures)
1. Lire [ARCHITECTURE.md](ARCHITECTURE.md)
2. Personnaliser les annotations
3. Optimiser les paramètres
4. Intégrer avec votre LLM

## 🤝 Support

### Documentation
- Tous les fichiers .md dans ce dossier
- Commentaires dans le code source

### Liens externes
- [Cohere Documentation](https://docs.cohere.com/)
- [AWS Neptune Documentation](https://docs.aws.amazon.com/neptune/)
- [AWS OpenSearch Documentation](https://docs.aws.amazon.com/opensearch-service/)

## 📁 Structure du projet

```
docling-rag-project/
├── 📖 Documentation (11 fichiers .md)
├── 🎨 architecture_diagram.svg
├── ⚙️ config.yaml
├── 📋 requirements.txt
├── 🚀 quick_start.sh / .bat
├── src/
│   ├── ingestion.py          # Script principal d'ingestion
│   ├── query.py              # Script principal d'interrogation
│   ├── docling_processor.py  # Traitement PDF
│   ├── embeddings.py         # Embeddings Cohere
│   ├── neptune_client.py     # Client Neptune
│   └── opensearch_client.py  # Client OpenSearch
└── data/
    ├── input/                # Vos PDFs ici
    └── output/               # Prompts générés ici
```

## 🎯 Prochaines étapes

1. ✅ Lire [GETTING_STARTED.md](GETTING_STARTED.md)
2. ✅ Obtenir une clé API Cohere
3. ✅ Tester en mode dry-run
4. ⬜ Configurer AWS
5. ⬜ Ingérer vos documents
6. ⬜ Tester des questions
7. ⬜ Intégrer avec votre LLM

## 🌟 Points forts

- ✅ **Qualité** : Cohere embed-multilingual-v3 (meilleur pour le français)
- ✅ **Complet** : Ingestion + Interrogation + Documentation
- ✅ **Flexible** : Mode dry-run, configuration YAML
- ✅ **Scalable** : AWS Neptune + OpenSearch
- ✅ **Documenté** : 11 fichiers de documentation
- ✅ **Prêt** : Code fonctionnel, exemples inclus

---

**Bon démarrage ! 🚀**

Pour toute question, consultez la documentation ou les commentaires dans le code.
