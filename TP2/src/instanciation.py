"""
Prend les opérateurs génériques (avec variables comme <rocket>, <place>)
produits par analyseur_domaine.py, et génère toutes les actions concrètes
possibles en substituant les variables par les objets du bon type.

Ex: l'opérateur LOAD(<object> CARGO, <rocket> ROCKET, <place> PLACE)
    + objets {CARGO: [alex], ROCKET: [r1], PLACE: [London]}
    -> l'action concrète LOAD_alex_r1_London

Chaque action concrète (GroundedAction) porte ses préconditions et effets
déjà substitués, sous forme de littéraux sans variable -- prêts à être
utilisés directement par graphe_planification.py.
"""

import itertools
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any

from parseur_donnees import Operateur, Proposition, ProblemePlanification


@dataclass(frozen=True)
class ActionInstanciee:
    nom: str                      # ex: "LOAD_alex_r1_London"
    operateur: str                # ex: "LOAD"
    args: Tuple[str, ...]         # ex: ("alex", "r1", "London")
    preconds: frozenset
    postconds: frozenset
    delete_effects: frozenset

    def __repr__(self):
        return self.nom


def substituer(litteral: Proposition, mapping: Dict[str, str]) -> tuple[str | None | Any, ...]:
    """Remplace chaque variable d'un littéral par sa valeur concrète.

    Le premier élément d'un littéral est le nom du prédicat (ex: "at"),
    il n'est jamais substitué -- seuls les arguments le sont.
    """
    predicat, *args = litteral
    return (predicat,) + tuple(mapping.get(a, a) for a in args)


def instancier_operateur(op: Operateur, objets_par_type: Dict[str, List[str]]) -> List[ActionInstanciee]:
    """Génère toutes les instances concrètes d'un opérateur donné."""
    noms_var = [v for v, _ in op.params]
    types_var = [t for _, t in op.params]

    # Pour chaque variable, la liste des objets compatibles avec son type
    try:
        domaines = [objets_par_type[t] for t in types_var]
    except KeyError as e:
        raise ValueError(
            f"Type d'objet {e} utilisé par l'opérateur {op.nom} "
            f"mais absent des objets déclarés dans le fichier de faits."
        )

    actions_instancie = []
    for combinaison in itertools.product(*domaines):
        correspondances = dict(zip(noms_var, combinaison))

        preconds = frozenset(substituer(lit, correspondances) for lit in op.preconds)
        postconds = frozenset(substituer(lit, correspondances) for lit in op.postconds)
        delete_effects = frozenset(substituer(lit, correspondances) for lit in op.delete_effects)

        nom = "_".join([op.nom] + list(combinaison))

        actions_instancie.append(ActionInstanciee(nom,op.nom,combinaison,preconds,postconds,delete_effects,))

    return actions_instancie


def instancier_tous_operateurs(probleme: ProblemePlanification) -> List[ActionInstanciee]:
    """Génère toutes les actions concrètes pour tous les opérateurs du problème."""
    actions = []
    for op in probleme.operateurs.values():
        actions.extend(instancier_operateur(op, probleme.objets_par_type))
    return actions

# Test local du fichier
if __name__ == "__main__":
    import glob
    from parseur_donnees import charger_probleme

    ops_file = glob.glob("../*/r_ops.txt")[0]
    facts_file = glob.glob("../*/r_fact2.txt")[0]

    problem = charger_probleme(ops_file, facts_file)
    actions = instancier_tous_operateurs(problem)

    print(f"Nombre total d'actions instanciées : {len(actions)}\n")
    for a in actions:
        print(a.nom)
        print(f"   preconds: {sorted(a.preconds)}")
        print(f"   add:      {sorted(a.postconds)}")
        print(f"   del:      {sorted(a.delete_effects)}")