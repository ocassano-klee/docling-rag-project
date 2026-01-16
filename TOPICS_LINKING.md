# Liaison des documents via les Topics

## Vue d'ensemble

Le système crée maintenant un **graphe de connaissances interconnecté** où les documents sont liés via des **nœuds Topic partagés**.

## Comment ça fonctionne

### 1. Extraction automatique de topics

Pour chaque chunk de texte, le système extrait :

- **Concepts métier** : assurance, remboursement, dentaire, santé, intervention, mutuelle, contrat, plafond, etc.
- **Mots-clés fréquents** : noms d'organisations, termes spécifiques, etc.

### 2. Création de nœuds Topic partagés

Les topics sont créés avec `MERGE` dans Neptune, ce qui signifie :

```cypher
MERGE (t:Topic {id: 'topic_assurance', name: 'assurance', type: 'business_concept'})
```

- Si le topic existe déjà → il est réutilisé
- Si le topic n'existe pas → il est créé

### 3. Relations ABOUT

Chaque chunk est lié aux topics qu'il contient :

```cypher
(Chunk) -[:ABOUT]-> (Topic)
```

## Exemple concret

### Document 1 : doc.pdf (Remboursement dentaire)

```
Document: doc.pdf
├── Chunk 1: "remboursement dentaire..."
│   ├── ABOUT → Topic: remboursement
│   ├── ABOUT → Topic: dentaire
│   └── ABOUT → Topic: assurance
└── Chunk 2: "intervention INAMI..."
    ├── ABOUT → Topic: intervention
    └── ABOUT → Topic: assurance
```

### Document 2 : rapport.pdf (Rapport d'assurance)

```
Document: rapport.pdf
├── Chunk 1: "contrat d'assurance..."
│   ├── ABOUT → Topic: assurance  ← PARTAGÉ avec doc.pdf !
│   └── ABOUT → Topic: contrat
└── Chunk 2: "remboursement annuel..."
    └── ABOUT → Topic: remboursement  ← PARTAGÉ avec doc.pdf !
```

### Graphe résultant

```
        [Topic: assurance]
       /        |         \
      /         |          \
Chunk 1     Chunk 2      Chunk 1
(doc.pdf)   (doc.pdf)  (rapport.pdf)
     \                    /
      \                  /
       [Topic: remboursement]
              |
          Chunk 2
        (rapport.pdf)
```

## Requêtes possibles

### 1. Trouver tous les documents sur un topic

```cypher
MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)-[:ABOUT]->(t:Topic {name: 'assurance'})
RETURN DISTINCT d.title
```

### 2. Trouver les documents similaires

```cypher
// Documents partageant au moins 3 topics communs
MATCH (d1:Document)-[:HAS_CHUNK]->(c1:Chunk)-[:ABOUT]->(t:Topic)<-[:ABOUT]-(c2:Chunk)<-[:HAS_CHUNK]-(d2:Document)
WHERE d1 <> d2
WITH d1, d2, COUNT(DISTINCT t) as common_topics
WHERE common_topics >= 3
RETURN d1.title, d2.title, common_topics
ORDER BY common_topics DESC
```

### 3. Trouver les topics les plus populaires

```cypher
MATCH (c:Chunk)-[:ABOUT]->(t:Topic)
RETURN t.name, t.type, COUNT(c) as chunk_count
ORDER BY chunk_count DESC
LIMIT 10
```

### 4. Navigation entre documents via topics

```cypher
// Depuis un document, trouver les documents liés via topics communs
MATCH (d1:Document {id: 'doc'})-[:HAS_CHUNK]->(c1:Chunk)-[:ABOUT]->(t:Topic)
MATCH (t)<-[:ABOUT]-(c2:Chunk)<-[:HAS_CHUNK]-(d2:Document)
WHERE d1 <> d2
RETURN d2.title, COLLECT(DISTINCT t.name) as shared_topics
```

## Avantages

### 1. Découverte de contenu

Les utilisateurs peuvent découvrir des documents connexes même s'ils ne partagent pas de mots-clés exacts.

### 2. Navigation contextuelle

Naviguer d'un document à l'autre via des concepts partagés.

### 3. Analyse thématique

Identifier les thèmes dominants dans une collection de documents.

### 4. Recommandations

Recommander des documents similaires basés sur les topics partagés.

## Topics extraits du document exemple

Voici les 17 topics identifiés dans `doc.pdf` :

### Concepts métier (score élevé)
1. **remboursement** (score: 4.0) - 2 chunks
2. **dentaire** (score: 6.0) - 2 chunks
3. **santé** (score: 2.0) - 1 chunk
4. **intervention** (score: 8.0) - 2 chunks
5. **client** (score: 2.0) - 1 chunk
6. **assurance** (score: 6.0) - 2 chunks
7. **mutuelle** (score: 2.0) - 1 chunk
8. **contrat** (score: 2.0) - 1 chunk
9. **montant** (score: 10.0) - 2 chunks
10. **plafond** (score: 8.0) - 1 chunk
11. **période** (score: 2.0) - 1 chunk

### Mots-clés spécifiques
12. **partenamut** (score: 2.0) - 1 chunk
13. **mloz** (score: 2.0) - 1 chunk
14. **insurance** (score: 2.0) - 1 chunk
15. **totaux** (score: 3.0) - 1 chunk
16. **dentalia** (score: 2.0) - 1 chunk
17. **année** (score: 2.0) - 1 chunk

## Configuration

Vous pouvez ajuster l'extraction de topics dans `src/topic_extractor.py` :

```python
TopicExtractor(
    min_word_length=4,      # Longueur minimale d'un mot
    max_topics=5            # Nombre max de topics par chunk
)
```

Vous pouvez aussi étendre le dictionnaire de concepts métier :

```python
self.business_concepts = {
    'assurance': ['assurance', 'assurances', 'assurantiel'],
    'votre_concept': ['mot1', 'mot2', 'mot3'],
    # ...
}
```

## Visualisation

Le graphe généré montre maintenant :

- **Nœuds rouges** : Documents
- **Nœuds bleus** : Chunks
- **Nœuds jaunes** : Topics (PARTAGÉS entre documents)
- **Nœuds verts** : Annotations

Les flèches jaunes `ABOUT` montrent les relations entre chunks et topics.

## Prochaines étapes

Pour tester le partage de topics :

1. Ajoutez un autre PDF dans `data/input/`
2. Lancez l'ingestion :
   ```bash
   python src/ingestion.py --input data/input/autre_doc.pdf --dry-run
   ```
3. Vérifiez que les topics communs sont réutilisés (MERGE au lieu de CREATE)
4. Visualisez le graphe combiné

## Exemple de requête multi-documents

Une fois plusieurs documents ingérés :

```cypher
// Trouver le "hub" de topics (topics les plus connectés)
MATCH (t:Topic)<-[:ABOUT]-(c:Chunk)
WITH t, COUNT(DISTINCT c) as connections
ORDER BY connections DESC
LIMIT 5
RETURN t.name, t.type, connections
```

Cela vous montrera quels concepts sont les plus centraux dans votre collection de documents.
