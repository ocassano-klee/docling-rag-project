"""
Script d'interrogation du système RAG
"""

import argparse
import yaml
import os
import csv
from typing import List, Dict, Any
from datetime import datetime

from embeddings import EmbeddingGenerator
from neptune_client import NeptuneClient
from opensearch_client import OpenSearchClient


class QueryPipeline:
    """Pipeline d'interrogation du système RAG"""
    
    def __init__(self, config_path: str = "config.yaml", dry_run: bool = False):
        """
        Initialise le pipeline d'interrogation
        
        Args:
            config_path: Chemin vers le fichier de configuration
            dry_run: Mode dry-run (génère des CSV sans exécution)
        """
        # Chargement de la configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.dry_run = dry_run
        
        # Initialisation des composants
        print("=== Initialisation du pipeline d'interrogation ===\n")
        
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
        else:
            print("Mode DRY-RUN activé - Génération de fichiers CSV\n")
            self.neptune_queries = []
            self.opensearch_queries = []
    
    def query(self, question: str, use_neptune_filter: bool = False) -> str:
        """
        Interroge le système RAG avec une question
        
        Args:
            question: Question de l'utilisateur
            use_neptune_filter: Utiliser Neptune pour filtrer les chunks
            
        Returns:
            Prompt augmenté avec le contexte
        """
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print(f"{'='*60}\n")
        
        # Étape 1: Génération de l'embedding de la question
        print("Étape 1/5: Génération de l'embedding de la question")
        question_embedding = self.embeddings.generate_embedding(question, input_type="search_query")
        print(f"✓ Embedding généré (dimension: {len(question_embedding)})\n")
        
        # Étape 2: Recherche de similarité dans OpenSearch
        print("Étape 2/5: Recherche de similarité dans OpenSearch")
        similar_chunks = self._search_similar_chunks(
            question_embedding,
            use_neptune_filter=use_neptune_filter
        )
        print(f"✓ {len(similar_chunks)} chunks pertinents trouvés\n")
        
        # Étape 3: Récupération des annotations depuis Neptune
        print("Étape 3/5: Récupération des annotations depuis Neptune")
        enriched_chunks = self._enrich_with_annotations(similar_chunks)
        print(f"✓ Chunks enrichis avec annotations\n")
        
        # Étape 4: Construction du prompt augmenté
        print("Étape 4/5: Construction du prompt augmenté")
        augmented_prompt = self._build_augmented_prompt(question, enriched_chunks)
        print(f"✓ Prompt augmenté construit ({len(augmented_prompt)} caractères)\n")
        
        # Étape 5: Export du résultat
        print("Étape 5/5: Export du résultat")
        output_file = self._export_prompt(augmented_prompt, question)
        print(f"✓ Prompt exporté: {output_file}\n")
        
        # Export en mode dry-run
        if self.dry_run:
            self._export_dry_run()
        
        print(f"{'='*60}")
        print("✓ Interrogation terminée avec succès")
        print(f"{'='*60}\n")
        
        return augmented_prompt
    
    def _search_similar_chunks(self, question_embedding: List[float], 
                              use_neptune_filter: bool = False) -> List[Dict[str, Any]]:
        """
        Recherche les chunks similaires dans OpenSearch
        
        Args:
            question_embedding: Embedding de la question
            use_neptune_filter: Utiliser Neptune pour filtrer
            
        Returns:
            Liste des chunks similaires
        """
        top_k = self.config['query']['top_k']
        filter_chunk_ids = None
        
        # Filtrage optionnel via Neptune
        if use_neptune_filter:
            print("  → Utilisation du filtrage Neptune")
            # Dans un cas réel, on pourrait extraire des entités de la question
            # et chercher les chunks liés dans le graphe
            # Pour l'exemple, on ne filtre pas
            filter_chunk_ids = None
        
        if self.dry_run:
            # Génération de la requête pour dry-run
            query = {
                "size": top_k,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": question_embedding[:5] + ["..."],  # Tronqué pour CSV
                            "k": top_k
                        }
                    }
                }
            }
            
            self.opensearch_queries.append({
                'query_type': 'SEARCH_SIMILAR',
                'query': str(query),
                'parameters': {
                    'top_k': top_k,
                    'embedding_dimension': len(question_embedding)
                }
            })
            
            # Retour de chunks fictifs pour dry-run
            return [
                {
                    'chunk_id': f'doc1_chunk_{i:04d}',
                    'document_id': 'doc1',
                    'content': f'Contenu du chunk {i} (exemple pour dry-run)',
                    'metadata': {'page': i, 'type': 'paragraph'},
                    'score': 0.9 - (i * 0.1)
                }
                for i in range(min(top_k, 3))
            ]
        else:
            return self.opensearch.search_similar(
                query_embedding=question_embedding,
                top_k=top_k,
                filter_chunk_ids=filter_chunk_ids
            )
    
    def _enrich_with_annotations(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrichit les chunks avec leurs annotations depuis Neptune
        
        Args:
            chunks: Liste des chunks à enrichir
            
        Returns:
            Chunks enrichis avec annotations
        """
        enriched = []
        
        for chunk in chunks:
            chunk_id = chunk['chunk_id']
            
            if self.dry_run:
                # Génération de la requête pour dry-run
                query = f"MATCH (c:Chunk {{id: '{chunk_id}'}})-[:HAS_ANNOTATION]->(a:Annotation) RETURN a"
                
                self.neptune_queries.append({
                    'query_type': 'GET_ANNOTATIONS',
                    'query': query,
                    'parameters': {'chunk_id': chunk_id}
                })
                
                # Annotations fictives pour dry-run
                chunk['annotations'] = [
                    {
                        'type': 'element_type',
                        'value': 'paragraph',
                        'context': 'Ce contenu est de type paragraph'
                    },
                    {
                        'type': 'location',
                        'value': f"page_{chunk['metadata']['page']}",
                        'context': f"Ce contenu se trouve à la page {chunk['metadata']['page']}"
                    }
                ]
            else:
                annotations = self.neptune.get_chunk_annotations(chunk_id)
                chunk['annotations'] = annotations
            
            enriched.append(chunk)
        
        return enriched
    
    def _build_augmented_prompt(self, question: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Construit le prompt augmenté avec contexte
        
        Args:
            question: Question originale
            chunks: Chunks enrichis avec annotations
            
        Returns:
            Prompt augmenté
        """
        prompt_parts = []
        
        # En-tête
        prompt_parts.append("=" * 80)
        prompt_parts.append("PROMPT AUGMENTÉ POUR LLM")
        prompt_parts.append("=" * 80)
        prompt_parts.append("")
        
        # Contexte
        prompt_parts.append("CONTEXTE RÉCUPÉRÉ:")
        prompt_parts.append("-" * 80)
        prompt_parts.append("")
        
        for i, chunk in enumerate(chunks, 1):
            prompt_parts.append(f"[CHUNK {i}] (Score: {chunk.get('score', 'N/A'):.3f})")
            prompt_parts.append(f"Document: {chunk['document_id']}")
            prompt_parts.append(f"Page: {chunk['metadata']['page']}")
            prompt_parts.append(f"Type: {chunk['metadata']['type']}")
            prompt_parts.append("")
            
            # Annotations
            if chunk.get('annotations'):
                prompt_parts.append("Annotations:")
                for ann in chunk['annotations']:
                    prompt_parts.append(f"  • {ann['type']}: {ann['value']}")
                    prompt_parts.append(f"    → {ann['context']}")
                prompt_parts.append("")
            
            # Contenu
            prompt_parts.append("Contenu:")
            prompt_parts.append(chunk['content'])
            prompt_parts.append("")
            prompt_parts.append("-" * 80)
            prompt_parts.append("")
        
        # Question
        prompt_parts.append("QUESTION:")
        prompt_parts.append("-" * 80)
        prompt_parts.append(question)
        prompt_parts.append("")
        prompt_parts.append("=" * 80)
        prompt_parts.append("")
        
        # Instructions pour le LLM
        prompt_parts.append("INSTRUCTIONS:")
        prompt_parts.append("En utilisant le contexte fourni ci-dessus, réponds à la question de manière")
        prompt_parts.append("précise et détaillée. Si le contexte ne contient pas suffisamment d'informations,")
        prompt_parts.append("indique-le clairement.")
        prompt_parts.append("")
        prompt_parts.append("=" * 80)
        
        return "\n".join(prompt_parts)
    
    def _export_prompt(self, prompt: str, question: str) -> str:
        """
        Exporte le prompt dans un fichier texte
        
        Args:
            prompt: Prompt augmenté
            question: Question originale
            
        Returns:
            Chemin du fichier créé
        """
        output_dir = self.config['output']['results_dir']
        os.makedirs(output_dir, exist_ok=True)
        
        # Nom de fichier avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_question = "".join(c if c.isalnum() else "_" for c in question[:30])
        filename = f"prompt_{timestamp}_{safe_question}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        return filepath
    
    def _export_dry_run(self):
        """Export les requêtes en CSV pour le mode dry-run"""
        
        output_dir = self.config['output']['dry_run_dir']
        os.makedirs(output_dir, exist_ok=True)
        
        # Export Neptune
        neptune_file = os.path.join(output_dir, 'neptune_queries.csv')
        with open(neptune_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['query_type', 'query', 'parameters'])
            writer.writeheader()
            for query in self.neptune_queries:
                writer.writerow(query)
        
        print(f"  ✓ Requêtes Neptune exportées: {neptune_file}")
        
        # Export OpenSearch
        opensearch_file = os.path.join(output_dir, 'opensearch_queries.csv')
        with open(opensearch_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['query_type', 'query', 'parameters'])
            writer.writeheader()
            for query in self.opensearch_queries:
                writer.writerow(query)
        
        print(f"  ✓ Requêtes OpenSearch exportées: {opensearch_file}")
    
    def close(self):
        """Ferme les connexions"""
        if not self.dry_run:
            self.neptune.close()


def main():
    parser = argparse.ArgumentParser(description="Interrogation du système RAG")
    parser.add_argument('--question', type=str, required=True, help="Question à poser")
    parser.add_argument('--config', type=str, default='config.yaml', help="Fichier de configuration")
    parser.add_argument('--dry-run', action='store_true', help="Mode dry-run (génère des CSV)")
    parser.add_argument('--use-neptune-filter', action='store_true', 
                       help="Utiliser Neptune pour filtrer les chunks")
    
    args = parser.parse_args()
    
    # Initialisation du pipeline
    pipeline = QueryPipeline(config_path=args.config, dry_run=args.dry_run)
    
    try:
        # Interrogation
        prompt = pipeline.query(
            question=args.question,
            use_neptune_filter=args.use_neptune_filter
        )
        
        if not args.dry_run:
            print("\n" + "="*60)
            print("APERÇU DU PROMPT GÉNÉRÉ:")
            print("="*60)
            print(prompt[:500] + "...\n")
    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
