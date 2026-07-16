"""
instanciation.py
-----------------
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
from typing import Dict, List, Tuple

from parseur_donnees import Operator, Literal, PlanningProblem


@dataclass(frozen=True)
class GroundedAction:
    name: str                      # ex: "LOAD_alex_r1_London"
    operator_name: str             # ex: "LOAD"
    args: Tuple[str, ...]          # ex: ("alex", "r1", "London")
    preconds: frozenset            # littéraux concrets requis
    add_effects: frozenset         # littéraux concrets ajoutés
    del_effects: frozenset         # littéraux concrets supprimés

    def __repr__(self):
        return self.name


def _substitute(literal: Literal, mapping: Dict[str, str]) -> Literal:
    """Remplace chaque variable d'un littéral par sa valeur concrète.

    Le premier élément d'un littéral est le nom du prédicat (ex: "at"),
    il n'est jamais substitué -- seuls les arguments le sont.
    """
    predicate, *args = literal
    return (predicate,) + tuple(mapping.get(a, a) for a in args)


def ground_operator(op: Operator, objects_by_type: Dict[str, List[str]]) -> List[GroundedAction]:
    """Génère toutes les instances concrètes d'un opérateur donné."""
    var_names = [v for v, _ in op.params]
    var_types = [t for _, t in op.params]

    # Pour chaque variable, la liste des objets compatibles avec son type
    try:
        domains = [objects_by_type[t] for t in var_types]
    except KeyError as e:
        raise ValueError(
            f"Type d'objet {e} utilisé par l'opérateur {op.name} "
            f"mais absent des objets déclarés dans le fichier de faits."
        )

    grounded_actions = []
    for combo in itertools.product(*domains):
        mapping = dict(zip(var_names, combo))

        preconds = frozenset(_substitute(lit, mapping) for lit in op.preconds)
        add_effects = frozenset(_substitute(lit, mapping) for lit in op.add_effects)
        del_effects = frozenset(_substitute(lit, mapping) for lit in op.del_effects)

        name = "_".join([op.name] + list(combo))

        grounded_actions.append(GroundedAction(
            name=name,
            operator_name=op.name,
            args=combo,
            preconds=preconds,
            add_effects=add_effects,
            del_effects=del_effects,
        ))

    return grounded_actions


def ground_all_operators(problem: PlanningProblem) -> List[GroundedAction]:
    """Génère toutes les actions concrètes pour tous les opérateurs du problème."""
    all_actions = []
    for op in problem.operators.values():
        all_actions.extend(ground_operator(op, problem.objects_by_type))
    return all_actions


if __name__ == "__main__":
    import glob
    from parseur_donnees import load_problem

    ops_file = glob.glob("../*/r_ops.txt")[0]
    facts_file = glob.glob("../*/r_fact2.txt")[0]

    problem = load_problem(ops_file, facts_file)
    actions = ground_all_operators(problem)

    print(f"Nombre total d'actions instanciées : {len(actions)}\n")
    for a in actions:
        print(a.name)
        print(f"   preconds: {sorted(a.preconds)}")
        print(f"   add:      {sorted(a.add_effects)}")
        print(f"   del:      {sorted(a.del_effects)}")