"""
Adaptation de l'algorithme Graphplan des notes de cours :
    function GRAPHPLAN(problem) returns solution or failure
        graph <- INITIAL-PLANNING-GRAPH(problem)
        goals <- GOALS[problem]
        loop do
            if goals all non-mutex in last level of graph then do
                solution <- EXTRACT-SOLUTION(graph, goals, LENGTH(graph))
                if solution != failure then return solution
                else if NO-SOLUTION-POSSIBLE(graph) then return failure
            graph <- EXPAND-GRAPH(graph, problem)
La fonction DoPlan(r_ops, r_facts) est le point d'entrée demandé dans l'énoncé.
"""

from typing import Dict, FrozenSet, List, Optional, Tuple

from parseur_donnees import charger_probleme, Proposition
from instanciation import ActionInstanciee, instancier_tous_operateurs
from planning_graph import PlanningGraph

# Table de mémorisation pour la recherche à rebours.
# Contient le niveau du graphe, l'ensemble des sous-buts et la liste d'actions si valide
MemoKey = Tuple[int, FrozenSet[Proposition]]
Memo = Dict[MemoKey, Optional[List[FrozenSet[ActionInstanciee]]]]


def extract_solution(graphe: PlanningGraph, buts: FrozenSet[Proposition],
                     niveau: int, memo: Memo):
    """Rcherche à rebours un plan atteignant les buts à un certaine niveau.
    Retourne la liste des niveaux d'actions (du premier exécuté au dernier),
     ou None en cas d'échec."""

    if niveau == 0:
        # Les buts doivent être vrais dans l'état initial.
        return [] if buts <= graphe.niveaux_propositions[0] else None

    key = (niveau, buts)
    if key in memo:
        return memo[key]

    # Exploiter les relations mutex.
    # Si mutex alors pas de possiblité de satisfaire les buts à ce niveau.
    if paire_est_mutex(buts, graphe.niveaux_propositions_mutex[niveau]):
        memo[key] = None
        return None

    # Trouver une action ayant le but dans ces effets
    result = choisir_action(
        graphe,
        buts_restants=list(buts),
        choix=frozenset(),
        niveau=niveau,
        memo=memo,
    )
    memo[key] = result
    return result


def choisir_action(graphe: PlanningGraph, buts_restants: List[Proposition],
                   choix: FrozenSet[ActionInstanciee], niveau: int, memo: Memo):
    """
    Pour chaque but du niveau, trouver une action ayant ce but dans ses effets
    et non mutex avec une action déjà choisie.
    """

    if not buts_restants:
        # Les préconditions des actions choisies deviennent les sous-buts du niveau précédent.
        sous_buts = frozenset().union(*(a.preconds for a in choix)) if choix else frozenset()
        # Récursion vers le niveau précédent
        sous_plan = extract_solution(graphe, sous_buts, niveau - 1, memo)
        if sous_plan is None:
            return None
        # On retire les actions noop dans le plan final
        vraies_actions = frozenset(a for a in choix if a.operateur != "NOOP")
        return sous_plan + [vraies_actions]

    goal, *rest = buts_restants

    # Ce but est peut-être déjà produit par une action déjà choisie.
    if any(goal in a.postconds for a in choix):
        return choisir_action(graphe, rest, choix, niveau, memo)

    action_mutex = graphe.niveaux_actions_mutex[niveau - 1]
    actions_candidates = [a for a in graphe.niveaux_actions[niveau - 1] if goal in a.postconds]

    # Les NOOP sont essayés en premier afin de limiter les branches explorées.
    # Cela améliore les performances sans modifier la validité du résultat.
    actions_candidates.sort(key=lambda a: (a.operateur != "NOOP", a.nom))

    for action in actions_candidates:
        if any(frozenset({action, c}) in action_mutex for c in choix):
            continue  # mutex avec une action déjà choisie
        result = choisir_action(graphe, rest, choix | {action}, niveau, memo)
        if result is not None:
            return result

    return None  # aucune action ne convient pour ce but


def paire_est_mutex(litterals, prop_mutex) -> bool:
    lits = list(litterals)
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
        print(f"Objets           : {problem.objets_par_type}")
        print(f"État initial     : {len(problem.etat_initial)} faits")
        print(f"Buts             : {len(problem.buts)}")
        print(f"Actions possibles: {len(actions)}\n")

    prev_memo_size = None

    while True:
        if verbose:
            print(f"--- Niveau {graph.profondeur} : {len(graph.niveaux_propositions[-1])} propositions, "
                  f"{len(graph.niveaux_propositions_mutex[-1])} paires mutex ---")

        if graph.buts_realisables():
            if verbose:
                print("  Buts présents et non-mutex -> extraction...")
            solution = extract_solution(graph, problem.buts, graph.profondeur, memo)
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