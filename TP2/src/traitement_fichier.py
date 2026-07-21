"""
Ce fichier permet d'analyser et de lire la structure des fichiers de texte
tels que ceux fournis en exemple (r_fact, r_ops)

Ce code transforme la structure du texte en listes Python
Un bloc entre parenthèses `(...)` devient une liste Python (`list`).

Exemple de conversion :
  Texte source : "(at r1 London)"
  Résultat     : ['at', 'r1', 'London']
"""

from typing import List, Union

# Un élément est un mot ou une liste contenant d'autres éléments.
Element = Union[str, List["Element"]]

def tokenize(text: str) -> List[str]:
    """Découpe le texte du fichier en une liste de tokens."""

    # Normaliser les fins de ligne
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Retirer les commentaires
    text = retirer_commentaires(text)

    # Ajout d'espace à côté des parenthèses pour pouvoir split()
    text = text.replace("(", " ( ").replace(")", " ) ")

    return text.split()


def retirer_commentaires(text: str) -> str:
    """Supprime tous les commentaires /* ... */ dans le texte."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text[i:i + 2] == "/*":
            # On cherche la fin du commentaire
            end = text.find("*/", i + 2)
            if end == -1:
                break  # commentaire non fermé
            i = end + 2
        else:
            # Aucun commentaire
            out.append(text[i])
            i += 1
    return "".join(out)


def parse_all(text: str) -> List[Element]:
    """Analyse un texte complet contenant une ou plusieurs expressions entre parenthèses."""
    tokens = tokenize(text)
    elements = []
    pos = 0
    while pos < len(tokens):
        element, pos = parse_one(tokens, pos)
        elements.append(element)
    return elements


def parse_one(tokens: List[str], pos: int):
    """Analyse un seul bloc (mot ou sous-liste) à partir de la position donnée."""
    if tokens[pos] != "(":
        return tokens[pos], pos + 1

    pos += 1  # on consomme '('
    items: List[Element] = []
    while tokens[pos] != ")":
        if tokens[pos] == "(":
            sub, pos = parse_one(tokens, pos)
            items.append(sub)
        else:
            items.append(tokens[pos])
            pos += 1
    pos += 1  # on consomme ')'
    return items, pos


# Test local du fichier
if __name__ == "__main__":
    sample = "(operator LOAD (params (<object> CARGO)) (preconds (at <rocket> <place>)))"
    import pprint
    pprint.pprint(parse_all(sample))