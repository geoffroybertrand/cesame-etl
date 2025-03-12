import re
from typing import List, Dict, Any, Optional, Tuple

def clean_document(text: str, cleaning_options: Dict[str, bool] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Nettoie le texte d'un document en supprimant les éléments indésirables.
    
    Args:
        text: Le texte à nettoyer
        cleaning_options: Options de nettoyage spécifiques
            - remove_headers: Supprime les en-têtes de page
            - remove_footers: Supprime les pieds de page
            - remove_page_numbers: Supprime les numéros de page
            - remove_extra_whitespace: Supprime les espaces vides excédentaires
            - normalize_quotes: Normalise les guillemets
            - fix_hyphenation: Corrige la coupure des mots par trait d'union
    
    Returns:
        Tuple contenant le texte nettoyé et des informations sur les modifications effectuées
    """
    if cleaning_options is None:
        cleaning_options = {
            "remove_headers": True,
            "remove_footers": True,
            "remove_page_numbers": True,
            "remove_extra_whitespace": True,
            "normalize_quotes": True,
            "fix_hyphenation": True
        }
    
    original_length = len(text)
    stats = {
        "original_length": original_length,
        "removed_elements": []
    }
    
    # Diviser le texte en pages (basées sur les séparateurs de page courants)
    pages = re.split(r'\f|\n\s*\n\s*\d+\s*\n|\n\s*-\s*\d+\s*-\s*\n', text)
    
    # Si le document n'a pas de séparateurs de page évidents, essayer une autre méthode
    if len(pages) <= 1:
        pages = re.split(r'\n\s*\n\s*\n\s*\n', text)
    
    # Nettoyer chaque page
    cleaned_pages = []
    
    for page in pages:
        lines = page.split('\n')
        page_lines = len(lines)
        
        # Sauter les pages vides ou trop courtes
        if page_lines < 3:
            continue
            
        # Identifier les lignes potentielles d'en-tête et de pied de page
        header_lines = min(2, page_lines // 10)
        footer_lines = min(3, page_lines // 10)
        
        # Nettoyer les en-têtes
        if cleaning_options.get("remove_headers", True) and page_lines > header_lines:
            potential_header = '\n'.join(lines[:header_lines])
            # Vérifier si c'est un en-tête avec des motifs communs
            if (re.search(r'(page|chapitre|\d+/\d+|confidential|draft)', potential_header, re.IGNORECASE) or 
                all(len(line) < 60 for line in lines[:header_lines])):
                lines = lines[header_lines:]
                stats["removed_elements"].append("headers")
        
        # Nettoyer les pieds de page
        if cleaning_options.get("remove_footers", True) and page_lines > footer_lines:
            potential_footer = '\n'.join(lines[-footer_lines:])
            # Vérifier si c'est un pied de page avec des motifs communs
            if (re.search(r'(page|©|copyright|tous droits|www|http|@|\d+$|\d+/\d+)', potential_footer, re.IGNORECASE) or
                all(len(line) < 60 for line in lines[-footer_lines:])):
                lines = lines[:-footer_lines]
                stats["removed_elements"].append("footers")
        
        # Nettoyer les numéros de page
        if cleaning_options.get("remove_page_numbers", True):
            # Supprimer les lignes contenant uniquement un numéro de page
            lines = [line for line in lines if not re.match(r'^\s*\d+\s*$', line)]
            
            # Supprimer les numéros de page à la fin des lignes
            lines = [re.sub(r'\s+\d+\s*$', '', line) for line in lines]
            stats["removed_elements"].append("page_numbers")
        
        # Corriger les mots coupés par un trait d'union
        if cleaning_options.get("fix_hyphenation", True):
            for i in range(len(lines) - 1):
                if re.search(r'-$', lines[i]) and lines[i + 1] and lines[i + 1][0].islower():
                    word_part1 = re.sub(r'-$', '', lines[i])
                    word_part2 = lines[i + 1]
                    lines[i] = word_part1
                    lines[i + 1] = word_part2
            stats["removed_elements"].append("hyphenation")
        
        # Normaliser les guillemets
        if cleaning_options.get("normalize_quotes", True):
            for i in range(len(lines)):
                lines[i] = re.sub(r'[""„‟]', '"', lines[i])
                lines[i] = re.sub(r'[''‛]', "'", lines[i])
            stats["removed_elements"].append("non_standard_quotes")
        
        cleaned_pages.append('\n'.join(lines))
    
    # Rejoindre les pages nettoyées
    cleaned_text = '\n\n'.join(cleaned_pages)
    
    # Supprimer les espaces vides excédentaires
    if cleaning_options.get("remove_extra_whitespace", True):
        # Remplacer les multiples lignes vides par une seule
        cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
        # Remplacer les multiples espaces par un seul
        cleaned_text = re.sub(r' +', ' ', cleaned_text)
        # Supprimer les espaces en début et fin de ligne
        cleaned_text = re.sub(r'^ +| +$', '', cleaned_text, flags=re.MULTILINE)
        stats["removed_elements"].append("extra_whitespace")
    
    # Calculer les statistiques de nettoyage
    cleaned_length = len(cleaned_text)
    stats["cleaned_length"] = cleaned_length
    stats["reduction_percentage"] = round(((original_length - cleaned_length) / original_length) * 100, 2)
    stats["removed_elements"] = list(set(stats["removed_elements"]))  # Dédupliquer
    
    return cleaned_text, stats


def identify_document_structure(text: str) -> Dict[str, Any]:
    """
    Identifie la structure du document (chapitres, sections, etc.).
    
    Args:
        text: Le texte du document
        
    Returns:
        Un dictionnaire contenant les informations sur la structure du document
    """
    structure = {
        "has_toc": False,
        "chapters": [],
        "sections": [],
        "subsections": [],
        "figures": [],
        "tables": []
    }
    
    lines = text.split('\n')
    
    # Patterns pour les titres de chapitres et sections
    chapter_patterns = [
        r'^chapitre\s+\d+',
        r'^\d+\.\s+[A-Z]',
        r'^[IVX]+\.\s+[A-Z]'
    ]
    
    section_patterns = [
        r'^\d+\.\d+\.\s+[A-Z]',
        r'^[A-Z][^.!?]*$'
    ]
    
    subsection_patterns = [
        r'^\d+\.\d+\.\d+\.\s+',
        r'^•\s+[A-Z]'
    ]
    
    # Détecter la table des matières
    toc_patterns = [
        r'^table\s+des\s+matières',
        r'^sommaire',
        r'^table\s+of\s+contents'
    ]
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Ignorer les lignes vides
        if not line:
            continue
        
        # Détecter la table des matières
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in toc_patterns):
            structure["has_toc"] = True
            continue
        
        # Détecter les chapitres
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in chapter_patterns):
            structure["chapters"].append({
                "title": line,
                "position": i
            })
            continue
        
        # Détecter les sections
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in section_patterns):
            structure["sections"].append({
                "title": line,
                "position": i
            })
            continue
        
        # Détecter les sous-sections
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in subsection_patterns):
            structure["subsections"].append({
                "title": line,
                "position": i
            })
            continue
        
        # Détecter les figures
        if re.search(r'^(figure|fig\.)\s+\d+', line, re.IGNORECASE):
            structure["figures"].append({
                "title": line,
                "position": i
            })
            continue
        
        # Détecter les tableaux
        if re.search(r'^(tableau|table)\s+\d+', line, re.IGNORECASE):
            structure["tables"].append({
                "title": line,
                "position": i
            })
    
    # Nettoyer les structures vides
    structure = {k: v for k, v in structure.items() if v or k == "has_toc"}
    
    return structure