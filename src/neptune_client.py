"""
Module pour l'interaction avec AWS Neptune
"""

from gremlin_python.driver import client, serializer
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from typing import List, Dict, Any
import json


class NeptuneClient:
    """Client pour interagir avec AWS Neptune"""
    
    def __init__(self, endpoint: str, port: int = 8182, use_iam: bool = True):
        """
        Initialise le client Neptune
        
        Args:
            endpoint: Endpoint du cluster Neptune
            port: Port de connexion
            use_iam: Utiliser l'authentification IAM
        """
        self.endpoint = endpoint
        self.port = port
        self.use_iam = use_iam
        
        # Construction de l'URL de connexion
        protocol = "wss" if use_iam else "ws"
        self.connection_url = f"{protocol}://{endpoint}:{port}/gremlin"
        
        self.client = None
        self.g = None
        
    def connect(self):
        """Établit la connexion à Neptune"""
        print(f"Connexion à Neptune: {self.connection_url}")
        
        try:
            self.client = client.Client(
                self.connection_url,
                'g',
                message_serializer=serializer.GraphSONSerializersV3d0()
            )
            
            # Test de connexion
            result = self.client.submit("g.V().limit(1)").all().result()
            print("✓ Connexion Neptune établie")
            
        except Exception as e:
            print(f"✗ Erreur de connexion Neptune: {e}")
            raise
    
    def close(self):
        """Ferme la connexion"""
        if self.client:
            self.client.close()
            print("Connexion Neptune fermée")
    
    def insert_document(self, document_id: str, title: str, source: str) -> str:
        """
        Insère un nœud Document dans Neptune
        
        Args:
            document_id: Identifiant du document
            title: Titre du document
            source: Source du document
            
        Returns:
            Query Cypher pour dry-run
        """
        query = f"""
        g.addV('Document')
         .property('id', '{document_id}')
         .property('title', '{title}')
         .property('source', '{source}')
        """
        
        if self.client:
            self.client.submit(query).all().result()
            print(f"✓ Document inséré: {document_id}")
        
        return query
    
    def insert_chunk(self, chunk: Dict[str, Any]) -> str:
        """
        Insère un nœud Chunk et ses relations dans Neptune
        
        Args:
            chunk: Dictionnaire contenant les données du chunk
            
        Returns:
            Query Cypher pour dry-run
        """
        chunk_id = chunk["id"]
        document_id = chunk["document_id"]
        content = chunk["content"].replace("'", "\\'")[:500]  # Limiter la taille
        page = chunk["metadata"]["page"]
        element_type = chunk["metadata"]["type"]
        
        # Création du chunk
        query = f"""
        g.addV('Chunk')
         .property('id', '{chunk_id}')
         .property('document_id', '{document_id}')
         .property('content', '{content}')
         .property('page', {page})
         .property('type', '{element_type}')
        """
        
        if self.client:
            self.client.submit(query).all().result()
        
        # Relation avec le document
        relation_query = f"""
        g.V().has('Document', 'id', '{document_id}')
         .addE('HAS_CHUNK')
         .to(g.V().has('Chunk', 'id', '{chunk_id}'))
        """
        
        if self.client:
            self.client.submit(relation_query).all().result()
        
        full_query = query + "\n" + relation_query
        
        # Insertion des annotations
        for annotation in chunk.get("annotations", []):
            ann_query = self.insert_annotation(chunk_id, annotation)
            full_query += "\n" + ann_query
        
        if self.client:
            print(f"✓ Chunk inséré: {chunk_id}")
        
        return full_query
    
    def insert_annotation(self, chunk_id: str, annotation: Dict[str, Any]) -> str:
        """
        Insère une annotation et la relie à un chunk
        
        Args:
            chunk_id: Identifiant du chunk
            annotation: Dictionnaire contenant l'annotation
            
        Returns:
            Query Cypher pour dry-run
        """
        ann_type = annotation["type"]
        ann_value = annotation["value"].replace("'", "\\'")
        ann_context = annotation["context"].replace("'", "\\'")
        ann_id = f"{chunk_id}_ann_{ann_type}"
        
        query = f"""
        g.addV('Annotation')
         .property('id', '{ann_id}')
         .property('type', '{ann_type}')
         .property('value', '{ann_value}')
         .property('context', '{ann_context}')
        """
        
        if self.client:
            self.client.submit(query).all().result()
        
        relation_query = f"""
        g.V().has('Chunk', 'id', '{chunk_id}')
         .addE('HAS_ANNOTATION')
         .to(g.V().has('Annotation', 'id', '{ann_id}'))
        """
        
        if self.client:
            self.client.submit(relation_query).all().result()
        
        return query + "\n" + relation_query
    
    def get_chunk_annotations(self, chunk_id: str) -> List[Dict[str, Any]]:
        """
        Récupère les annotations d'un chunk
        
        Args:
            chunk_id: Identifiant du chunk
            
        Returns:
            Liste des annotations
        """
        query = f"""
        g.V().has('Chunk', 'id', '{chunk_id}')
         .outE('HAS_ANNOTATION')
         .inV()
         .valueMap()
        """
        
        if not self.client:
            return []
        
        try:
            results = self.client.submit(query).all().result()
            annotations = []
            
            for result in results:
                annotations.append({
                    "type": result.get("type", [""])[0],
                    "value": result.get("value", [""])[0],
                    "context": result.get("context", [""])[0]
                })
            
            return annotations
            
        except Exception as e:
            print(f"Erreur lors de la récupération des annotations: {e}")
            return []
    
    def get_related_chunks(self, chunk_id: str, max_distance: int = 2) -> List[str]:
        """
        Récupère les chunks liés dans le graphe (pour filtrage)
        
        Args:
            chunk_id: Identifiant du chunk de départ
            max_distance: Distance maximale dans le graphe
            
        Returns:
            Liste d'identifiants de chunks
        """
        query = f"""
        g.V().has('Chunk', 'id', '{chunk_id}')
         .repeat(both().simplePath())
         .times({max_distance})
         .hasLabel('Chunk')
         .values('id')
         .dedup()
        """
        
        if not self.client:
            return []
        
        try:
            results = self.client.submit(query).all().result()
            return list(results)
            
        except Exception as e:
            print(f"Erreur lors de la récupération des chunks liés: {e}")
            return []
    
    def generate_cypher_query(self, operation: str, params: Dict[str, Any]) -> str:
        """
        Génère une requête Cypher formatée pour export CSV
        
        Args:
            operation: Type d'opération (CREATE_DOCUMENT, CREATE_CHUNK, etc.)
            params: Paramètres de la requête
            
        Returns:
            Requête Cypher formatée
        """
        if operation == "CREATE_DOCUMENT":
            return f"""g.addV('Document').property('id', '{params["id"]}').property('title', '{params["title"]}').property('source', '{params["source"]}')"""
        
        elif operation == "CREATE_CHUNK":
            return f"""g.addV('Chunk').property('id', '{params["id"]}').property('document_id', '{params["document_id"]}').property('content', '{params["content"][:100]}...').property('page', {params["page"]})"""
        
        elif operation == "CREATE_ANNOTATION":
            return f"""g.addV('Annotation').property('id', '{params["id"]}').property('type', '{params["type"]}').property('value', '{params["value"]}')"""
        
        return ""
