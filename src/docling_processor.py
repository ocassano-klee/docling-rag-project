"""
Module pour le traitement des documents PDF avec Docling
"""

from docling.document_converter import DocumentConverter
from typing import List, Dict, Any
import os


class DoclingProcessor:
    """Traite les documents PDF avec Docling et génère des chunks"""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50, min_chunk_size: int = 100):
        """
        Initialise le processeur Docling
        
        Args:
            chunk_size: Taille maximale d'un chunk en caractères
            chunk_overlap: Chevauchement entre chunks
            min_chunk_size: Taille minimale d'un chunk
        """
        # Configuration avec layout detection (télécharge les modèles au premier lancement)
        self.converter = DocumentConverter()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Traite un fichier PDF et extrait son contenu structuré
        
        Args:
            pdf_path: Chemin vers le fichier PDF
            
        Returns:
            Dictionnaire contenant le document structuré
        """
        print(f"Traitement du PDF: {pdf_path}")
        
        # Conversion du PDF
        result = self.converter.convert(pdf_path)
        
        # Extraction des métadonnées
        document_data = {
            "id": os.path.splitext(os.path.basename(pdf_path))[0],
            "title": os.path.basename(pdf_path),
            "source": pdf_path,
            "pages": [],
            "metadata": {}
        }
        
        # Extraction du contenu - l'API Docling retourne le document directement
        doc = result.document
        
        # Extraire le texte complet par page en utilisant iterate_items()
        page_texts = {}
        
        for item, level in doc.iterate_items():
            # Vérifier si l'item a du texte et des informations de provenance
            if hasattr(item, 'text') and item.text and hasattr(item, 'prov') and item.prov:
                for prov_item in item.prov:
                    page_no = prov_item.page_no
                    if page_no not in page_texts:
                        page_texts[page_no] = []
                    
                    element = {
                        "type": item.__class__.__name__,
                        "content": item.text,
                        "bbox": prov_item.bbox if hasattr(prov_item, 'bbox') else None
                    }
                    page_texts[page_no].append(element)
        
        # Extraire les tables séparément
        if hasattr(doc, 'tables') and doc.tables:
            print(f"Extraction de {len(doc.tables)} table(s) détectée(s)")
            for table in doc.tables:
                if hasattr(table, 'prov') and table.prov:
                    for prov_item in table.prov:
                        page_no = prov_item.page_no
                        if page_no not in page_texts:
                            page_texts[page_no] = []
                        
                        # Extraire le contenu de la table
                        table_text = self._extract_table_text(table)
                        if table_text:
                            element = {
                                "type": "TableItem",
                                "content": table_text,
                                "bbox": prov_item.bbox if hasattr(prov_item, 'bbox') else None
                            }
                            page_texts[page_no].append(element)
        
        # Si aucune page n'a été extraite avec iterate_items, utiliser export_to_text comme fallback
        if not page_texts:
            print("Aucun contenu extrait avec iterate_items, utilisation de export_to_text()")
            full_text = doc.export_to_text()
            if full_text:
                # Créer une seule page avec tout le texte
                page_texts[1] = [{
                    "type": "Text",
                    "content": full_text,
                    "bbox": None
                }]
        
        # Construire les données de page
        for page_no in sorted(page_texts.keys()):
            elements = page_texts[page_no]
            page_content = "\n".join([el["content"] for el in elements if el["content"]])
            
            page_data = {
                "page_number": page_no,
                "content": page_content,
                "elements": elements
            }
            document_data["pages"].append(page_data)
        
        return document_data
    
    def create_chunks(self, document_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Crée des chunks à partir du document structuré
        
        Args:
            document_data: Document structuré issu de process_pdf
            
        Returns:
            Liste de chunks avec métadonnées
        """
        chunks = []
        chunk_id = 0
        
        for page in document_data["pages"]:
            page_num = page["page_number"]
            
            # Traitement par élément pour préserver la structure
            for element in page["elements"]:
                content = element["content"].strip()
                
                if len(content) < self.min_chunk_size:
                    continue
                
                # Si l'élément est trop grand, on le découpe
                if len(content) > self.chunk_size:
                    sub_chunks = self._split_text(content)
                    for sub_chunk in sub_chunks:
                        chunk = self._create_chunk(
                            chunk_id=f"{document_data['id']}_chunk_{chunk_id:04d}",
                            document_id=document_data["id"],
                            content=sub_chunk,
                            page_number=page_num,
                            element_type=element["type"],
                            bbox=element.get("bbox")
                        )
                        chunks.append(chunk)
                        chunk_id += 1
                else:
                    chunk = self._create_chunk(
                        chunk_id=f"{document_data['id']}_chunk_{chunk_id:04d}",
                        document_id=document_data["id"],
                        content=content,
                        page_number=page_num,
                        element_type=element["type"],
                        bbox=element.get("bbox")
                    )
                    chunks.append(chunk)
                    chunk_id += 1
        
        print(f"Créé {len(chunks)} chunks pour le document {document_data['id']}")
        return chunks
    
    def _split_text(self, text: str) -> List[str]:
        """
        Découpe un texte en chunks avec chevauchement
        
        Args:
            text: Texte à découper
            
        Returns:
            Liste de chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Essayer de couper à un espace pour ne pas couper les mots
            if end < len(text):
                last_space = chunk.rfind(' ')
                if last_space > self.chunk_size // 2:
                    chunk = chunk[:last_space]
                    end = start + last_space
            
            chunks.append(chunk.strip())
            start = end - self.chunk_overlap
        
        return chunks
    
    def _create_chunk(self, chunk_id: str, document_id: str, content: str, 
                     page_number: int, element_type: str, bbox: Any = None) -> Dict[str, Any]:
        """
        Crée un chunk avec ses métadonnées et annotations
        
        Args:
            chunk_id: Identifiant unique du chunk
            document_id: Identifiant du document parent
            content: Contenu textuel du chunk
            page_number: Numéro de page
            element_type: Type d'élément (paragraph, title, table, etc.)
            bbox: Bounding box de l'élément
            
        Returns:
            Dictionnaire représentant le chunk
        """
        chunk = {
            "id": chunk_id,
            "document_id": document_id,
            "content": content,
            "metadata": {
                "page": page_number,
                "type": element_type,
                "bbox": bbox,
                "length": len(content)
            },
            "annotations": self._generate_annotations(content, element_type, page_number)
        }
        
        return chunk
    
    def _generate_annotations(self, content: str, element_type: str, page_number: int) -> List[Dict[str, Any]]:
        """
        Génère des annotations contextuelles pour un chunk
        
        Args:
            content: Contenu du chunk
            element_type: Type d'élément
            page_number: Numéro de page
            
        Returns:
            Liste d'annotations
        """
        annotations = []
        
        # Annotation de type
        annotations.append({
            "type": "element_type",
            "value": element_type,
            "context": f"Ce contenu est de type {element_type}"
        })
        
        # Annotation de localisation
        annotations.append({
            "type": "location",
            "value": f"page_{page_number}",
            "context": f"Ce contenu se trouve à la page {page_number}"
        })
        
        # Annotation de longueur
        length_category = "court" if len(content) < 200 else "moyen" if len(content) < 400 else "long"
        annotations.append({
            "type": "length",
            "value": length_category,
            "context": f"Ce contenu est de longueur {length_category}"
        })
        
        # Détection de mots-clés importants (exemple simple)
        keywords = ["data fabric", "architecture", "ingestion", "metadata", "pipeline"]
        found_keywords = [kw for kw in keywords if kw.lower() in content.lower()]
        
        if found_keywords:
            annotations.append({
                "type": "keywords",
                "value": ", ".join(found_keywords),
                "context": f"Contient les concepts: {', '.join(found_keywords)}"
            })
        
        return annotations
    
    def _extract_table_text(self, table) -> str:
        """
        Extrait le texte d'une table Docling
        
        Args:
            table: Objet TableItem de Docling
            
        Returns:
            Texte formaté de la table
        """
        if not hasattr(table, 'data') or not table.data:
            return ""
        
        table_data = table.data
        
        # Vérifier si la table a des cellules
        if not hasattr(table_data, 'table_cells') or not table_data.table_cells:
            return ""
        
        # Extraire le texte de toutes les cellules
        texts = []
        for cell in table_data.table_cells:
            if hasattr(cell, 'text') and cell.text:
                texts.append(cell.text)
        
        # Joindre tous les textes avec des espaces
        return " | ".join(texts) if texts else ""
