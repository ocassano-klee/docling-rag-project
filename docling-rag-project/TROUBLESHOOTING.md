# Guide de dépannage

## Problèmes d'installation

### Erreur : "No module named 'docling'"

**Solution** :
```bash
pip install --upgrade docling
```

Si le problème persiste :
```bash
pip install docling --no-cache-dir
```

### Erreur : "Could not find a version that satisfies the requirement"

**Cause** : Version de Python incompatible

**Solution** : Vérifier la version de Python (minimum 3.8)
```bash
python --version
```

Si nécessaire, créer un environnement avec la bonne version :
```bash
conda create -n docling-rag python=3.10
conda activate docling-rag
```

### Erreur lors de l'installation de sentence-transformers

**Solution** : Installer PyTorch d'abord
```bash
pip install torch torchvision torchaudio
pip install sentence-transformers
```

## Problèmes de connexion Neptune

### Erreur : "Connection refused"

**Causes possibles** :
1. Endpoint incorrect dans config.yaml
2. Cluster Neptune arrêté
3. Security group ne permet pas la connexion
4. VPC/subnet incorrect

**Solutions** :

1. Vérifier l'endpoint :
```bash
aws neptune describe-db-clusters --query 'DBClusters[*].[DBClusterIdentifier,Endpoint]'
```

2. Vérifier le statut du cluster :
```bash
aws neptune describe-db-clusters --db-cluster-identifier your-cluster
```

3. Vérifier les security groups :
   - Port 8182 doit être ouvert
   - Source : votre IP ou security group

4. Si vous êtes hors VPC, utiliser un bastion ou VPN

### Erreur : "Authentication failed"

**Cause** : Problème d'authentification IAM

**Solution** :

1. Vérifier les credentials AWS :
```bash
aws sts get-caller-identity
```

2. Vérifier les permissions IAM :
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "neptune-db:*"
      ],
      "Resource": "arn:aws:neptune-db:region:account:cluster/*"
    }
  ]
}
```

3. Pour l'authentification IAM, installer :
```bash
pip install requests-aws4auth
```

### Mode sans Neptune (développement local)

Utiliser le mode dry-run pour tester sans Neptune :
```bash
python src/ingestion.py --input data/input/test.pdf --dry-run
```

## Problèmes de connexion OpenSearch

### Erreur : "ConnectionError"

**Solutions** :

1. Vérifier l'endpoint :
```bash
aws opensearch describe-domain --domain-name your-domain
```

2. Vérifier l'accès réseau :
   - Si VPC : vérifier security groups
   - Si public : vérifier access policy

3. Tester la connexion :
```bash
curl -X GET "https://your-domain.region.es.amazonaws.com/"
```

### Erreur : "AuthorizationException"

**Solution** : Configurer l'access policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::account:user/your-user"
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:region:account:domain/your-domain/*"
    }
  ]
}
```

### Erreur : "Index not found"

**Cause** : L'index n'a pas été créé

**Solution** :
```python
from opensearch_client import OpenSearchClient

client = OpenSearchClient(...)
client.create_index(dimension=384)
```

## Problèmes avec Docling

### Erreur : "Failed to parse PDF"

**Causes possibles** :
1. PDF corrompu
2. PDF protégé par mot de passe
3. PDF avec encodage non standard

**Solutions** :

1. Vérifier le PDF :
```bash
pdfinfo your-file.pdf
```

2. Réparer le PDF :
```bash
# Avec Ghostscript
gs -o repaired.pdf -sDEVICE=pdfwrite -dPDFSETTINGS=/prepress input.pdf
```

3. Retirer la protection :
```bash
# Avec qpdf
qpdf --decrypt input.pdf output.pdf
```

### Erreur : "Out of memory"

**Cause** : PDF trop volumineux

**Solutions** :

1. Augmenter la mémoire disponible
2. Découper le PDF en plusieurs fichiers
3. Traiter page par page

```python
# Traitement page par page
for page_num in range(1, num_pages + 1):
    result = converter.convert(pdf_path, pages=[page_num])
```

### Chunks vides ou de mauvaise qualité

**Causes** :
- PDF scanné (images, pas de texte)
- Mise en page complexe
- Tableaux mal formatés

**Solutions** :

1. Pour PDF scannés, utiliser OCR :
```bash
pip install pytesseract
```

2. Ajuster les paramètres de chunking :
```yaml
docling:
  chunk_size: 1024  # Augmenter
  chunk_overlap: 100
  min_chunk_size: 50  # Réduire
```

## Problèmes d'embeddings

### Erreur : "CUDA out of memory"

**Solution** : Utiliser CPU ou réduire batch_size

```yaml
embeddings:
  batch_size: 8  # Réduire de 32 à 8
```

Ou forcer l'utilisation du CPU :
```python
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
```

### Embeddings de mauvaise qualité

**Solutions** :

1. Utiliser un meilleur modèle :
```yaml
embeddings:
  model: "sentence-transformers/all-mpnet-base-v2"
  dimension: 768
```

2. Pour le français :
```yaml
embeddings:
  model: "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
  dimension: 768
```

### Téléchargement du modèle échoue

**Solution** : Télécharger manuellement

```python
from sentence_transformers import SentenceTransformer

# Télécharger et sauvegarder
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save('models/all-MiniLM-L6-v2')

# Charger depuis le disque
model = SentenceTransformer('models/all-MiniLM-L6-v2')
```

## Problèmes de performance

### Ingestion trop lente

**Solutions** :

1. Utiliser GPU pour embeddings :
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

2. Augmenter batch_size :
```yaml
embeddings:
  batch_size: 64
```

3. Utiliser bulk indexing pour OpenSearch :
```python
opensearch.bulk_index(chunks)
```

4. Paralléliser le traitement :
```python
from multiprocessing import Pool

with Pool(4) as p:
    p.map(process_document, pdf_files)
```

### Recherche trop lente

**Solutions** :

1. Réduire ef_search dans OpenSearch :
```json
{
  "index": {
    "knn.algo_param.ef_search": 50
  }
}
```

2. Réduire top_k :
```yaml
query:
  top_k: 3
```

3. Utiliser le filtrage Neptune pour réduire l'espace de recherche

### Consommation mémoire excessive

**Solutions** :

1. Traiter les documents un par un
2. Libérer la mémoire après chaque document :
```python
import gc
gc.collect()
```

3. Utiliser un modèle d'embeddings plus petit

## Problèmes de qualité des résultats

### Chunks non pertinents retournés

**Solutions** :

1. Augmenter le seuil de similarité :
```yaml
query:
  similarity_threshold: 0.8
```

2. Augmenter top_k pour avoir plus de choix :
```yaml
query:
  top_k: 10
```

3. Utiliser le filtrage Neptune :
```bash
python src/query.py --question "..." --use-neptune-filter
```

4. Améliorer le chunking :
   - Réduire chunk_size pour plus de précision
   - Augmenter chunk_overlap pour plus de contexte

### Annotations manquantes ou incorrectes

**Solution** : Améliorer la génération d'annotations

Éditer `src/docling_processor.py` :
```python
def _generate_annotations(self, content, element_type, page_number):
    annotations = []
    
    # Ajouter vos propres règles
    if "important" in content.lower():
        annotations.append({
            "type": "priority",
            "value": "high",
            "context": "Contenu marqué comme important"
        })
    
    return annotations
```

### Contexte insuffisant dans le prompt

**Solutions** :

1. Augmenter top_k
2. Inclure les chunks adjacents :
```python
# Récupérer les chunks avant/après
related_chunks = neptune.get_related_chunks(chunk_id, max_distance=1)
```

3. Ajouter plus d'annotations contextuelles

## Problèmes avec le mode dry-run

### Fichiers CSV vides

**Cause** : Erreur avant la génération des requêtes

**Solution** : Vérifier les logs pour identifier l'erreur

### CSV mal formatés

**Cause** : Caractères spéciaux dans les données

**Solution** : Améliorer l'échappement

```python
import csv

# Utiliser QUOTE_ALL
writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
```

## Problèmes AWS

### Erreur : "Credentials not found"

**Solutions** :

1. Configurer AWS CLI :
```bash
aws configure
```

2. Utiliser des variables d'environnement :
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=eu-west-1
```

3. Utiliser un profil :
```bash
export AWS_PROFILE=your-profile
```

### Erreur : "Region not specified"

**Solution** : Ajouter la région dans config.yaml

```yaml
neptune:
  region: "eu-west-1"

opensearch:
  region: "eu-west-1"
```

### Coûts AWS élevés

**Solutions** :

1. Utiliser des instances plus petites pour Neptune
2. Activer auto-scaling pour OpenSearch
3. Supprimer les anciens index :
```bash
curl -X DELETE "https://your-domain.es.amazonaws.com/old-index"
```

4. Arrêter Neptune quand non utilisé :
```bash
aws neptune stop-db-cluster --db-cluster-identifier your-cluster
```

## Logs et debugging

### Activer les logs détaillés

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Vérifier les requêtes Neptune

```python
# Activer le logging Gremlin
import logging
logging.getLogger('gremlin_python').setLevel(logging.DEBUG)
```

### Vérifier les requêtes OpenSearch

```python
# Activer le logging OpenSearch
import logging
logging.getLogger('opensearch').setLevel(logging.DEBUG)
```

### Tester les composants individuellement

```python
# Test embeddings
from embeddings import EmbeddingGenerator
gen = EmbeddingGenerator()
vec = gen.generate_embedding("test")
print(f"Dimension: {len(vec)}")

# Test Neptune
from neptune_client import NeptuneClient
client = NeptuneClient(...)
client.connect()

# Test OpenSearch
from opensearch_client import OpenSearchClient
client = OpenSearchClient(...)
client.create_index()
```

## Support

Si le problème persiste :

1. Vérifier les logs dans `logs/` (si configuré)
2. Exécuter en mode dry-run pour isoler le problème
3. Tester chaque composant séparément
4. Consulter la documentation AWS :
   - [Neptune](https://docs.aws.amazon.com/neptune/)
   - [OpenSearch](https://docs.aws.amazon.com/opensearch-service/)
5. Vérifier les issues GitHub de Docling
