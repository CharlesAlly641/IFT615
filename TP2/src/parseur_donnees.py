"""
Lit les fichiers de texte (r_ops, r_fact) et construit les
structures de données dont Graphplan a besoin :
  - Operateur : LOAD, UNLOAD, MOVE
  - Litteral : un littéral représenté par un prédicat + arguments, ex ("at", "r1", "London")
  - objets_par_type : {"PLACE": ["London", "Paris", ...], ...}
  - etat_initial : L'état de départ (reste fixe tout au long du problème)
  - buts : Les objectifs à atteindre (reste fixe tout au long du problème)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from traitement_fichier import parser_texte, Element

# Litéral concret (avec instanciation) ou avec des variables
Litteral = Tuple[str, ...]  # ex: ("at", "r1", "London")  ou variable: ("at","<rocket>","<place>")


@dataclass
class Operateur:
    """Un opérateur générique (LOAD, UNLOAD, MOVE), avant instanciation.
        Représente l'opérateur sous forme de triplet PAD du formalisme STRIPS."""

    nom: str
    params: List[Tuple[str, str]]      # [("<object>", "CARGO"), ("<rocket>", "ROCKET"), ...]
    preconds: List[Litteral]            # Ensemble de pré conditions
    postconds: List[Litteral]           # Liste post conditions
    delete_effects: List[Litteral]      # Liste DELETE effects

    @property
    def nom_var(self) -> List[str]:
        """ Retourne le nom des variables uniquement """
        return [v for v, _ in self.params]


@dataclass
class ProblemePlanification:
    """Regroupe tout ce qui constitue un problème de planification
    (Les opérateurs, les objets, les conditions de départ
    et les objectifs)"""

    operateurs: Dict[str, Operateur]
    objets_par_type: Dict[str, List[str]]
    etat_initial: frozenset
    buts: frozenset


def lire_fichier(chemin: str) -> str:
    # Les fichiers fournis sont en général en Windows-1252 / latin-1
    # (accents mal encodés dans les commentaires). errors="replace" pour
    # ne jamais planter dessus -- de toute façon on jette les commentaires.
    with open(chemin, "rb") as f:
        contenu_brut = f.read()
    return contenu_brut.decode("latin-1", errors="replace")


def litteral_depuis_element(element: Element) -> Litteral:
    """Convertit un élément comme ['at', '<rocket>', '<place>']
    en tuple ("at", "<rocket>", "<place>")."""
    assert isinstance(element, list), f"littéral attendu, reçu : {element}"
    return tuple(element)


def parse_operateurs(chemin: str) -> Dict[str, Operateur]:
    """Lit le fichier des opérateurs (r_ops) et construit un
    dictionnaire {nom_operateur: Operateur}."""
    texte = lire_fichier(chemin)
    expressions = parser_texte(texte)

    operateurs: Dict[str, Operateur] = {}
    for expression in expressions:
        # expression = ['operator', 'LOAD', ['params', ...], ['preconds', ...], ['effects', ...]]
        if not isinstance(expression, list) or not expression or expression[0] != "operator":
            continue

        nom = expression[1]
        bloc_parametres = trouver_bloc(expression, "params")
        bloc_preconditions = trouver_bloc(expression, "preconds")
        bloc_effets = trouver_bloc(expression, "effects")

        parametres = [(p[0], p[1]) for p in bloc_parametres]
        preconditions = [litteral_depuis_element(p) for p in bloc_preconditions]

        postconds, delete_effects = [], []
        for effet in bloc_effets:
            if effet[0] == "del":
                delete_effects.append(tuple(effet[1:]))
            else:
                postconds.append(litteral_depuis_element(effet))

        operateurs[nom] = Operateur(nom, parametres, preconditions, postconds, delete_effects,)

    return operateurs


def parse_faits(chemin: str) -> Tuple[Dict[str, List[str]], frozenset, frozenset]:
    """Lit un fichier de faits r_fact et retourne :
    (objets_par_type, etat_initial, buts)."""
    texte = lire_fichier(chemin)
    expressions_racine = parser_texte(texte)

    objets_par_type: Dict[str, List[str]] = {}
    etat_initial, buts = [], []

    for expression in expressions_racine:
        if not isinstance(expression, list) or not expression:
            continue

        entete = expression[0]
        if entete == "preconds":
            etat_initial = [litteral_depuis_element(lit) for lit in expression[1:]]
        elif entete == "effects":
            buts = [litteral_depuis_element(lit) for lit in expression[1:]]
        elif len(expression) == 2 and expression[1].isupper():
            # ex: ['London', 'PLACE'] -> déclaration d'un objet typé
            nom_objet, type_objet = expression
            objets_par_type.setdefault(type_objet, []).append(nom_objet)

    return objets_par_type, frozenset(etat_initial), frozenset(buts)


def trouver_bloc(expression: List[Element], mot_cle: str) -> List[Element]:
    """Cherche le sous-bloc ['mot_cle', ...] dans expression et retourne
    son contenu (sans le mot-clé lui-même)."""
    for element in expression:
        if isinstance(element, list) and element and element[0] == mot_cle:
            return element[1:]
    return []


def charger_probleme(chemin_ops: str, chemin_faits: str) -> ProblemePlanification:
    """Point d'entrée du module : lit les deux fichiers et construit le
    ProblemePlanification complet, prêt à être utilisé par Graphplan."""
    operateurs = parse_operateurs(chemin_ops)
    objets_par_type, etat_initial, buts = parse_faits(chemin_faits)
    return ProblemePlanification(operateurs, objets_par_type, etat_initial, buts)

# Test local du fichier
if __name__ == "__main__":
    import glob
    ops_file = glob.glob("../*/r_ops.txt")[0]
    facts_file = glob.glob("../*/r_fact2.txt")[0]

    probleme = charger_probleme(ops_file, facts_file)

    print("=== Opérateurs ===")
    for name, op in probleme.operateurs.items():
        print(f"{name}: params={op.params}")
        print(f"   preconds={op.preconds}")
        print(f"   add={op.postconds}  del={op.delete_effects}")

    print("\n=== Objets ===")
    print(probleme.objets_par_type)

    print("\n=== État initial ===")
    print(probleme.etat_initial)

    print("\n=== Buts ===")
    print(probleme.buts)