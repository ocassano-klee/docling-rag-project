# 📖 Guide d'utilisation du Graph Viewer

## 🎯 Objectif

Le Graph Viewer permet de visualiser comment vos documents PDF sont automatiquement liés via les **topics partagés** extraits par le système RAG.

## 🚀 Démarrage rapide

### 1. Générer les données (mode dry-run)

Avant d'utiliser le viewer, vous devez avoir des fichiers CSV générés en mode dry-run :

```bash
# Windows
python src/ingestion.py --file data/input/document1.pdf --dry-run
python src/ingestion.py --file data/input/document2.pdf --dry-run

# Linux/Mac
python src/ingestion.py --file data/input/document1.pdf --dry-run
python src/ingestion.py --file data/input/document2.pdf --dry-run
```

Cela génère des fichiers dans `dry_run_output/` :
- `neptune_inserts_document1.csv`
- `neptune_inserts_document2.csv`
- etc.

### 2. Générer la visualisation

```bash
cd dry_run_output/viewer
python generate_graph_viewer.py
```

### 3. Ouvrir le viewer

Double-cliquez sur `graph_viewer.html` ou ouvrez-le dans votre navigateur.

## 🔍 Comprendre la visualisation

### Les couleurs

- 🔴 **Rouge** = Documents (vos fichiers PDF)
- 🔵 **Bleu** = Chunks (morceaux de texte extraits)
- 🟡 **Jaune** = Topics (concepts partagés) ⭐ **C'EST LA CLÉ !**
- 🟢 **Vert** = Annotations (métadonnées)

### Les relations

- **Document → Chunk** : Un document contient plusieurs chunks
- **Chunk → Topic** : Un chunk parle de certains topics
- **Chunk → Annotation** : Un chunk a des métadonnées

### Les topics partagés

Un **topic partagé** est un concept mentionné dans plusieurs documents.

**Exemple concret** :
- Document 1 (olivia_ortho_1.pdf) mentionne "assurance", "remboursement", "santé"
- Document 2 (olivia_ortho_2.pdf) mentionne aussi "assurance", "remboursement", "santé"
- → Ces 3 topics créent des liens automatiques entre les 2 documents !

## 💡 Cas d'usage pratiques

### Cas 1 : Trouver des documents similaires

**Problème** : "Quels documents parlent des mêmes sujets ?"

**Solution** :
1. Cliquez sur "Focus Topics Partagés"
2. Regardez les topics jaunes qui connectent plusieurs documents rouges
3. Ces documents sont liés par les mêmes concepts

### Cas 2 : Explorer un concept

**Problème** : "Où est-ce qu'on parle de 'remboursement' dans mes documents ?"

**Solution** :
1. Trouvez le topic "remboursement" (nœud jaune)
2. Cliquez dessus
3. Tous les chunks bleus connectés mentionnent ce concept
4. Remontez aux documents rouges pour savoir quels fichiers en parlent

### Cas 3 : Analyser un document

**Problème** : "De quoi parle ce document ?"

**Solution** :
1. Cliquez sur un document rouge
2. Regardez tous les topics jaunes connectés
3. Ce sont les concepts principaux du document

## 🎮 Contrôles avancés

### Layouts

- **Hiérarchique** : Vue en arbre (par défaut)
  - Idéal pour voir la structure Document → Chunk → Topic
  
- **Force-directed** : Les nœuds se repoussent naturellement
  - Idéal pour voir les clusters de documents similaires
  
- **Circulaire** : Tous les nœuds en cercle
  - Idéal pour une vue d'ensemble équilibrée

### Boutons d'action

- **Focus Topics Partagés** : Zoom sur les topics qui lient plusieurs documents
- **Tout Afficher** : Vue complète du graphe
- **Mettre en évidence les liens** : Highlight les connexions du nœud sélectionné
- **Réinitialiser** : Retour à la vue initiale

### Navigation souris

- **Clic gauche + glisser** : Déplacer le graphe
- **Molette** : Zoomer/dézoomer
- **Clic sur nœud** : Sélectionner
- **Double-clic sur nœud** : Zoom sur le nœud et ses voisins

## 📊 Interpréter les statistiques

En haut de la page, vous voyez :

```
Documents: 2    Chunks: 11    Topics: 25    Annotations: 33    Relations: 82
```

- **Documents** : Nombre de PDF traités
- **Chunks** : Nombre total de morceaux de texte
- **Topics** : Nombre de concepts uniques extraits
- **Annotations** : Nombre de métadonnées
- **Relations** : Nombre total de liens dans le graphe

### Topics partagés

La section jaune montre les topics qui lient plusieurs documents :

```
🔗 Topics Partagés (Liens entre documents)
- santé : 2 documents liés
- remboursement : 2 documents liés
- assurance : 2 documents liés
```

Plus un topic est partagé, plus il est important pour relier vos documents !

## 🎓 Exemple d'analyse complète

Imaginons que vous avez traité 2 documents d'assurance :

1. **Ouvrez le viewer** → Vous voyez 2 nœuds rouges (documents)

2. **Cliquez sur "Focus Topics Partagés"** → Vous voyez 5 topics jaunes au centre

3. **Cliquez sur le topic "assurance"** → Vous voyez :
   - 4 chunks bleus connectés (2 par document)
   - Ces chunks mentionnent tous "assurance"
   - Les 2 documents sont donc liés par ce concept

4. **Changez le layout en "Force-directed"** → Les documents similaires se rapprochent naturellement

5. **Double-cliquez sur un document** → Zoom sur ce document et tous ses concepts

## 🔧 Personnalisation

Le fichier `generate_graph_viewer.py` peut être modifié pour :

- Changer les couleurs des nœuds (ligne ~200)
- Ajuster la taille des nœuds (ligne ~400)
- Modifier les layouts (ligne ~450)
- Ajouter des filtres personnalisés

## ❓ Questions fréquentes

**Q : Pourquoi certains topics ne sont pas partagés ?**
R : Certains concepts sont spécifiques à un seul document. Seuls les topics mentionnés dans plusieurs documents sont "partagés".

**Q : Comment ajouter plus de documents ?**
R : Exécutez simplement l'ingestion en dry-run sur de nouveaux PDF, puis régénérez le viewer.

**Q : Le graphe est trop chargé, comment simplifier ?**
R : Utilisez le layout "Force-directed" et zoomez sur des sections spécifiques. Vous pouvez aussi modifier le script pour filtrer certains types de nœuds.

**Q : Puis-je exporter le graphe ?**
R : Oui, faites un clic droit sur le graphe et "Enregistrer l'image sous" dans votre navigateur.

## 🎉 Conclusion

Le Graph Viewer vous permet de **voir visuellement** comment vos documents sont interconnectés via les concepts qu'ils partagent. C'est la clé pour comprendre comment le système RAG va pouvoir faire des liens intelligents entre vos documents lors des requêtes !
