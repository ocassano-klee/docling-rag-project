"""
Script d'ingestion de documents PDF dans Neptune et OpenSearch
"""

import argparse
import yaml
import os
import csv
from typing import Dict, Any, List, Set
from tqdm import tqdm
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from docling_processor import DoclingProcessor
from embeddings import EmbeddingGenerator
from neptune_client import NeptuneClient
from opensearch_client import OpenSearchClient
from topic_extractor import TopicExtractor


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
        
        self.topic_extractor = TopicExtractor(
            min_word_length=4,
            max_topics=5
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
        print("Étape 2/6: Génération des embeddings")
        chunk_contents = [chunk['content'] for chunk in chunks]
        embeddings = self.embeddings.generate_embeddings_batch(
            chunk_contents,
            batch_size=self.config['embeddings']['batch_size']
        )
        print(f"✓ {len(embeddings)} embeddings générés\n")
        
        # Étape 3: Extraction des topics
        print("Étape 3/6: Extraction des topics et concepts")
        all_topics = self.topic_extractor.get_all_unique_topics(chunks)
        chunk_topics = self.topic_extractor.extract_topics_batch(chunks)
        print(f"✓ {len(all_topics)} topics uniques identifiés\n")
        
        # Étape 4: Insertion dans Neptune
        print("Étape 4/6: Insertion des métadonnées dans Neptune")
        self._insert_to_neptune(document_data, chunks, all_topics, chunk_topics)
        print()
        
        # Étape 5: Insertion dans OpenSearch
        print("Étape 5/6: Insertion des embeddings dans OpenSearch")
        self._insert_to_opensearch(chunks, embeddings)
        print()
        
        # Étape 6: Export ou visualisation
        if self.dry_run:
            print("Étape 6/6: Export des requêtes en CSV")
            self._export_dry_run()
        else:
            print("Étape 6/6: Génération de la visualisation du graphe")
            output_dir = self.config['output']['results_dir']
            os.makedirs(output_dir, exist_ok=True)
            graph_image = os.path.join(output_dir, f'neptune_graph_{document_data["id"]}.png')
            self._generate_graph_visualization_from_data(document_data, chunks, all_topics, chunk_topics)
            print(f"✓ Visualisation du graphe Neptune: {graph_image}")
        
        print(f"\n{'='*60}")
        print("✓ Traitement terminé avec succès")
        print(f"{'='*60}\n")
    
    def _insert_to_neptune(self, document_data: Dict[str, Any], chunks: List[Dict[str, Any]], 
                           all_topics: Dict[str, Dict[str, Any]], chunk_topics: Dict[str, Set[str]]):
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
        
        # Insertion des topics (nœuds partagés)
        for topic_id, topic_data in tqdm(all_topics.items(), desc="Insertion topics Neptune"):
            if self.dry_run:
                query = f"MERGE (t:Topic {{id: '{topic_id}', name: '{topic_data['name']}', type: '{topic_data['type']}'}})"
                self.neptune_queries.append({
                    'query_type': 'MERGE_TOPIC',
                    'query': query,
                    'parameters': topic_data
                })
            else:
                # MERGE pour éviter les doublons entre documents
                self.neptune.merge_topic(topic_id, topic_data['name'], topic_data['type'])
        
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
                
                # Relation Document -> Chunk
                query = f"MATCH (d:Document {{id: '{chunk['document_id']}'}}), (c:Chunk {{id: '{chunk['id']}'}}) CREATE (d)-[:HAS_CHUNK]->(c)"
                self.neptune_queries.append({
                    'query_type': 'CREATE_RELATIONSHIP',
                    'query': query,
                    'parameters': {}
                })
                
                # Relations Chunk -> Topic
                if chunk['id'] in chunk_topics:
                    for topic_id in chunk_topics[chunk['id']]:
                        query = f"MATCH (c:Chunk {{id: '{chunk['id']}'}}), (t:Topic {{id: '{topic_id}'}}) CREATE (c)-[:ABOUT]->(t)"
                        self.neptune_queries.append({
                            'query_type': 'CREATE_RELATIONSHIP',
                            'query': query,
                            'parameters': {'relationship': 'ABOUT'}
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
                
                # Créer les relations avec les topics
                if chunk['id'] in chunk_topics:
                    for topic_id in chunk_topics[chunk['id']]:
                        self.neptune.create_relationship(chunk['id'], topic_id, 'ABOUT')
        
        print(f"✓ {len(chunks)} chunks et {len(all_topics)} topics insérés dans Neptune")
    
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
        
        # Récupérer le nom du document depuis la première requête
        doc_name = "unknown"
        for query in self.neptune_queries:
            if query['query_type'] == 'CREATE_DOCUMENT':
                doc_name = query['parameters']['id']
                break
        
        # Export Neptune
        neptune_file = os.path.join(output_dir, f'neptune_inserts_{doc_name}.csv')
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
        opensearch_file = os.path.join(output_dir, f'opensearch_inserts_{doc_name}.csv')
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
        
        # Générer la visualisation du graphe Neptune
        graph_image = os.path.join(output_dir, f'neptune_graph_{doc_name}.png')
        self._generate_graph_visualization(graph_image)
        print(f"✓ Visualisation du graphe Neptune: {graph_image}")
    
    def _generate_graph_visualization(self, output_path: str):
        """
        Génère une visualisation PNG du graphe Neptune
        
        Args:
            output_path: Chemin de sortie pour l'image PNG
        """
        # Créer un graphe dirigé
        G = nx.DiGraph()
        
        # Dictionnaires pour stocker les informations
        node_types = {}
        node_labels = {}
        edges_to_add = []
        
        # Première passe : créer tous les nœuds
        for query in self.neptune_queries:
            query_type = query['query_type']
            
            if query_type == 'CREATE_DOCUMENT':
                params = query['parameters']
                doc_id = params['id']
                G.add_node(doc_id)
                node_types[doc_id] = 'Document'
                node_labels[doc_id] = f"[Document]\n{params['title']}"
            
            elif query_type == 'CREATE_CHUNK':
                params = query['parameters']
                chunk_id = params['id']
                G.add_node(chunk_id)
                node_types[chunk_id] = 'Chunk'
                node_labels[chunk_id] = f"[Chunk]\n{chunk_id}\nPage {params['metadata']['page']}"
            
            elif query_type == 'MERGE_TOPIC':
                params = query['parameters']
                topic_id = params['id']
                G.add_node(topic_id)
                node_types[topic_id] = 'Topic'
                node_labels[topic_id] = f"[Topic]\n{params['name']}"
            
            elif query_type == 'CREATE_ANNOTATION':
                params = query['parameters']
                ann_id = query['query'].split("'")[1]  # Extraire l'ID de l'annotation
                G.add_node(ann_id)
                node_types[ann_id] = 'Annotation'
                node_labels[ann_id] = f"[{params['type']}]\n{params['value']}"
        
        # Deuxième passe : créer les relations
        current_chunk = None
        for query in self.neptune_queries:
            query_type = query['query_type']
            query_str = query['query']
            
            if query_type == 'CREATE_CHUNK':
                current_chunk = query['parameters']['id']
            
            elif query_type == 'CREATE_RELATIONSHIP':
                if 'HAS_CHUNK' in query_str:
                    # Extraire doc_id et chunk_id de la requête
                    parts = query_str.split("'")
                    if len(parts) >= 4:
                        doc_id = parts[1]
                        chunk_id = parts[3]
                        if doc_id in G.nodes and chunk_id in G.nodes:
                            edges_to_add.append((doc_id, chunk_id, 'HAS_CHUNK'))
                
                elif 'ABOUT' in query_str:
                    # Relation Chunk -> Topic
                    parts = query_str.split("'")
                    if len(parts) >= 4:
                        chunk_id = parts[1]
                        topic_id = parts[3]
                        if chunk_id in G.nodes and topic_id in G.nodes:
                            edges_to_add.append((chunk_id, topic_id, 'ABOUT'))
                
                elif 'HAS_ANNOTATION' in query_str and current_chunk:
                    # Extraire chunk_id et annotation_id de la requête
                    parts = query_str.split("'")
                    if len(parts) >= 4:
                        chunk_id = parts[1]
                        ann_id = parts[3]
                        if chunk_id in G.nodes and ann_id in G.nodes:
                            edges_to_add.append((chunk_id, ann_id, 'HAS_ANNOTATION'))
        
        # Ajouter toutes les arêtes
        for source, target, label in edges_to_add:
            G.add_edge(source, target, label=label)
        
        # Créer la figure avec une taille adaptée
        plt.figure(figsize=(28, 18))
        
        # Séparer les nœuds par type pour un meilleur positionnement
        documents = [n for n in G.nodes() if node_types.get(n) == 'Document']
        chunks = [n for n in G.nodes() if node_types.get(n) == 'Chunk']
        topics = [n for n in G.nodes() if node_types.get(n) == 'Topic']
        annotations = [n for n in G.nodes() if node_types.get(n) == 'Annotation']
        
        pos = {}
        
        # Positionner le document en haut au centre
        for i, doc in enumerate(documents):
            pos[doc] = (0, 3)
        
        # Positionner les chunks au niveau 2
        chunk_spacing = 5 if len(chunks) > 0 else 1
        for i, chunk in enumerate(chunks):
            x = (i - len(chunks)/2) * chunk_spacing
            pos[chunk] = (x, 2)
        
        # Positionner les topics au niveau 1 (partagés entre chunks)
        topic_spacing = 4
        for i, topic in enumerate(topics):
            x = (i - len(topics)/2) * topic_spacing
            pos[topic] = (x, 1)
        
        # Positionner les annotations en bas
        ann_spacing = 1.5
        for i, ann in enumerate(annotations):
            # Grouper les annotations par chunk
            chunk_parent = None
            for source, target, label in edges_to_add:
                if target == ann and label == 'HAS_ANNOTATION':
                    chunk_parent = source
                    break
            
            if chunk_parent and chunk_parent in pos:
                chunk_x = pos[chunk_parent][0]
                offset = (i % 3 - 1) * ann_spacing
                pos[ann] = (chunk_x + offset, 0)
            else:
                pos[ann] = (i * ann_spacing, 0)
        
        # Définir les couleurs par type de nœud
        color_map = {
            'Document': '#FF6B6B',
            'Chunk': '#4ECDC4',
            'Topic': '#FFD93D',  # Jaune pour les topics
            'Annotation': '#95E1D3'
        }
        
        # Préparer les couleurs et tailles des nœuds
        node_colors = [color_map.get(node_types.get(node, 'Unknown'), '#CCCCCC') for node in G.nodes()]
        node_sizes = [
            5000 if node_types.get(node) == 'Document' 
            else 3500 if node_types.get(node) == 'Chunk'
            else 3000 if node_types.get(node) == 'Topic'
            else 2000 
            for node in G.nodes()
        ]
        
        # Dessiner les nœuds
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, 
                               alpha=0.9, edgecolors='black', linewidths=2)
        
        # Dessiner les arêtes avec des styles différents
        has_chunk_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('label') == 'HAS_CHUNK']
        about_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('label') == 'ABOUT']
        has_annotation_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('label') == 'HAS_ANNOTATION']
        
        nx.draw_networkx_edges(G, pos, edgelist=has_chunk_edges, edge_color='#FF6B6B', 
                               arrows=True, arrowsize=25, arrowstyle='->', width=3, alpha=0.7,
                               connectionstyle='arc3,rad=0.1')
        
        nx.draw_networkx_edges(G, pos, edgelist=about_edges, edge_color='#FFD93D', 
                               arrows=True, arrowsize=20, arrowstyle='->', width=2.5, alpha=0.8,
                               connectionstyle='arc3,rad=0.15')
        
        nx.draw_networkx_edges(G, pos, edgelist=has_annotation_edges, edge_color='#4ECDC4', 
                               arrows=True, arrowsize=20, arrowstyle='->', width=2, alpha=0.6,
                               connectionstyle='arc3,rad=0.1')
        
        # Dessiner les labels des nœuds
        nx.draw_networkx_labels(G, pos, node_labels, font_size=8, font_weight='bold', 
                               font_family='sans-serif')
        
        # Ajouter une légende
        legend_elements = [
            mpatches.Patch(color='#FF6B6B', label='Document (1 nœud)'),
            mpatches.Patch(color='#4ECDC4', label=f'Chunks ({len(chunks)} nœuds)'),
            mpatches.Patch(color='#FFD93D', label=f'Topics ({len(topics)} nœuds - PARTAGÉS)'),
            mpatches.Patch(color='#95E1D3', label=f'Annotations ({len(annotations)} nœuds)')
        ]
        plt.legend(handles=legend_elements, loc='upper left', fontsize=14, framealpha=0.9)
        
        # Titre et statistiques
        stats_text = f"Total: {len(G.nodes())} nœuds, {len(G.edges())} relations"
        plt.title(f'Graphe Neptune - Structure du Document avec Topics\n{stats_text}', 
                 fontsize=18, fontweight='bold', pad=30)
        
        # Ajouter une note en bas
        plt.text(0.5, -0.15, 
                'Rouge: Document → Chunks | Jaune: Chunks → Topics (PARTAGÉS) | Bleu: Chunks → Annotations',
                ha='center', va='top', transform=plt.gca().transAxes,
                fontsize=12, style='italic', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Supprimer les axes
        plt.axis('off')
        
        # Ajuster les marges
        plt.tight_layout()
        
        # Sauvegarder
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
    
    def _generate_graph_visualization_from_data(self, document_data: Dict[str, Any], chunks: List[Dict[str, Any]]):
        """
        Génère une visualisation du graphe à partir des données (mode non-dry-run)
        
        Args:
            document_data: Données du document
            chunks: Liste des chunks
        """
        output_dir = self.config['output']['results_dir']
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f'neptune_graph_{document_data["id"]}.png')
        
        # Créer un graphe dirigé
        G = nx.DiGraph()
        
        # Dictionnaires pour stocker les informations
        node_types = {}
        node_labels = {}
        
        # Ajouter le document
        doc_id = document_data['id']
        G.add_node(doc_id)
        node_types[doc_id] = 'Document'
        node_labels[doc_id] = f"Document\n{document_data['title']}"
        
        # Ajouter les chunks et leurs annotations
        for chunk in chunks:
            chunk_id = chunk['id']
            G.add_node(chunk_id)
            node_types[chunk_id] = 'Chunk'
            node_labels[chunk_id] = f"{chunk_id}\nPage {chunk['metadata']['page']}"
            
            # Relation Document -> Chunk
            G.add_edge(doc_id, chunk_id, label='HAS_CHUNK')
            
            # Ajouter les annotations
            for annotation in chunk.get('annotations', []):
                ann_id = f"{chunk_id}_ann_{annotation['type']}"
                G.add_node(ann_id)
                node_types[ann_id] = 'Annotation'
                node_labels[ann_id] = f"{annotation['type']}\n{annotation['value']}"
                
                # Relation Chunk -> Annotation
                G.add_edge(chunk_id, ann_id, label='HAS_ANNOTATION')
        
        # Créer la figure
        plt.figure(figsize=(24, 16))
        
        # Positionner les nœuds
        documents = [n for n in G.nodes() if node_types.get(n) == 'Document']
        chunks_nodes = [n for n in G.nodes() if node_types.get(n) == 'Chunk']
        annotations = [n for n in G.nodes() if node_types.get(n) == 'Annotation']
        
        pos = {}
        
        # Document en haut
        for i, doc in enumerate(documents):
            pos[doc] = (0, 2)
        
        # Chunks au milieu
        chunk_spacing = 4 if len(chunks_nodes) > 0 else 1
        for i, chunk in enumerate(chunks_nodes):
            x = (i - len(chunks_nodes)/2) * chunk_spacing
            pos[chunk] = (x, 1)
        
        # Annotations en bas
        ann_spacing = 1.5
        for i, ann in enumerate(annotations):
            # Trouver le chunk parent
            chunk_parent = None
            for source, target in G.edges():
                if target == ann:
                    chunk_parent = source
                    break
            
            if chunk_parent and chunk_parent in pos:
                chunk_x = pos[chunk_parent][0]
                offset = (i % 3 - 1) * ann_spacing
                pos[ann] = (chunk_x + offset, 0)
            else:
                pos[ann] = (i * ann_spacing, 0)
        
        # Couleurs
        color_map = {
            'Document': '#FF6B6B',
            'Chunk': '#4ECDC4',
            'Annotation': '#95E1D3'
        }
        
        node_colors = [color_map.get(node_types.get(node, 'Unknown'), '#CCCCCC') for node in G.nodes()]
        node_sizes = [4000 if node_types.get(node) == 'Document' else 3000 if node_types.get(node) == 'Chunk' else 2000 for node in G.nodes()]
        
        # Dessiner
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, 
                               alpha=0.9, edgecolors='black', linewidths=2)
        
        has_chunk_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('label') == 'HAS_CHUNK']
        has_annotation_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('label') == 'HAS_ANNOTATION']
        
        nx.draw_networkx_edges(G, pos, edgelist=has_chunk_edges, edge_color='#FF6B6B', 
                               arrows=True, arrowsize=25, arrowstyle='->', width=3, alpha=0.7)
        
        nx.draw_networkx_edges(G, pos, edgelist=has_annotation_edges, edge_color='#4ECDC4', 
                               arrows=True, arrowsize=20, arrowstyle='->', width=2, alpha=0.6)
        
        nx.draw_networkx_labels(G, pos, node_labels, font_size=9, font_weight='bold')
        
        # Légende
        legend_elements = [
            mpatches.Patch(color='#FF6B6B', label='Document (1 nœud)'),
            mpatches.Patch(color='#4ECDC4', label=f'Chunks ({len(chunks_nodes)} nœuds)'),
            mpatches.Patch(color='#95E1D3', label=f'Annotations ({len(annotations)} nœuds)')
        ]
        plt.legend(handles=legend_elements, loc='upper left', fontsize=14, framealpha=0.9)
        
        stats_text = f"Total: {len(G.nodes())} nœuds, {len(G.edges())} relations"
        plt.title(f'Graphe Neptune - {document_data["title"]}\n{stats_text}', 
                 fontsize=18, fontweight='bold', pad=30)
        
        plt.text(0.5, -0.15, 
                'Rouge: Document → Chunks | Bleu: Chunks → Annotations',
                ha='center', va='top', transform=plt.gca().transAxes,
                fontsize=12, style='italic', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.axis('off')
        plt.tight_layout()
        
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()

    
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
