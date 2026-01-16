"""
Module pour la génération d'embeddings vectoriels
"""

import cohere
import os
from typing import List, Union
import numpy as np
from tqdm import tqdm


class EmbeddingGenerator:
    """Génère des embeddings vectoriels pour les textes"""
    
    def __init__(self, provider: str = "cohere", model_name: str = "embed-multilingual-v3", 
                 api_key: str = None):
        """
        Initialise le générateur d'embeddings
        
        Args:
            provider: Provider d'embeddings ("cohere" ou "sentence-transformers")
            model_name: Nom du modèle à utiliser
            api_key: Clé API (pour Cohere)
        """
        self.provider = provider
        self.model_name = model_name
        
        if provider == "cohere":
            # Récupérer la clé API depuis les paramètres ou variable d'environnement
            self.api_key = api_key or os.getenv("COHERE_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "Clé API Cohere requise. Définissez COHERE_API_KEY dans l'environnement "
                    "ou passez api_key au constructeur."
                )
            
            print(f"Initialisation du client Cohere avec le modèle: {model_name}")
            self.client = cohere.Client(self.api_key)
            
            # Dimensions selon le modèle Cohere
            if "v3" in model_name:
                self.dimension = 1024
            elif "v2" in model_name:
                self.dimension = 768
            else:
                self.dimension = 1024  # Par défaut
                
        else:
            # Fallback sur sentence-transformers
            from sentence_transformers import SentenceTransformer
            print(f"Chargement du modèle sentence-transformers: {model_name}")
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
        
    def generate_embedding(self, text: str, input_type: str = "search_document") -> List[float]:
        """
        Génère un embedding pour un texte unique
        
        Args:
            text: Texte à vectoriser
            input_type: Type d'input pour Cohere ("search_document" ou "search_query")
            
        Returns:
            Liste de floats représentant l'embedding
        """
        if self.provider == "cohere":
            response = self.client.embed(
                texts=[text],
                model=self.model_name,
                input_type=input_type,
                embedding_types=["float"]
            )
            return response.embeddings.float[0]
        else:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 96, 
                                  input_type: str = "search_document") -> List[List[float]]:
        """
        Génère des embeddings pour un batch de textes
        
        Args:
            texts: Liste de textes à vectoriser
            batch_size: Taille des batchs pour le traitement
            input_type: Type d'input pour Cohere ("search_document" ou "search_query")
            
        Returns:
            Liste d'embeddings
        """
        if self.provider == "cohere":
            all_embeddings = []
            
            # Traiter par batch (Cohere a une limite de 96 textes par requête)
            for i in tqdm(range(0, len(texts), batch_size), desc="Génération embeddings"):
                batch = texts[i:i + batch_size]
                
                response = self.client.embed(
                    texts=batch,
                    model=self.model_name,
                    input_type=input_type,
                    embedding_types=["float"]
                )
                
                all_embeddings.extend(response.embeddings.float)
            
            return all_embeddings
        else:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=True,
                convert_to_numpy=True
            )
            return embeddings.tolist()
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calcule la similarité cosinus entre deux embeddings
        
        Args:
            embedding1: Premier embedding
            embedding2: Second embedding
            
        Returns:
            Score de similarité (0 à 1)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Similarité cosinus
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return float(dot_product / (norm1 * norm2))
