"""
graphe_planification.py
------------------------
Construit le planning graph de Graphplan, niveau par niveau (diapos 55-56
du chapitre 6), et calcule les ensembles mutex à chaque niveau.

Structure du graphe :
    P0 -> A1 -> P1 -> A2 -> P2 -> ...

  - prop_levels[i]         : ensemble de littéraux (propositions) au niveau i
  - action_levels[i]       : actions applicables entre prop_levels[i] et prop_levels[i+1]
                              (inclut les actions no-op, pour la persistance)
  - action_mutex_levels[i] : paires d'actions mutex dans action_levels[i]
  - prop_mutex_levels[i]   : paires de propositions mutex dans prop_levels[i]

Deux littéraux/actions mutex sont représentés par un frozenset({x, y})
de taille 2, mis dans un set() -- pratique et rapide à tester (`in`).
"""

from dataclasses import dataclass, field
from typing import FrozenSet, List, Set

from parseur_donnees import Litteral, ProblemePlanification
from instanciation import ActionInstanciee

MutexPair = FrozenSet  # frozenset({a, b}) de taille 2


def make_noop(literal: Litteral) -> ActionInstanciee:
    """Action no-op : persiste un littéral d'un niveau à l'autre sans rien changer."""
    return ActionInstanciee(
        nom=f"NOOP_{'_'.join(literal)}",
        operateur="NOOP",
        args=literal,
        preconds=frozenset({literal}),
        postconds=frozenset({literal}),
        delete_effects=frozenset(),
    )


@dataclass
class PlanningGraph:
    problem: ProblemePlanification
    all_actions: List[ActionInstanciee]

    prop_levels: List[FrozenSet[Litteral]] = field(default_factory=list)
    action_levels: List[FrozenSet[ActionInstanciee]] = field(default_factory=list)
    action_mutex_levels: List[Set[MutexPair]] = field(default_factory=list)
    prop_mutex_levels: List[Set[MutexPair]] = field(default_factory=list)

    def __post_init__(self):
        self.prop_levels = [self.problem.etat_initial]
        # Au niveau 0, aucune action n'a encore rien produit -> pas de mutex
        # (on suppose l'état initial cohérent, ce qui est le cas ici puisqu'on
        # ne représente que des littéraux positifs, sans négation explicite).
        self.prop_mutex_levels = [set()]

    @property
    def depth(self) -> int:
        """Nombre de niveaux d'actions déjà construits."""
        return len(self.action_levels)

    def expand(self) -> None:
        """Ajoute un niveau au graphe (une couche d'actions + la couche de propositions suivante)."""
        last_props = self.prop_levels[-1]
        last_prop_mutex = self.prop_mutex_levels[-1]

        # Une action est applicable si ses préconditions sont présentes au
        # niveau précédent ET non-mutex deux à deux : deux préconditions
        # mutex ne peuvent jamais être vraies en même temps, donc l'action
        # ne pourrait de toute façon jamais s'exécuter. Sans cette seconde
        # condition, le graphe devient trop optimiste (des propositions
        # apparaissent à des niveaux où elles ne sont pas réellement
        # atteignables) et l'extraction doit ensuite explorer d'énormes
        # branches vouées à l'échec.
        applicable = [
            a for a in self.all_actions
            if a.preconds <= last_props and not self._has_mutex_preconds(a, last_prop_mutex)
        ]
        noops = [make_noop(p) for p in last_props]
        level_actions = applicable + noops

        action_mutex = self._compute_action_mutex(level_actions, last_prop_mutex)

        next_props = frozenset().union(*(a.postconds for a in level_actions)) if level_actions else frozenset()
        prop_mutex = self._compute_prop_mutex(next_props, level_actions, action_mutex)

        self.action_levels.append(frozenset(level_actions))
        self.action_mutex_levels.append(action_mutex)
        self.prop_levels.append(next_props)
        self.prop_mutex_levels.append(prop_mutex)

    @staticmethod
    def _has_mutex_preconds(action: ActionInstanciee, prop_mutex: Set[MutexPair]) -> bool:
        """Vrai si deux préconditions de l'action sont mutex entre elles."""
        preconds = list(action.preconds)
        for i in range(len(preconds)):
            for j in range(i + 1, len(preconds)):
                if frozenset({preconds[i], preconds[j]}) in prop_mutex:
                    return True
        return False

    def _compute_action_mutex(
        self, actions: List[ActionInstanciee], prop_mutex_prev: Set[MutexPair]
    ) -> Set[MutexPair]:
        mutex_pairs: Set[MutexPair] = set()

        for i in range(len(actions)):
            for j in range(i + 1, len(actions)):
                a1, a2 = actions[i], actions[j]
                if self._actions_are_mutex(a1, a2, prop_mutex_prev):
                    mutex_pairs.add(frozenset({a1, a2}))

        return mutex_pairs

    @staticmethod
    def _actions_are_mutex(
        a1: ActionInstanciee, a2: ActionInstanciee, prop_mutex_prev: Set[MutexPair]
    ) -> bool:
        # 1. Inconsistance : l'une annule un effet de l'autre
        if a1.postconds & a2.delete_effects or a2.postconds & a1.delete_effects:
            return True

        # 2. Interférence : l'une supprime une précondition de l'autre
        if a1.delete_effects & a2.preconds or a2.delete_effects & a1.preconds:
            return True

        # 3. Ressources conflictuelles : préconditions mutex entre elles
        for p1 in a1.preconds:
            for p2 in a2.preconds:
                if frozenset({p1, p2}) in prop_mutex_prev:
                    return True

        return False

    @staticmethod
    def _compute_prop_mutex(
        props: FrozenSet[Litteral],
        actions: List[ActionInstanciee],
        action_mutex: Set[MutexPair],
    ) -> Set[MutexPair]:
        # Pour chaque proposition, la liste des actions qui la produisent
        producers = {p: [a for a in actions if p in a.postconds] for p in props}

        prop_list = list(props)
        mutex_pairs: Set[MutexPair] = set()

        for i in range(len(prop_list)):
            for j in range(i + 1, len(prop_list)):
                p1, p2 = prop_list[i], prop_list[j]

                if PlanningGraph._is_negation(p1, p2):
                    mutex_pairs.add(frozenset({p1, p2}))
                    continue

                if PlanningGraph._support_inconsistent(
                    producers[p1], producers[p2], action_mutex
                ):
                    mutex_pairs.add(frozenset({p1, p2}))

        return mutex_pairs

    @staticmethod
    def _is_negation(p1: Litteral, p2: Litteral) -> bool:
        """Vrai si p1 == not(p2). Le domaine rocket ne représente que des
        littéraux positifs (pas de préfixe "not"), donc ce cas ne se
        produit jamais ici -- gardé pour rester général."""
        return (
            p1[0] == "not" and p1[1:] == p2
        ) or (
            p2[0] == "not" and p2[1:] == p1
        )

    @staticmethod
    def _support_inconsistent(
        producers_p1: List[ActionInstanciee],
        producers_p2: List[ActionInstanciee],
        action_mutex: Set[MutexPair],
    ) -> bool:
        """Vrai si TOUTES les paires d'actions productrices de p1 et p2
        sont mutex entre elles (aucune paire ne peut coexister)."""
        if not producers_p1 or not producers_p2:
            return False

        for a in producers_p1:
            for b in producers_p2:
                if a == b:
                    return False  # une même action produit les deux -> pas mutex
                if frozenset({a, b}) not in action_mutex:
                    return False  # une paire compatible existe -> pas mutex

        return True

    def goals_reachable(self) -> bool:
        """Vrai si tous les buts sont présents au dernier niveau et non-mutex entre eux."""
        goals = self.problem.buts
        last_props = self.prop_levels[-1]
        last_prop_mutex = self.prop_mutex_levels[-1]

        if not goals <= last_props:
            return False

        goal_list = list(goals)
        for i in range(len(goal_list)):
            for j in range(i + 1, len(goal_list)):
                if frozenset({goal_list[i], goal_list[j]}) in last_prop_mutex:
                    return False

        return True

    def has_leveled_off(self) -> bool:
        """Vrai si le graphe s'est stabilisé (2 derniers niveaux identiques,
        propositions ET mutex) -- signe qu'il est inutile de continuer à
        étendre le graphe si les buts ne sont toujours pas atteignables."""
        if len(self.prop_levels) < 2:
            return False
        return (
            self.prop_levels[-1] == self.prop_levels[-2]
            and self.prop_mutex_levels[-1] == self.prop_mutex_levels[-2]
        )


if __name__ == "__main__":
    import glob
    from parseur_donnees import charger_probleme
    from instanciation import instancier_tous_operateurs

    ops_file = glob.glob("../*/r_ops.txt")[0]
    facts_file = glob.glob("../*/r_fact2.txt")[0]

    problem = charger_probleme(ops_file, facts_file)
    actions = instancier_tous_operateurs(problem)

    graph = PlanningGraph(problem, actions)

    for niveau in range(1, 6):
        graph.expand()
        print(f"--- Après expansion {niveau} ---")
        print(f"  # actions niveau: {len(graph.action_levels[-1])} "
              f"(dont mutex: {len(graph.action_mutex_levels[-1])})")
        print(f"  # propositions niveau: {len(graph.prop_levels[-1])} "
              f"(dont mutex: {len(graph.prop_mutex_levels[-1])})")
        print(f"  buts atteignables et non-mutex ? {graph.goals_reachable()}")
        if graph.goals_reachable():
            break