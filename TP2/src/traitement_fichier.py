"""
analyseur_parentheses.py
-------------------------
Parseur générique de S-expressions (syntaxe façon Lisp) utilisé pour lire
r_ops.txt et r_factX.txt du rocket domain (IFT615 - Devoir 2).

Une S-expression est soit :
  - un atome (chaîne sans espace ni parenthèse), ex: "LOAD", "<rocket>", "ROCKET"
  - une liste de S-expressions entre parenthèses, ex: (at <rocket> <place>)

On la représente en Python par :
  - un atome -> str
  - une liste -> list (récursif)
"""

from typing import List, Union

SExpr = Union[str, List["SExpr"]]


def tokenize(text: str) -> List[str]:
    """Découpe le texte en tokens : '(', ')' et atomes.

    Gère les \\r\\n, les commentaires /* ... */ et les lignes vides
    qu'on retrouve dans les fichiers fournis.
    """
    # Normaliser les fins de ligne
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Retirer les commentaires de style /* ... */ (utilisés dans simulation_factX.txt)
    text = _strip_block_comments(text)

    # Coller des espaces autour des parenthèses pour pouvoir les split()
    text = text.replace("(", " ( ").replace(")", " ) ")

    return text.split()


def _strip_block_comments(text: str) -> str:
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text[i:i + 2] == "/*":
            end = text.find("*/", i + 2)
            if end == -1:
                break  # commentaire non fermé -> on ignore le reste
            i = end + 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def parse_all(text: str) -> List[SExpr]:
    """Parse un texte contenant plusieurs S-expressions au niveau racine.

    Retourne la liste des S-expressions de premier niveau, dans l'ordre.
    Ex: "(a b) (c d)" -> [['a', 'b'], ['c', 'd']]
    """
    tokens = tokenize(text)
    exprs = []
    pos = 0
    while pos < len(tokens):
        expr, pos = _parse_one(tokens, pos)
        exprs.append(expr)
    return exprs


def _parse_one(tokens: List[str], pos: int):
    """Parse une seule S-expression à partir de tokens[pos]. Retourne (expr, nouvelle_pos)."""
    if tokens[pos] != "(":
        # atome isolé (rare ici, mais géré par robustesse)
        return tokens[pos], pos + 1

    pos += 1  # on consomme '('
    items: List[SExpr] = []
    while tokens[pos] != ")":
        if tokens[pos] == "(":
            sub, pos = _parse_one(tokens, pos)
            items.append(sub)
        else:
            items.append(tokens[pos])
            pos += 1
    pos += 1  # on consomme ')'
    return items, pos


if __name__ == "__main__":
    # petit test manuel
    sample = "(operator LOAD (params (<object> CARGO)) (preconds (at <rocket> <place>)))"
    import pprint
    pprint.pprint(parse_all(sample))