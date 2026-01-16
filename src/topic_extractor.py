"""
Module pour l'extraction de topics et concepts depuis les chunks
"""

from typing import List, Dict, Set
import re
from collections import Counter


class TopicExtractor:
    """Extrait des topics et concepts depuis le texte"""
    
    def __init__(self, min_word_length: int = 4, max_topics: int = 5):
        """
        Initialise l'extracteur de topics
        
        Args:
            min_word_length: Longueur minimale d'un mot pour être considéré comme topic
            max_topics: Nombre maximum de topics à extraire par chunk
        """
        self.min_word_length = min_word_length
        self.max_topics = max_topics
        
        # Mots vides français (stop words)
        self.stop_words = {
            'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 'mais',
            'dans', 'pour', 'par', 'sur', 'avec', 'sans', 'sous', 'vers', 'chez',
            'est', 'sont', 'être', 'avoir', 'fait', 'faire', 'peut', 'plus', 'tout',
            'tous', 'toute', 'toutes', 'cette', 'ces', 'son', 'sa', 'ses', 'leur',
            'leurs', 'notre', 'nos', 'votre', 'vos', 'mon', 'ma', 'mes', 'ce', 'cet',
            'qui', 'que', 'quoi', 'dont', 'où', 'comment', 'quand', 'pourquoi',
            'très', 'bien', 'aussi', 'encore', 'déjà', 'jamais', 'toujours', 'souvent',
            'vous', 'nous', 'ils', 'elles', 'lui', 'elle', 'eux', 'je', 'tu', 'il',
            'avez', 'avons', 'ont', 'été', 'était', 'étaient', 'sera', 'seront',
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'
        }
        
        # Dictionnaire de concepts métier (peut être étendu)
        self.business_concepts = {
            'assurance': ['assurance', 'assurances', 'assurantiel', 'assureur'],
            'remboursement': ['remboursement', 'remboursements', 'rembourser', 'remboursé'],
            'dentaire': ['dentaire', 'dentaires', 'dent', 'dents', 'dentiste', 'orthodontie'],
            'santé': ['santé', 'médical', 'médicale', 'soins', 'patient', 'patients'],
            'mutuelle': ['mutuelle', 'mutuelles', 'mutualité', 'mutualités'],
            'contrat': ['contrat', 'contrats', 'contractuel', 'contractuelle'],
            'intervention': ['intervention', 'interventions'],
            'plafond': ['plafond', 'plafonds'],
            'prestation': ['prestation', 'prestations'],
            'bénéficiaire': ['bénéficiaire', 'bénéficiaires'],
            'facture': ['facture', 'factures', 'facturation'],
            'paiement': ['paiement', 'paiements', 'payé', 'payer'],
            'compte': ['compte', 'comptes'],
            'client': ['client', 'clients', 'clientèle'],
            'document': ['document', 'documents', 'documentation'],
            'période': ['période', 'périodes', 'date', 'dates'],
            'montant': ['montant', 'montants', 'somme', 'sommes'],
        }
    
    def extract_topics(self, text: str) -> List[Dict[str, any]]:
        """
        Extrait les topics principaux d'un texte
        
        Args:
            text: Texte à analyser
            
        Returns:
            Liste de topics avec leur score de pertinence
        """
        if not text:
            return []
        
        # Normaliser le texte
        text_lower = text.lower()
        
        # 1. Extraire les concepts métier
        business_topics = self._extract_business_concepts(text_lower)
        
        # 2. Extraire les mots-clés fréquents
        keyword_topics = self._extract_keywords(text_lower)
        
        # 3. Combiner et scorer
        all_topics = {}
        
        # Les concepts métier ont un score plus élevé
        for topic, score in business_topics.items():
            all_topics[topic] = {'name': topic, 'score': score * 2.0, 'type': 'business_concept'}
        
        # Les mots-clés ont un score normal
        for topic, score in keyword_topics.items():
            if topic not in all_topics:
                all_topics[topic] = {'name': topic, 'score': score, 'type': 'keyword'}
        
        # Trier par score et limiter
        sorted_topics = sorted(all_topics.values(), key=lambda x: x['score'], reverse=True)
        return sorted_topics[:self.max_topics]
    
    def _extract_business_concepts(self, text: str) -> Dict[str, float]:
        """
        Extrait les concepts métier prédéfinis
        
        Args:
            text: Texte normalisé en minuscules
            
        Returns:
            Dictionnaire {concept: score}
        """
        concepts = {}
        
        for concept, variations in self.business_concepts.items():
            count = 0
            for variation in variations:
                # Compter les occurrences avec word boundaries
                pattern = r'\b' + re.escape(variation) + r'\b'
                count += len(re.findall(pattern, text))
            
            if count > 0:
                # Score basé sur la fréquence
                concepts[concept] = float(count)
        
        return concepts
    
    def _extract_keywords(self, text: str) -> Dict[str, float]:
        """
        Extrait les mots-clés fréquents
        
        Args:
            text: Texte normalisé en minuscules
            
        Returns:
            Dictionnaire {keyword: score}
        """
        # Extraire les mots (lettres uniquement, avec accents)
        words = re.findall(r'\b[a-zàâäéèêëïîôùûüÿæœç]+\b', text)
        
        # Filtrer les mots courts et les stop words
        filtered_words = [
            word for word in words 
            if len(word) >= self.min_word_length and word not in self.stop_words
        ]
        
        # Compter les fréquences
        word_counts = Counter(filtered_words)
        
        # Retourner les plus fréquents (score = fréquence)
        keywords = {}
        for word, count in word_counts.most_common(10):
            if count >= 2:  # Au moins 2 occurrences
                keywords[word] = float(count)
        
        return keywords
    
    def normalize_topic_id(self, topic_name: str) -> str:
        """
        Normalise un nom de topic en ID
        
        Args:
            topic_name: Nom du topic
            
        Returns:
            ID normalisé
        """
        # Remplacer les caractères spéciaux
        normalized = topic_name.lower()
        normalized = re.sub(r'[àâä]', 'a', normalized)
        normalized = re.sub(r'[éèêë]', 'e', normalized)
        normalized = re.sub(r'[ïî]', 'i', normalized)
        normalized = re.sub(r'[ôö]', 'o', normalized)
        normalized = re.sub(r'[ùûü]', 'u', normalized)
        normalized = re.sub(r'[ÿ]', 'y', normalized)
        normalized = re.sub(r'[ç]', 'c', normalized)
        normalized = re.sub(r'[^a-z0-9]+', '_', normalized)
        normalized = normalized.strip('_')
        
        return f"topic_{normalized}"
    
    def extract_topics_batch(self, chunks: List[Dict[str, any]]) -> Dict[str, Set[str]]:
        """
        Extrait les topics pour un batch de chunks et retourne les relations
        
        Args:
            chunks: Liste de chunks avec leur contenu
            
        Returns:
            Dictionnaire {chunk_id: set(topic_ids)}
        """
        chunk_topics = {}
        
        for chunk in chunks:
            chunk_id = chunk['id']
            content = chunk['content']
            
            # Extraire les topics
            topics = self.extract_topics(content)
            
            # Convertir en IDs
            topic_ids = {self.normalize_topic_id(t['name']) for t in topics}
            
            chunk_topics[chunk_id] = topic_ids
        
        return chunk_topics
    
    def get_all_unique_topics(self, chunks: List[Dict[str, any]]) -> Dict[str, Dict[str, any]]:
        """
        Extrait tous les topics uniques de tous les chunks
        
        Args:
            chunks: Liste de chunks
            
        Returns:
            Dictionnaire {topic_id: {name, type, total_score}}
        """
        all_topics = {}
        
        for chunk in chunks:
            topics = self.extract_topics(chunk['content'])
            
            for topic in topics:
                topic_id = self.normalize_topic_id(topic['name'])
                
                if topic_id not in all_topics:
                    all_topics[topic_id] = {
                        'id': topic_id,
                        'name': topic['name'],
                        'type': topic['type'],
                        'total_score': 0.0,
                        'chunk_count': 0
                    }
                
                all_topics[topic_id]['total_score'] += topic['score']
                all_topics[topic_id]['chunk_count'] += 1
        
        return all_topics
