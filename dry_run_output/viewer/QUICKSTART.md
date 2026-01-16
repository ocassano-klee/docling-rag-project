# 🚀 Quick Start - Graph Viewer

## En 3 étapes simples

### 1️⃣ Générer les données

Traitez au moins 2 documents en mode dry-run :

```bash
python src/ingestion.py --file data/input/olivia_ortho_1.pdf --dry-run
python src/ingestion.py --file data/input/olivia_ortho_2.pdf --dry-run
```

✅ Cela crée des fichiers CSV dans `dry_run_output/`

### 2️⃣ Générer la visualisation

```bash
cd dry_run_output/viewer
python generate_graph_viewer.py
```

✅ Cela crée `graph_viewer.html`

### 3️⃣ Ouvrir dans le navigateur

Double-cliquez sur `graph_viewer.html` ou :

```bash
# Windows
start graph_viewer.html

# Mac
open graph_viewer.html

# Linux
xdg-open graph_viewer.html
```

## 🎯 Que voir ?

### Topics partagés (section jaune)

```
🔗 Topics Partagés (Liens entre documents)
- santé : 2 documents liés
- remboursement : 2 documents liés
- assurance : 2 documents liés
```

Ces topics sont la **clé** ! Ils montrent comment vos documents sont liés.

### Graphe interactif

- **Cliquez** sur un nœud pour le sélectionner
- **Glissez** pour déplacer le graphe
- **Molette** pour zoomer
- **Double-clic** sur un nœud pour zoomer dessus

### Boutons utiles

- **Focus Topics Partagés** : Zoom sur les topics qui lient vos documents
- **Layouts** : Changez la disposition (hiérarchique, force, circulaire)

## 💡 Astuce

Plus vous traitez de documents sur des sujets similaires, plus le graphe devient intéressant !

## 📖 Documentation complète

- [README.md](README.md) - Fonctionnalités détaillées
- [USAGE_GUIDE.md](USAGE_GUIDE.md) - Guide d'utilisation complet

## ❓ Problème ?

**Aucun fichier CSV trouvé**
→ Exécutez d'abord l'ingestion en mode `--dry-run`

**Le graphe ne s'affiche pas**
→ Vérifiez votre connexion internet (pour charger vis.js)

**Pas de topics partagés**
→ Normal si vous n'avez traité qu'un seul document ou des documents très différents
