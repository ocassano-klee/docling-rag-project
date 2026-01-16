"""
Module pour l'interaction avec AWS OpenSearch
"""

from opensearchpy import OpenSearch, RequestsHttpConnection
from typing import List, Dict, Any
import json


class OpenSearchClient:
    """Client pour interagir avec AWS OpenSearch"""
    
    def __init__(self, endpoint: str, index_name: str, use_iam: bool = True, 
                 username: str = None, password: str = None):
        """
        Initialise le client OpenSearch
        
        Args:
            endpoint: Endpoint du domaine OpenSearch
            index_name: Nom de l'index
            use_iam: Utiliser l'authentification IAM
            username: Nom d'utilisateur (si pas IAM)
            password: Mot de passe (si pas IAM)
        """
        self.endpoint = endpoint.replace("https://", "").replace("http://", "")
        self.index_name = index_name
        self.use_iam = use_iam
        
        # Configuration du client
        client_config = {
            "hosts": [{"host": self.endpoint, "port": 443}],
            "http_compress": True,
            "use_ssl": True,
            "verify_certs": True,
            "ssl_assert_hostname": False,
            "ssl_show_warn": False,
            "connection_class": RequestsHttpConnection,
        }
        
        if use_iam:
            # Pour IAM, il faudrait ajouter AWS4Auth
            # from requests_aws4auth import AWS4Auth
            # import boto3
            # credentials = boto3.Session().get_credentials()
            # awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, 
            #                    region, 'es', session_token=credentials.token)
            # client_config["http_auth"] = awsauth
            pass
        else:
            if username and password:
                client_config["http_auth"] = (username, password)
        
        self.client = OpenSearch(**client_config)
        
    def create_index(self, dimension: int = 384):
        """
        Crée l'index avec mapping pour les vecteurs
        
        Args:
            dimension: Dimension des vecteurs d'embedding
        """
        index_body = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100
                }
            },
            "mappings": {
                "properties": {
                    "chunk_id": {"type": "keyword"},
                    "document_id": {"type": "keyword"},
                    "content": {"type": "text"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": dimension,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib"
                        }
                    },
                    "metadata": {
                        "properties": {
                            "page": {"type": "integer"},
                            "type": {"type": "keyword"},
                            "length": {"type": "integer"}
                        }
                    }
                }
            }
        }
        
        try:
            if self.client.indices.exists(index=self.index_name):
                print(f"Index {self.index_name} existe déjà")
            else:
                self.client.indices.create(index=self.index_name, body=index_body)
                print(f"✓ Index {self.index_name} créé")
        except Exception as e:
            print(f"Erreur lors de la création de l'index: {e}")
    
    def index_chunk(self, chunk_id: str, document_id: str, content: str, 
                   embedding: List[float], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Indexe un chunk avec son embedding dans OpenSearch
        
        Args:
            chunk_id: Identifiant du chunk
            document_id: Identifiant du document
            content: Contenu textuel
            embedding: Vecteur d'embedding
            metadata: Métadonnées du chunk
            
        Returns:
            Document pour dry-run
        """
        document = {
            "chunk_id": chunk_id,
            "document_id": document_id,
            "content": content,
            "embedding": embedding,
            "metadata": metadata
        }
        
        try:
            response = self.client.index(
                index=self.index_name,
                id=chunk_id,
                body=document
            )
            print(f"✓ Chunk indexé: {chunk_id}")
            return document
            
        except Exception as e:
            print(f"Erreur lors de l'indexation: {e}")
            return document
    
    def search_similar(self, query_embedding: List[float], top_k: int = 5, 
                      filter_chunk_ids: List[str] = None) -> List[Dict[str, Any]]:
        """
        Recherche les chunks les plus similaires par similarité cosinus
        
        Args:
            query_embedding: Vecteur de la question
            top_k: Nombre de résultats à retourner
            filter_chunk_ids: Liste optionnelle de chunk_ids à filtrer
            
        Returns:
            Liste des chunks les plus similaires avec scores
        """
        # Construction de la requête KNN
        query_body = {
            "size": top_k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": top_k
                    }
                }
            }
        }
        
        # Ajout du filtre si fourni
        if filter_chunk_ids:
            query_body["query"] = {
                "bool": {
                    "must": [
                        {
                            "knn": {
                                "embedding": {
                                    "vector": query_embedding,
                                    "k": top_k
                                }
                            }
                        }
                    ],
                    "filter": [
                        {
                            "terms": {
                                "chunk_id": filter_chunk_ids
                            }
                        }
                    ]
                }
            }
        
        try:
            response = self.client.search(
                index=self.index_name,
                body=query_body
            )
            
            results = []
            for hit in response["hits"]["hits"]:
                results.append({
                    "chunk_id": hit["_source"]["chunk_id"],
                    "document_id": hit["_source"]["document_id"],
                    "content": hit["_source"]["content"],
                    "metadata": hit["_source"]["metadata"],
                    "score": hit["_score"]
                })
            
            return results
            
        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
            return []
    
    def generate_api_request(self, action: str, chunk_id: str = None, 
                           document: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Génère une requête API formatée pour export CSV
        
        Args:
            action: Type d'action (index, search, etc.)
            chunk_id: Identifiant du chunk
            document: Document à indexer
            
        Returns:
            Dictionnaire représentant la requête API
        """
        if action == "index":
            return {
                "method": "PUT",
                "path": f"/{self.index_name}/_doc/{chunk_id}",
                "body": json.dumps(document, ensure_ascii=False)
            }
        
        elif action == "search":
            return {
                "method": "POST",
                "path": f"/{self.index_name}/_search",
                "body": json.dumps(document, ensure_ascii=False)
            }
        
        return {}
    
    def bulk_index(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Indexe plusieurs chunks en batch
        
        Args:
            chunks: Liste de chunks à indexer
            
        Returns:
            Nombre de chunks indexés
        """
        from opensearchpy import helpers
        
        actions = []
        for chunk in chunks:
            action = {
                "_index": self.index_name,
                "_id": chunk["chunk_id"],
                "_source": chunk
            }
            actions.append(action)
        
        try:
            success, failed = helpers.bulk(self.client, actions)
            print(f"✓ {success} chunks indexés en batch")
            if failed:
                print(f"✗ {len(failed)} échecs")
            return success
            
        except Exception as e:
            print(f"Erreur lors de l'indexation batch: {e}")
            return 0
