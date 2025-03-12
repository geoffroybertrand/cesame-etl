import re
from typing import List, Dict, Any, Optional

def chunk_document(
    text: str,
    strategy: str = "semantic",
    chunk_size: int = 800,
    chunk_overlap: int = 100,
    min_chunk_size: int = 200,
    respect_boundaries: bool = True
) -> List[Dict[str, Any]]:
    """
    Découpe un texte en chunks selon la stratégie spécifiée.
    
    Args:
        text: Le texte à découper
        strategy: La stratégie de chunking (semantic, fixed, paragraph)
        chunk_size: La taille cible de chaque chunk (en caractères)
        chunk_overlap: Le chevauchement entre les chunks (en caractères)
        min_chunk_size: La taille minimale d'un chunk
        respect_boundaries: Si True, respecte les frontières naturelles du texte
        
    Returns:
        Une liste de dictionnaires, chacun représentant un chunk avec son texte et ses métadonnées
    """
    if strategy == "paragraph":
        return chunk_by_paragraph(text, chunk_size, chunk_overlap, min_chunk_size)
    elif strategy == "semantic":
        return chunk_semantically(text, chunk_size, chunk_overlap, min_chunk_size, respect_boundaries)
    else:  # fixed
        return chunk_by_fixed_size(text, chunk_size, chunk_overlap, min_chunk_size)

def chunk_by_fixed_size(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
    min_chunk_size: int = 200
) -> List[Dict[str, Any]]:
    """Découpe le texte en morceaux de taille fixe"""
    chunks = []
    
    # Normaliser les sauts de ligne
    text = re.sub(r'\r\n', '\n', text)
    
    start = 0
    text_length = len(text)
    
    while start < text_length:
        # Déterminer la fin du chunk actuel
        end = min(start + chunk_size, text_length)
        
        # Si ce n'est pas le dernier chunk et qu'on ne respecte pas la fin d'une phrase
        if end < text_length:
            # Chercher la fin de phrase la plus proche
            punct_pos = max(
                text.rfind('. ', start, end),
                text.rfind('? ', start, end),
                text.rfind('! ', start, end),
                text.rfind('\n\n', start, end)
            )
            
            if punct_pos > start + min_chunk_size:
                end = punct_pos + 1  # +1 pour inclure le point
        
        # Extraire le chunk
        chunk_text = text[start:end].strip()
        
        # Ajouter le chunk s'il n'est pas vide et suffisamment grand
        if chunk_text and len(chunk_text) >= min_chunk_size:
            # Estimer la page à partir de la position dans le texte
            page_start = (start // 2000) + 1  # Approximation grossière: ~2000 chars par page
            page_end = (end // 2000) + 1
            
            chunks.append({
                "text": chunk_text,
                "page_range": f"{page_start}-{page_end}",
                "start_char": start,
                "end_char": end
            })
        
        # Calculer la position de départ du prochain chunk
        start = end - chunk_overlap
        
        # Éviter les boucles infinies si l'avancement est trop petit
        if start >= end - min(chunk_overlap, min_chunk_size // 2):
            start = end
    
    # Ajouter des informations sur les sections (simulation)
    for i, chunk in enumerate(chunks):
        if i % 3 == 0:
            chunk["section"] = "Introduction"
        elif i % 3 == 1:
            chunk["section"] = "Méthodologie"
        else:
            chunk["section"] = "Application clinique"
    
    return chunks

def chunk_by_paragraph(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
    min_chunk_size: int = 200
) -> List[Dict[str, Any]]:
    """Découpe le texte par paragraphes"""
    chunks = []
    
    # Normaliser les sauts de ligne
    text = re.sub(r'\r\n', '\n', text)
    
    # Diviser en paragraphes
    paragraphs = re.split(r'\n\s*\n', text)
    
    current_chunk = ""
    current_start = 0
    start_char = 0
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        
        # Si l'ajout de ce paragraphe dépasse la taille cible
        if len(current_chunk) + len(paragraph) > chunk_size and len(current_chunk) >= min_chunk_size:
            # Ajouter le chunk actuel
            end_char = start_char + len(current_chunk)
            page_start = (current_start // 2000) + 1
            page_end = (end_char // 2000) + 1
            
            chunks.append({
                "text": current_chunk,
                "page_range": f"{page_start}-{page_end}",
                "start_char": current_start,
                "end_char": end_char
            })
            
            # Conserver une partie pour le chevauchement
            overlap_text = current_chunk[-chunk_overlap:] if chunk_overlap < len(current_chunk) else current_chunk
            current_chunk = overlap_text
            current_start = end_char - len(overlap_text)
        
        # Ajouter le paragraphe au chunk actuel
        if current_chunk:
            current_chunk += "\n\n" + paragraph
        else:
            current_chunk = paragraph
            current_start = start_char
        
        start_char += len(paragraph) + 2  # +2 pour le \n\n
    
    # Ajouter le dernier chunk s'il est assez grand
    if len(current_chunk) >= min_chunk_size:
        end_char = start_char
        page_start = (current_start // 2000) + 1
        page_end = (end_char // 2000) + 1
        
        chunks.append({
            "text": current_chunk,
            "page_range": f"{page_start}-{page_end}",
            "start_char": current_start,
            "end_char": end_char
        })
    
    # Ajouter des informations sur les sections (simulation)
    for i, chunk in enumerate(chunks):
        if i % 3 == 0:
            chunk["section"] = "Introduction"
        elif i % 3 == 1:
            chunk["section"] = "Méthodologie"
        else:
            chunk["section"] = "Application clinique"
    
    return chunks

def chunk_semantically(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
    min_chunk_size: int = 200,
    respect_boundaries: bool = True
) -> List[Dict[str, Any]]:
    """
    Découpe le texte en essayant de préserver le sens.
    
    Note: Une véritable implémentation sémantique nécessiterait un modèle NLP
    comme spaCy ou un LLM. Cette fonction est une approximation simplifiée.
    """
    chunks = []
    
    # Normaliser les sauts de ligne
    text = re.sub(r'\r\n', '\n', text)
    
    # Diviser en paragraphes puis en phrases
    paragraphs = re.split(r'\n\s*\n', text)
    
    current_chunk = ""
    current_paragraphs = []
    current_start = 0
    start_char = 0
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        
        # Tenter d'identifier les frontières sémantiques (titres, etc.)
        is_heading = False
        if respect_boundaries:
            # Heuristique simple: un paragraphe court suivi d'un saut de ligne est probablement un titre
            is_heading = len(paragraph) < 100 and not re.search(r'[.!?]$', paragraph)
        
        # Si l'ajout de ce paragraphe dépasse la taille cible ou c'est un titre
        if ((len(current_chunk) + len(paragraph) > chunk_size and len(current_chunk) >= min_chunk_size) 
            or (is_heading and current_chunk)):
            
            # Ajouter le chunk actuel
            end_char = start_char
            page_start = (current_start // 2000) + 1
            page_end = (end_char // 2000) + 1
            
            # Identifier la section à partir du contenu
            section = identify_section(current_paragraphs)
            
            # Extraire des concepts clés (simulation)
            key_concepts = extract_key_concepts(current_chunk)
            
            chunks.append({
                "text": current_chunk,
                "page_range": f"{page_start}-{page_end}",
                "start_char": current_start,
                "end_char": end_char,
                "section": section,
                "key_concepts": key_concepts
            })
            
            # Si c'est un titre, commencer un nouveau chunk avec lui
            if is_heading:
                current_chunk = paragraph
                current_paragraphs = [paragraph]
                current_start = start_char
            else:
                # Conserver une partie pour le chevauchement
                # Trouver le début d'une phrase dans les derniers caractères
                overlap_start = max(len(current_chunk) - chunk_overlap, 0)
                sentence_start = current_chunk.find('. ', overlap_start) + 2
                
                if sentence_start > overlap_start + 2:  # +2 pour le '. '
                    overlap_text = current_chunk[sentence_start:]
                else:
                    overlap_text = current_chunk[-chunk_overlap:] if chunk_overlap < len(current_chunk) else current_chunk
                
                current_chunk = overlap_text
                # Filtrer les paragraphes qui font partie du chevauchement
                current_paragraphs = [p for p in current_paragraphs if p in overlap_text]
                current_start = end_char - len(overlap_text)
        
        # Ajouter le paragraphe au chunk actuel
        if current_chunk:
            current_chunk += "\n\n" + paragraph
        else:
            current_chunk = paragraph
            current_start = start_char
            
        current_paragraphs.append(paragraph)
        start_char += len(paragraph) + 2  # +2 pour le \n\n
    
    # Ajouter le dernier chunk s'il est assez grand
    if len(current_chunk) >= min_chunk_size:
        end_char = start_char
        page_start = (current_start // 2000) + 1
        page_end = (end_char // 2000) + 1
        
        # Identifier la section à partir du contenu
        section = identify_section(current_paragraphs)
        
        # Extraire des concepts clés (simulation)
        key_concepts = extract_key_concepts(current_chunk)
        
        chunks.append({
            "text": current_chunk,
            "page_range": f"{page_start}-{page_end}",
            "start_char": current_start,
            "end_char": end_char,
            "section": section,
            "key_concepts": key_concepts
        })
    
    return chunks

def identify_section(paragraphs: List[str]) -> str:
    """
    Identifie la section à partir des paragraphes.
    C'est une approximation simplement basée sur des mots-clés.
    """
    if not paragraphs:
        return "Section non spécifiée"
    
    text = " ".join(paragraphs).lower()
    
    if any(word in text for word in ["introduction", "contexte", "préambule", "avant-propos"]):
        return "Introduction"
    elif any(word in text for word in ["méthode", "approche", "démarche", "processus"]):
        return "Méthodologie"
    elif any(word in text for word in ["résultat", "analyse", "observation", "discussion"]):
        return "Résultats et Discussion"
    elif any(word in text for word in ["application", "cas", "exemple", "pratique", "clinique"]):
        return "Application clinique"
    elif any(word in text for word in ["conclusion", "synthèse", "perspective", "recommandation"]):
        return "Conclusion"
    else:
        return "Contenu principal"

def extract_key_concepts(text: str) -> List[str]:
    """
    Extrait des concepts clés du texte.
    Dans une implémentation réelle, cela utiliserait un modèle NLP.
    Ici, c'est une simulation basée sur des mots-clés prédéfinis.
    """
    # Mots-clés liés à l'approche systémique
    keywords = {
        "communication circulaire": ["communication", "circulaire", "circularité"],
        "feedback": ["feedback", "rétroaction", "boucle"],
        "MRI": ["MRI", "mental research institute", "palo alto"],
        "homéostasie": ["homéostasie", "équilibre", "stabilité"],
        "double contrainte": ["double contrainte", "double bind", "paradoxe"],
        "recadrage": ["recadrage", "reframing", "nouvelle perspective"],
        "prescription du symptôme": ["prescription", "symptôme", "paradoxale"],
    }
    
    # Rechercher les mots-clés dans le texte
    found_concepts = []
    text_lower = text.lower()
    
    for concept, terms in keywords.items():
        if any(term in text_lower for term in terms):
            found_concepts.append(concept)
    
    # S'assurer qu'il y a au moins quelques concepts
    if not found_concepts:
        found_concepts = ["communication circulaire", "feedback", "MRI"]
    
    return found_concepts[:3]  # Limiter à 3 concepts