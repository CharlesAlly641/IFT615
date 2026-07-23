"""
Ce fichier permet d'analyser et de lire les fichiers de texte.
Dans le contexte de la planification, il est utilisé pour les fichiers de texte suivants :
 - r_ops : fichier texte contenant la liste des opérateurs permis (actions).
 - r_facts : fichier texte comprenant la liste des conditions initiales et les objectifs fixés.

Chaque bloc de texte entre parenthèses dans les fichiers textes devient une liste Python.

Résultat attendu à la sortie du fichier :
  Entrée : "(at r1 London)"
  Sortie : ['at', 'r1', 'London']
"""

from typing import List, Union

# Un élément peut être un mot ou une liste contenant d'autres éléments.
Element = Union[str, List["Element"]]

def tokenizer(text: str) -> List[str]:
    """Découpe le texte du fichier en une liste de "tokens"."""

    # Normaliser les fins de ligne
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Retirer les commentaires
    text = retirer_commentaires(text)

    # Ajout d'espace à côté des parenthèses pour pouvoir split()
    text = text.replace("(", " ( ").replace(")", " ) ")

    return text.split()


def retirer_commentaires(text: str) -> str:
    """Supprime tous les commentaires /* ... */ dans le texte."""
    sortie = []
    i = 0
    n = len(text)
    while i < n:
        if text[i:i + 2] == "/*":
            # On cherche la fin du commentaire
            fin = text.find("*/", i + 2)
            if fin == -1:
                break  # commentaire non fermé
            i = fin + 2
        else:
            # Aucun commentaire
            sortie.append(text[i])
            i += 1
    return "".join(sortie)


def parser_texte(text: str) -> List[Element]:
    """Analyse un texte complet contenant une ou plusieurs sections entre parenthèses."""
    tokens = tokenizer(text)
    elements = []
    pos = 0
    while pos < len(tokens):
        element, pos = parser_token(tokens, pos)
        elements.append(element)
    return elements


def parser_token(tokens: List[str], pos: int):
    """Analyse un seul bloc (mot ou sous-liste) à partir de la position donnée."""
    if tokens[pos] != "(":
        return tokens[pos], pos + 1

    pos += 1  # on dépasse la '('
    items: List[Element] = []
    while tokens[pos] != ")":
        if tokens[pos] == "(":
            # On fait un appel récursif si on a un autre bloc dans le bloc précédent
            sub, pos = parser_token(tokens, pos)
            items.append(sub)
        else:
            items.append(tokens[pos])
            pos += 1
    pos += 1  # on dépasse la ')'
    return items, pos


# Test local du fichier
if __name__ == "__main__":
    test = "(operator LOAD (params (<object> CARGO)) (preconds (at <rocket> <place>)))"
    import pprint
    pprint.pprint(parser_texte(test))