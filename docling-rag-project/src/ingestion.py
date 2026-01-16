"""
Script d'ingestion de documents PDF dans Neptune et OpenSearch
"""

import argparse
import yaml
import os
import csv
from typing import Dict, Any, List
from tqdm import tqdm

from docling_processor import DoclingProcessor
from embeddings import EmbeddingGenerator
from neptune_client import NeptuneClient
from opensearch_client import OpenSearchClient


class IngestionPipeline:
    """Pipeline d'ingestion de documents"""
    
    def __init__(self, config_path: str = "config.yaml", dry_run: bool = False):
        """
        Initialise le pipeline d'ingestion
        
        Args:
            config_path: Chemin vers le fichier de configuration
            dry_run: Mode dry-run (génère des CSV sans insertion)
        """
        # Chargement de la configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.dry_run = dry_run
        
        # Initialisation des composants
        print("=== Initialisation du pipeline d'ingestion ===\n")
        
        self.docling = DoclingProcessor(
            chunk_size=self.config['docling']['chunk_size'],
            chunk_overlap=self.config['docling']['chunk_overlap'],
            min_chunk_size=self.config['docling']['min_chunk_size']
        )
        
        self.embeddings = EmbeddingGenerator(
            provider=self.config['embeddings']['provider'],
            model_name=self.config['embeddings']['model'],
            api_key=self.config['embeddings'].get('api_key')
        )
        
        if not dry_run:
            self.neptune = NeptuneClient(
                endpoint=self.config['neptune']['endpoint'],
                port=self.config['neptune']['port'],
                use_iam=self.config['neptune']['use_iam']
            )
            self.neptune.connect()
            
            self.opensearch = OpenSearchClient(
                endpoint=self.config['opensearch']['endpoint'],
                index_name=self.config['opensearch']['index_name'],
                use_iam=self.config['opensearch']['use_iam']
            )
            self.opensearch.create_index(
                dimension=self.config['embeddings']['dimension']
            )
        else:
            print("Mode DRY-RUN activé - Génération de fichiers CSV\n")
            self.neptune_queries = []
            self.opensearch_requests = []
    
    def process_document(self, pdf_path: str):
        """
        Traite un document PDF complet
        
        Args:
            pdf_path: Chemin vers le fichier PDF
        """
        print(f"\n{'='*60}")
        print(f"Traitement du document: {pdf_path}")
        print(f"{'='*60}\n")
        
        # Étape 1: Extraction et chunking avec Docling
        print("Étape 1/5: Extraction et chunking avec Docling")
        document_data = self.docling.process_pdf(pdf_path)
        chunks = self.docling.create_chunks(document_data)
        print(f"✓ {len(chunks)} chunks créés\n")
        
        # Étape 2: Génération des embeddings
        print("Étape 2/5: Génération des embeddings")
        chunk_contents = [chunk['content'] for chunk in chunks]
        embeddings = self.embeddings.generate_embeddings_batch(
            chunk_contents,
            batch_size=self.config['embeddings']['batch_size']
        )
        print(f"✓ {len(embeddings)} embeddings générés\n")
        
        # Étape 3: Insertion dans Neptune
        print("Étape 3/5: Insertion des métadonnées dans Neptune")
        self._insert_to_neptune(document_data, chunks)
        print()
        
        # Étape 4: Insertion dans OpenSearch
        print("Étape 4/5: Insertion des embeddings dans OpenSearch")
        self._insert_to_opensearch(chunks, embeddings)
        print()
        
        # Étape 5: Export en mode dry-run
        if self.dry_run:
            print("Étape 5/5: Export des requêtes en CSV")
            self._export_dry_run()
        
        print(f"\n{'='*60}")
        print("✓ Traitement terminé avec succès")
        print(f"{'='*60}\n")
    
    def _insert_to_neptune(self, document_data: Dict[str, Any], chunks: List[Dict[str, Any]]):
        """Insère les données dans Neptune"""
        
        # Insertion du document
        if self.dry_run:
            query = f"CREATE (d:Document {{id: '{document_data['id']}', title: '{document_data['title']}', source: '{document_data['source']}'}})"
            self.neptune_queries.append({
                'query_type': 'CREATE_DOCUMENT',
                'query': query,
                'parameters': {
                    'id': document_data['id'],
                    'title': document_data['title'],
                    'source': document_data['source']
                }
            })
        else:
            self.neptune.insert_document(
                document_data['id'],
                document_data['title'],
                document_data['source']
            )
        
        # Insertion des chunks et annotations
        for chunk in tqdm(chunks, desc="Insertion chunks Neptune"):
            if self.dry_run:
                # Chunk
                query = f"CREATE (c:Chunk {{id: '{chunk['id']}', document_id: '{chunk['document_id']}', page: {chunk['metadata']['page']}, type: '{chunk['metadata']['type']}'}})"
                self.neptune_queries.append({
                    'query_type': 'CREATE_CHUNK',
                    'query': query,
                    'parameters': chunk
                })
                
                # Relation
                query = f"MATCH (d:Document {{id: '{chunk['document_id']}'}}), (c:Chunk {{id: '{chunk['id']}'}}) CREATE (d)-[:HAS_CHUNK]->(c)"
                self.neptune_queries.append({
                    'query_type': 'CREATE_RELATIONSHIP',
                    'query': query,
                    'parameters': {}
                })
                
                # Annotations
                for annotation in chunk.get('annotations', []):
                    ann_id = f"{chunk['id']}_ann_{annotation['type']}"
                    query = f"CREATE (a:Annotation {{id: '{ann_id}', type: '{annotation['type']}', value: '{annotation['value']}'}})"
                    self.neptune_queries.append({
                        'query_type': 'CREATE_ANNOTATION',
                        'query': query,
                        'parameters': annotation
                    })
                    
                    query = f"MATCH (c:Chunk {{id: '{chunk['id']}'}}), (a:Annotation {{id: '{ann_id}'}}) CREATE (c)-[:HAS_ANNOTATION]->(a)"
                    self.neptune_queries.append({
                        'query_type': 'CREATE_RELATIONSHIP',
                        'query': query,
                        'parameters': {}
                    })
            else:
                self.neptune.insert_chunk(chunk)
        
        print(f"✓ {len(chunks)} chunks insérés dans Neptune")
    
    def _insert_to_opensearch(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Insère les embeddings dans OpenSearch"""
        
        for chunk, embedding in tqdm(zip(chunks, embeddings), total=len(chunks), desc="Insertion OpenSearch"):
            if self.dry_run:
                document = {
                    "chunk_id": chunk['id'],
                    "document_id": chunk['document_id'],
                    "content": chunk['content'],
                    "embedding": embedding,
                    "metadata": chunk['metadata']
                }
                
                request = {
                    'action': 'index',
                    'index': self.config['opensearch']['index_name'],
                    'document_id': chunk['id'],
                    'body': document
                }
                self.opensearch_requests.append(request)
            else:
                self.opensearch.index_chunk(
                    chunk_id=chunk['id'],
                    document_id=chunk['document_id'],
                    content=chunk['content'],
                    embedding=embedding,
                    metadata=chunk['metadata']
                )
        
        print(f"✓ {len(chunks)} chunks indexés dans OpenSearch")
    
    def _export_dry_run(self):
        """Export les requêtes en CSV pour le mode dry-run"""
        
        output_dir = self.config['output']['dry_run_dir']
        os.makedirs(output_dir, exist_ok=True)
        
        # Export Neptune
        neptune_file = os.path.join(output_dir, 'neptune_inserts.csv')
        with open(neptune_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['query_type', 'query', 'parameters'])
            writer.writeheader()
            for query in self.neptune_queries:
                writer.writerow({
                    'query_type': query['query_type'],
                    'query': query['query'],
                    'parameters': str(query['parameters'])
                })
        
        print(f"✓ Requêtes Neptune exportées: {neptune_file}")
        
        # Export OpenSearch
        opensearch_file = os.path.join(output_dir, 'opensearch_inserts.csv')
        with open(opensearch_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['action', 'index', 'document_id', 'body'])
            writer.writeheader()
            for request in self.opensearch_requests:
                writer.writerow({
                    'action': request['action'],
                    'index': request['index'],
                    'document_id': request['document_id'],
                    'body': str(request['body'])[:1000]  # Limiter la taille
                })
        
        print(f"✓ Requêtes OpenSearch exportées: {opensearch_file}")
    
    def close(self):
        """Ferme les connexions"""
        if not self.dry_run:
            self.neptune.close()


def main():
    parser = argparse.ArgumentParser(description="Ingestion de documents PDF")
    parser.add_argument('--input', type=str, required=True, help="Chemin vers le fichier PDF")
    parser.add_argument('--config', type=str, default='config.yaml', help="Fichier de configuration")
    parser.add_argument('--dry-run', action='store_true', help="Mode dry-run (génère des CSV)")
    parser.add_argument('--s3-uri', type=str, help="URI S3 du document (futur)")
    
    args = parser.parse_args()
    
    # Vérification du fichier
    if not args.s3_uri and not os.path.exists(args.input):
        print(f"Erreur: Le fichier {args.input} n'existe pas")
        return
    
    # Initialisation du pipeline
    pipeline = IngestionPipeline(config_path=args.config, dry_run=args.dry_run)
    
    try:
        # Traitement du document
        pipeline.process_document(args.input)
    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
