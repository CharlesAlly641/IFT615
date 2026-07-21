"""
graphplan.py
------------
Algorithme GRAPHPLAN, suivant le pseudocode du cours (diapo 57) :

    function GRAPHPLAN(problem) returns solution or failure
        graph <- INITIAL-PLANNING-GRAPH(problem)
        goals <- GOALS[problem]
        loop do
            if goals all non-mutex in last level of graph then do
                solution <- EXTRACT-SOLUTION(graph, goals, LENGTH(graph))
                if solution != failure then return solution
                else if NO-SOLUTION-POSSIBLE(graph) then return failure
            graph <- EXPAND-GRAPH(graph, problem)

et l'extraction arrière (diapo 58) :

    - Recherche à rebours, niveau par niveau, pour mieux exploiter les mutex
    - Pour chaque but à l'itération n, trouver une action ayant ce but dans
      ses effets et non mutex avec une action déjà choisie
    - Les préconditions de ces actions deviennent les sous-buts à l'étape n-1
    - Mémorisation

La mémorisation (table des "no-goods") retient les couples
(niveau, ensemble de buts) déjà connus comme impossibles, ce qui évite de
refaire une recherche vouée à l'échec. C'est aussi elle qui fournit le
critère d'arrêt de NO-SOLUTION-POSSIBLE.

DoPlan(r_ops, r_facts) est le point d'entrée demandé par l'énoncé.
"""

from typing import Dict, FrozenSet, List, Optional, Tuple

from parseur_donnees import charger_probleme, Litteral
from instanciation import ActionInstanciee, instancier_tous_operateurs
from planning_graph import PlanningGraph

# Table de mémorisation : (niveau, ensemble de buts) -> plan trouvé, ou None
# si on sait déjà que cet ensemble de buts est impossible à ce niveau.
MemoKey = Tuple[int, FrozenSet[Litteral]]
Memo = Dict[MemoKey, Optional[List[FrozenSet[ActionInstanciee]]]]


def _extract_solution(graph: PlanningGraph, goals: FrozenSet[Litteral],
                      level: int, memo: Memo):
    """EXTRACT-SOLUTION : cherche à rebours un plan atteignant `goals` au
    niveau `level`. Retourne la liste des niveaux d'actions (du premier
    exécuté au dernier), ou None en cas d'échec."""

    # Niveau 0 : les buts doivent simplement être vrais dans l'état initial.
    if level == 0:
        return [] if goals <= graph.niveaux_propositions[0] else None

    key = (level, goals)
    if key in memo:
        return memo[key]

    # Si deux buts sont mutex à ce niveau, ils ne peuvent pas être atteints
    # ensemble : inutile de chercher.
    if _any_pair_mutex(goals, graph.niveaux_propositions_mutex[level]):
        memo[key] = None
        return None

    result = _choose_actions(
        graph,
        remaining_goals=list(goals),
        chosen=frozenset(),
        level=level,
        memo=memo,
    )
    memo[key] = result
    return result


def _choose_actions(graph: PlanningGraph, remaining_goals: List[Litteral],
                    chosen: FrozenSet[ActionInstanciee], level: int, memo: Memo):
    """Pour chaque but du niveau, choisit une action le produisant et non
    mutex avec celles déjà choisies ; puis descend d'un niveau avec les
    préconditions de ces actions comme nouveaux sous-buts."""

    if not remaining_goals:
        # Tous les buts de ce niveau sont couverts : les préconditions des
        # actions choisies deviennent les sous-buts du niveau précédent.
        sub_goals = frozenset().union(*(a.preconds for a in chosen)) if chosen else frozenset()
        sub_plan = _extract_solution(graph, sub_goals, level - 1, memo)
        if sub_plan is None:
            return None
        # Les no-op ne sont pas de vraies actions : on ne les garde pas
        # dans le plan final.
        real_actions = frozenset(a for a in chosen if a.operateur != "NOOP")
        return sub_plan + [real_actions]

    goal, *rest = remaining_goals

    # Ce but est peut-être déjà produit par une action déjà choisie.
    if any(goal in a.postconds for a in chosen):
        return _choose_actions(graph, rest, chosen, level, memo)

    action_mutex = graph.niveaux_actions_mutex[level - 1]
    producers = [a for a in graph.niveaux_actions[level - 1] if goal in a.postconds]

    # Ordre d'essai : les no-op (persistance) d'abord. Si un but est déjà
    # atteint à un niveau antérieur, le laisser persister est presque
    # toujours le bon choix ; essayer d'abord de le ré-atteindre par une
    # vraie action envoie la recherche dans des branches où l'on refait
    # inutilement un travail déjà accompli. L'ordre n'affecte que la
    # vitesse de la recherche, pas les plans qu'elle peut trouver.
    producers.sort(key=lambda a: (a.operateur != "NOOP", a.nom))

    for action in producers:
        if any(frozenset({action, c}) in action_mutex for c in chosen):
            continue  # mutex avec une action déjà choisie
        result = _choose_actions(graph, rest, chosen | {action}, level, memo)
        if result is not None:
            return result

    return None  # aucune action ne convient pour ce but


def _any_pair_mutex(literals, prop_mutex) -> bool:
    lits = list(literals)
    for i in range(len(lits)):
        for j in range(i + 1, len(lits)):
            if frozenset({lits[i], lits[j]}) in prop_mutex:
                return True
    return False


def _flatten_plan(plan_levels: List[FrozenSet[ActionInstanciee]]) -> List[str]:
    """Les actions d'un même niveau sont non-mutex entre elles : n'importe
    quel ordre entre elles donne un plan valide. On les sérialise donc
    niveau par niveau."""
    plan = []
    for level_actions in plan_levels:
        for action in sorted(level_actions, key=lambda a: a.nom):
            plan.append(action.nom)
    return plan


def DoPlan(r_ops: str, r_facts: str, verbose: bool = False) -> Optional[List[str]]:
    """Point d'entrée : retourne un plan (liste de noms d'actions) pour le
    problème décrit par r_ops et r_facts, ou None si aucun plan n'existe."""

    problem = charger_probleme(r_ops, r_facts)
    actions = instancier_tous_operateurs(problem)
    graph = PlanningGraph(problem, actions)
    memo: Memo = {}

    if verbose:
        print(f"Objets           : {problem.objects_by_type}")
        print(f"État initial     : {len(problem.initial_state)} faits")
        print(f"Buts             : {len(problem.goals)}")
        print(f"Actions possibles: {len(actions)}\n")

    prev_memo_size = None

    while True:
        if verbose:
            print(f"--- Niveau {graph.profondeur} : {len(graph.niveaux_propositions[-1])} propositions, "
                  f"{len(graph.niveaux_propositions_mutex[-1])} paires mutex ---")

        if graph.buts_realisables():
            if verbose:
                print("  Buts présents et non-mutex -> extraction...")
            solution = _extract_solution(graph, problem.goals, graph.profondeur, memo)
            if solution is not None:
                plan = _flatten_plan(solution)
                if verbose:
                    print(f"  Plan trouvé : {len(plan)} actions.\n")
                return plan
            if verbose:
                print("  Échec de l'extraction à ce niveau.")

            # NO-SOLUTION-POSSIBLE : si le graphe est stabilisé ET que la
            # table de mémorisation n'a plus rien appris depuis la dernière
            # itération, alors aucune expansion supplémentaire ne peut
            # changer le résultat -> il n'existe aucun plan.
            if graph.graphe_est_stable() and len(memo) == prev_memo_size:
                if verbose:
                    print("  Graphe et mémorisation stabilisés -> aucun plan n'existe.")
                return None
            prev_memo_size = len(memo)

        elif graph.graphe_est_stable():
            # Les buts ne sont toujours pas tous présents et non-mutex, alors
            # que le graphe n'évolue plus : étendre davantage ne changera
            # rien, donc ils ne le seront jamais -> aucun plan n'existe.
            # (Sans ce cas, un problème insoluble dont les buts restent
            # mutex fait boucler l'expansion indéfiniment.)
            if verbose:
                print("  Graphe stabilisé et buts toujours inatteignables "
                      "-> aucun plan n'existe.")
            return None

        graph.agrandir()


if __name__ == "__main__":
    import glob
    import time

    ops_file = glob.glob("../*/r_ops.txt")[0]

    for n in ["2", "3", "4", "6", "8", "9"]:
        facts_file = glob.glob(f"../*/r_fact{n}.txt")[0]
        t0 = time.time()
        plan = DoPlan(ops_file, facts_file)
        dt = time.time() - t0
        print(f"=== r_fact{n} ({dt:.2f}s) ===")
        if plan is None:
            print("  Aucun plan trouvé.")
        else:
            print(f"  PLAN ({len(plan)} actions) :")
            for a in plan:
                print(f"    {a}")
        print()