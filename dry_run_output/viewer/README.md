# 🌐 Neptune Graph Viewer

Outil de visualisation interactive du graphe Neptune généré par le système d'ingestion RAG.

## 📋 Description

Cet outil lit tous les fichiers CSV `neptune_inserts_*.csv` générés en mode dry-run et crée une page HTML interactive permettant de visualiser comment les différents documents sont liés via les topics partagés.

## 🚀 Utilisation

### Génération de la visualisation

```bash
# Depuis le dossier viewer
python generate_graph_viewer.py
```

Le script va :
1. Scanner tous les fichiers `neptune_inserts_*.csv` dans le dossier parent
2. Parser les requêtes Cypher pour extraire les nœuds et relations
3. Identifier les topics partagés entre documents
4. Générer un fichier `graph_viewer.html` interactif

### Ouverture de la visualisation

Ouvrez simplement le fichier `graph_viewer.html` dans votre navigateur web préféré.

## 🎨 Fonctionnalités

### Types de nœuds

- 🔴 **Documents** (rouge) : Fichiers PDF sources
- 🔵 **Chunks** (bleu) : Morceaux de texte extraits
- 🟡 **Topics** (jaune) : Concepts et mots-clés partagés ⭐
- 🟢 **Annotations** (vert) : Métadonnées contextuelles

### Contrôles interactifs

- **Layouts** : Choisissez entre hiérarchique, force-directed ou circulaire
- **Focus Topics Partagés** : Zoom automatique sur les topics qui lient plusieurs documents
- **Tout Afficher** : Vue d'ensemble du graphe complet
- **Mettre en évidence les liens** : Highlight les connexions du nœud sélectionné
- **Réinitialiser** : Retour à la vue initiale

### Navigation

- **Cliquer-glisser** : Déplacer le graphe
- **Molette** : Zoomer/dézoomer
- **Clic sur nœud** : Sélectionner et voir les connexions
- **Double-clic** : Zoom sur le nœud et ses voisins

## 🔗 Topics Partagés

Les **topics partagés** sont la clé du système de liaison entre documents !

Lorsque plusieurs documents mentionnent les mêmes concepts (ex: "assurance", "remboursement", "santé"), ils sont automatiquement liés via ces topics dans le graphe Neptune.

La visualisation affiche :
- Le nombre de topics partagés
- Les documents liés par chaque topic
- Une mise en évidence visuelle des connexions

## 📊 Statistiques

Le viewer affiche en temps réel :
- Nombre de documents
- Nombre de chunks
- Nombre de topics (dont partagés)
- Nombre d'annotations
- Nombre total de relations

## 💡 Cas d'usage

### Comprendre les liens entre documents

Utilisez le bouton "Focus Topics Partagés" pour voir immédiatement quels concepts relient vos documents.

### Explorer un document spécifique

Cliquez sur un nœud Document (rouge) pour voir tous ses chunks, topics et annotations.

### Analyser un concept

Cliquez sur un Topic (jaune) pour voir tous les chunks qui mentionnent ce concept, potentiellement dans plusieurs documents.

## 🛠️ Personnalisation

Le script `generate_graph_viewer.py` peut être modifié pour :
- Changer les couleurs des nœuds
- Ajuster les layouts
- Ajouter des filtres personnalisés
- Modifier les statistiques affichées

## 📝 Notes techniques

- Le viewer utilise la bibliothèque [vis.js](https://visjs.org/) pour le rendu du graphe
- Tous les calculs sont effectués côté client (pas de serveur nécessaire)
- Le fichier HTML est autonome et portable
- Compatible avec tous les navigateurs modernes

## 🐛 Dépannage

**Aucun fichier CSV trouvé**
- Vérifiez que vous avez exécuté l'ingestion en mode dry-run
- Les fichiers doivent être dans le dossier parent (`../neptune_inserts_*.csv`)

**Le graphe ne s'affiche pas**
- Vérifiez que vous avez une connexion internet (pour charger vis.js)
- Ouvrez la console du navigateur pour voir les erreurs éventuelles

**Trop de nœuds, le graphe est illisible**
- Utilisez le layout "Force-directed" pour une meilleure répartition
- Zoomez sur des sections spécifiques
- Utilisez les filtres pour afficher uniquement certains types de nœuds
