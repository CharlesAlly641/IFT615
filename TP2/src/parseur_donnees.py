"""
Lit les fichiers de texte (r_ops, r_fact) et construit les
structures de données dont Graphplan a besoin :
  - Operateur : LOAD, UNLOAD, MOVE
  - Proposition (ou littéral):  prédicat avec argument (instanciée ou avec variables)
        ex ("at", "r1", "London")
  - objets_par_type : {"PLACE": ["London", "Paris", ...], ...}
  - etat_initial : L'état de départ (immuable)
  - buts : Les objectifs à atteindre (immuable)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from traitement_fichier import parser_texte, Element

# Le premier élément est le nom du prédicat, les suivants sont ses arguments.
# Longueur variable (Généralement 2 ou 3)
Proposition = Tuple[str, ...]

@dataclass
class Operateur:
    """Un opérateur générique (LOAD, UNLOAD, MOVE), avant instanciation.
        Représente l'opérateur sous forme de triplet PAD du formalisme STRIPS."""

    nom: str
    params: List[Tuple[str, str]]      # [("<object>", "CARGO"), ("<rocket>", "ROCKET"), ...]
    preconds: List[Proposition]            # Ensemble de pré conditions
    postconds: List[Proposition]           # Liste post conditions
    delete_effects: List[Proposition]      # Liste DELETE effects


@dataclass
class ProblemePlanification:
    """Regroupe tout ce qui constitue un problème de planification
    (Les opérateurs, les objets, les conditions de départ
    et les objectifs)"""

    operateurs: Dict[str, Operateur]
    objets_par_type: Dict[str, List[str]]
    etat_initial: frozenset[Proposition]
    buts: frozenset[Proposition]


def lire_fichier(chemin: str) -> str:
    """Lit un fichier texte"""
    with open(chemin, "rb") as f:
        contenu_brut = f.read()
    # Évite de faire planter le programme si mauvais encodage (ex : accents)
    return contenu_brut.decode("latin-1", errors="replace")


def proposition_depuis_element(element: Element) -> Proposition:
    """Convertit un élément ['at', '<rocket>', '<place>']
    en tuple ("at", "<rocket>", "<place>")."""
    assert isinstance(element, list), f"littéral attendu, reçu : {element}"
    return tuple(element)


def parse_operateurs(chemin: str) -> Dict[str, Operateur]:
    """Lit le fichier des opérateurs (r_ops) et construit un
    dictionnaire {nom_operateur: Operateur}."""
    texte = lire_fichier(chemin)
    blocs_texte = parser_texte(texte)

    operateurs: Dict[str, Operateur] = {}
    for bloc in blocs_texte:
        # expression = ['operator', 'LOAD', ['params', ...], ['preconds', ...], ['effects', ...]]
        if not isinstance(bloc, list) or not bloc or bloc[0] != "operator":
            continue

        nom = bloc[1]
        bloc_parametres = trouver_bloc(bloc, "params")
        bloc_preconditions = trouver_bloc(bloc, "preconds")
        bloc_effets = trouver_bloc(bloc, "effects")

        parametres = [(p[0], p[1]) for p in bloc_parametres]
        preconditions = [proposition_depuis_element(p) for p in bloc_preconditions]

        postconds, delete_effects = [], []
        for effet in bloc_effets:
            if effet[0] == "del":
                delete_effects.append(tuple(effet[1:]))
            else:
                postconds.append(proposition_depuis_element(effet))

        operateurs[nom] = Operateur(nom, parametres, preconditions, postconds, delete_effects,)

    return operateurs


def parse_faits(chemin: str) -> Tuple[Dict[str, List[str]], frozenset, frozenset]:
    """Lit un fichier r_fact et retourne (objets_par_type, etat_initial, buts)."""
    texte = lire_fichier(chemin)
    blocs_texte = parser_texte(texte)

    objets_par_type: Dict[str, List[str]] = {}
    etat_initial, buts = [], []

    for bloc in blocs_texte:
        if not isinstance(bloc, list) or not bloc:
            continue

        entete = bloc[0]
        if entete == "preconds":
            etat_initial = [proposition_depuis_element(lit) for lit in bloc[1:]]
        elif entete == "effects":
            buts = [proposition_depuis_element(lit) for lit in bloc[1:]]
        elif len(bloc) == 2 and bloc[1].isupper():
            # ex: ['London', 'PLACE'] -> déclaration d'un objet typé
            nom_objet, type_objet = bloc
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
    """Lit les deux fichiers (r_ops et r_fact) et construit le
    ProblemePlanification complet."""
    operateurs = parse_operateurs(chemin_ops)
    objets_par_type, etat_initial, buts = parse_faits(chemin_faits)
    return ProblemePlanification(operateurs, objets_par_type, etat_initial, buts)

# Test local du fichier
if __name__ == "__main__":
    import glob
    ops = glob.glob("../*/r_ops.txt")[0]
    facts = glob.glob("../*/r_fact2.txt")[0]

    probleme = charger_probleme(ops, facts)

    print("=== Opérateurs ===")
    for nom, op in probleme.operateurs.items():
        print(f"{nom}: params={op.params}")
        print(f"   preconds={op.preconds}")
        print(f"   add={op.postconds}  del={op.delete_effects}")

    print("\n=== Objets ===")
    print(probleme.objets_par_type)

    print("\n=== État initial ===")
    print(probleme.etat_initial)

    print("\n=== Buts ===")
    print(probleme.buts)