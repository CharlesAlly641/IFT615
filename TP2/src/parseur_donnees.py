"""
domain_parser.py
-----------------
Lit r_ops.txt et r_factX.txt (via sexpr.py) et construit les structures
de données dont Graphplan aura besoin :

  - Operator : un opérateur générique (LOAD, UNLOAD, MOVE) avec variables
  - Literal  : un littéral prédicat + arguments, ex ("at", "r1", "London")
  - objects_by_type : {"PLACE": ["London", "Paris", ...], ...}
  - initial_state : frozenset de Literal (l'état de départ)
  - goals : frozenset de Literal (les objectifs à atteindre)

On garde les littéraux comme tuples de chaînes -> hashables, faciles à
mettre dans des set() (utile pour tout le reste de Graphplan : niveaux
de propositions, mutex, etc.)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from traitement_fichier import parse_all, SExpr

Literal = Tuple[str, ...]  # ex: ("at", "r1", "London")  ou variable: ("at","<rocket>","<place>")


@dataclass
class Operator:
    name: str
    params: List[Tuple[str, str]]      # [("<object>", "CARGO"), ("<rocket>", "ROCKET"), ...]
    preconds: List[Literal]            # littéraux (avec variables) requis
    add_effects: List[Literal]         # littéraux ajoutés
    del_effects: List[Literal]         # littéraux supprimés

    @property
    def var_names(self) -> List[str]:
        return [v for v, _ in self.params]


@dataclass
class PlanningProblem:
    operators: Dict[str, Operator]
    objects_by_type: Dict[str, List[str]]
    initial_state: frozenset
    goals: frozenset


def _read_file(path: str) -> str:
    # Les fichiers fournis sont en général en Windows-1252 / latin-1
    # (accents mal encodés dans les commentaires). errors="replace" pour
    # ne jamais planter dessus -- de toute façon on jette les commentaires.
    with open(path, "rb") as f:
        raw = f.read()
    return raw.decode("latin-1", errors="replace")


def _literal_from_sexpr(sexpr: SExpr) -> Literal:
    """Une S-expression comme ['at', '<rocket>', '<place>'] -> tuple."""
    assert isinstance(sexpr, list), f"littéral attendu, reçu: {sexpr}"
    return tuple(sexpr)


def parse_operators(path: str) -> Dict[str, Operator]:
    text = _read_file(path)
    top_level = parse_all(text)

    operators: Dict[str, Operator] = {}
    for expr in top_level:
        # expr = ['operator', 'LOAD', ['params', ...], ['preconds', ...], ['effects', ...]]
        if not isinstance(expr, list) or not expr or expr[0] != "operator":
            continue

        name = expr[1]
        params_block = _find_block(expr, "params")
        preconds_block = _find_block(expr, "preconds")
        effects_block = _find_block(expr, "effects")

        params = [(p[0], p[1]) for p in params_block]
        preconds = [_literal_from_sexpr(p) for p in preconds_block]

        add_effects, del_effects = [], []
        for eff in effects_block:
            if eff[0] == "del":
                del_effects.append(tuple(eff[1:]))
            else:
                add_effects.append(_literal_from_sexpr(eff))

        operators[name] = Operator(
            name=name,
            params=params,
            preconds=preconds,
            add_effects=add_effects,
            del_effects=del_effects,
        )

    return operators


def parse_facts(path: str) -> Tuple[Dict[str, List[str]], frozenset, frozenset]:
    text = _read_file(path)
    top_level = parse_all(text)

    objects_by_type: Dict[str, List[str]] = {}
    initial_state, goals = [], []

    for expr in top_level:
        if not isinstance(expr, list) or not expr:
            continue

        head = expr[0]
        if head == "preconds":
            initial_state = [_literal_from_sexpr(lit) for lit in expr[1:]]
        elif head == "effects":
            goals = [_literal_from_sexpr(lit) for lit in expr[1:]]
        elif len(expr) == 2 and expr[1].isupper():
            # ex: ['London', 'PLACE'] -> déclaration d'objet typé
            obj_name, obj_type = expr
            objects_by_type.setdefault(obj_type, []).append(obj_name)

    return objects_by_type, frozenset(initial_state), frozenset(goals)


def _find_block(expr: List[SExpr], keyword: str) -> List[SExpr]:
    """Cherche le sous-bloc ['keyword', ...] dans expr et retourne son contenu."""
    for item in expr:
        if isinstance(item, list) and item and item[0] == keyword:
            return item[1:]
    return []


def load_problem(ops_path: str, facts_path: str) -> PlanningProblem:
    operators = parse_operators(ops_path)
    objects_by_type, initial_state, goals = parse_facts(facts_path)
    return PlanningProblem(operators, objects_by_type, initial_state, goals)


if __name__ == "__main__":
    import glob
    ops_file = glob.glob("../*/r_ops.txt")[0]
    facts_file = glob.glob("../*/r_fact2.txt")[0]

    problem = load_problem(ops_file, facts_file)

    print("=== Opérateurs ===")
    for name, op in problem.operators.items():
        print(f"{name}: params={op.params}")
        print(f"   preconds={op.preconds}")
        print(f"   add={op.add_effects}  del={op.del_effects}")

    print("\n=== Objets ===")
    print(problem.objects_by_type)

    print("\n=== État initial ===")
    print(problem.initial_state)

    print("\n=== Buts ===")
    print(problem.goals)