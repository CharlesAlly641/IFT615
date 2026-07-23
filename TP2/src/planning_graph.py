"""
Construit le planning graph de Graphplan, niveau par niveau,
et calcule l'ensemble mutex avec les actions et propositions à chaque niveau.

Structure : P0 -> A1 -> P1 -> A2 -> P2 -> ...
  - niveaux_propositions[i]       : propositions au niveau i
  - niveaux_actions[i]            : actions au niveau i (incluant les no-op, pour la persistance)
  - niveaux_actions_mutex[i]      : paires d'actions mutuellement exclusives au niveau i
  - niveaux_propositions_mutex[i] : paires de propositions mutuellement exclusives au niveau i
"""

from dataclasses import dataclass, field
from typing import FrozenSet, List, Set

from parseur_donnees import Proposition, ProblemePlanification
from instanciation import ActionInstanciee

PaireMutex = FrozenSet  # frozenset({a, b}) de taille 2


def action_noop(literal: Proposition) -> ActionInstanciee:
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
    probleme: ProblemePlanification
    liste_actions: List[ActionInstanciee]

    niveaux_propositions: List[FrozenSet[Proposition]] = field(default_factory=list)
    niveaux_actions: List[FrozenSet[ActionInstanciee]] = field(default_factory=list)
    niveaux_actions_mutex: List[Set[PaireMutex]] = field(default_factory=list)
    niveaux_propositions_mutex: List[Set[PaireMutex]] = field(default_factory=list)

    def __post_init__(self):
        # Aucun mutex au premier niveau
        self.niveaux_propositions = [self.probleme.etat_initial]
        self.niveaux_propositions_mutex = [set()]

    @property
    def profondeur(self) -> int:
        """Nombre de niveaux d'actions déjà construits."""
        return len(self.niveaux_actions)

    def agrandir(self) -> None:
        """Ajoute un niveau au graphe (actions + propositions)."""
        propositions_precedentes = self.niveaux_propositions[-1]
        propositions_precedentes_mutex = self.niveaux_propositions_mutex[-1]

        # Une action est applicable si ses préconditions sont présentes au
        # niveau de proposition précédent et si ses préconditions ne sont pas mutex.
        actions_applicables = [
            a for a in self.liste_actions
            # On vérifie si les preconds de a font partie du niveau de proposition précédent
            if a.preconds <= propositions_precedentes
            # On vérifie qu'il n'existe pas de paire de préconds qui sont mutex
            and not self.preconds_sont_mutex(a, propositions_precedentes_mutex)
        ]
        # Construction du nouveau niveau d'actions
        noops = [action_noop(p) for p in propositions_precedentes]
        actions_courantes = actions_applicables + noops
        propositions_courantes = frozenset().union(
            *(a.postconds for a in actions_courantes)) if actions_courantes else frozenset()

        # Construction de l'ensemble mutex
        mutex_actions_courantes = self.construire_mutex_actions(actions_courantes, propositions_precedentes_mutex)
        mutex_propositions_courantes = self.construire_mutex_propositions(propositions_courantes, actions_courantes, mutex_actions_courantes)

        # Ajout du nouveau niveau
        self.niveaux_actions.append(frozenset(actions_courantes))
        self.niveaux_actions_mutex.append(mutex_actions_courantes)
        self.niveaux_propositions.append(propositions_courantes)
        self.niveaux_propositions_mutex.append(mutex_propositions_courantes)

    # ------------------------------------------------------------
    # Les fonctions suivantes aident à construire l'ensemble mutex
    # ------------------------------------------------------------

    @staticmethod
    def preconds_sont_mutex(action: ActionInstanciee, prop_mutex: Set[PaireMutex]) -> bool:
        """Vrai si deux préconditions de l'action sont mutex entre elles."""
        preconds = list(action.preconds)
        for i in range(len(preconds)):
            for j in range(i + 1, len(preconds)):
                if frozenset({preconds[i], preconds[j]}) in prop_mutex:
                    return True
        return False

    def construire_mutex_actions(
        self, actions: List[ActionInstanciee], mutex_propositions: Set[PaireMutex]
    ) -> Set[PaireMutex]:
        mutex_actions: Set[PaireMutex] = set()

        for i in range(len(actions)):
            for j in range(i + 1, len(actions)):
                a1, a2 = actions[i], actions[j]
                if self.actions_sont_mutex(a1, a2, mutex_propositions):
                    mutex_actions.add(frozenset({a1, a2}))

        return mutex_actions

    @staticmethod
    def actions_sont_mutex(
        a1: ActionInstanciee, a2: ActionInstanciee, mutex_propositions: Set[PaireMutex]
    ) -> bool:
        # Inconsistance : l'une annule l'effet d'une autre
        if a1.postconds & a2.delete_effects or a2.postconds & a1.delete_effects:
            return True

        # Interférence : l'une supprime la précondition d'une autre
        if a1.delete_effects & a2.preconds or a2.delete_effects & a1.preconds:
            return True

        # Ressources conflictuelles : elles ont des préconditions mutex
        for p1 in a1.preconds:
            for p2 in a2.preconds:
                if frozenset({p1, p2}) in mutex_propositions:
                    return True

        return False

    @staticmethod
    def construire_mutex_propositions(
        propositions: FrozenSet[Proposition],
        actions: List[ActionInstanciee],
        action_mutex: Set[PaireMutex],
    ) -> Set[PaireMutex]:
        # Pour chaque proposition, la liste des actions qui la produisent
        actions_candidates = {}
        for p in propositions:
            actions_candidates[p] = [a for a in actions if p in a.postconds]

        liste_propositions = list(propositions)
        mutex_propositions: Set[PaireMutex] = set()

        for i in range(len(liste_propositions)):
            for j in range(i + 1, len(liste_propositions)):
                p1, p2 = liste_propositions[i], liste_propositions[j]

                # Une proposition est la négation de l'autre
                if PlanningGraph.est_negation(p1, p2):
                    mutex_propositions.add(frozenset({p1, p2}))
                    continue

                # Toutes les paires d'actions qui ont des propositions comme effets
                if PlanningGraph.support_inconsistant(
                    actions_candidates[p1], actions_candidates[p2], action_mutex
                ):
                    mutex_propositions.add(frozenset({p1, p2}))

        return mutex_propositions

    @staticmethod
    def est_negation(p1: Proposition, p2: Proposition) -> bool:
        """Vrai si p1 == not(p2)"""
        return (
            p1[0] == "not" and p1[1:] == p2
        ) or (
            p2[0] == "not" and p2[1:] == p1
        )

    @staticmethod
    def support_inconsistant(
        producteurs_p1: List[ActionInstanciee],
        producteurs_p2: List[ActionInstanciee],
        action_mutex: Set[PaireMutex],
    ) -> bool:
        """Vrai si toutes les paires d'actions productrices de p1 et p2
        sont mutex entre elles (aucune paire ne peut coexister)."""
        if not producteurs_p1 or not producteurs_p2:
            return False

        for a in producteurs_p1:
            for b in producteurs_p2:
                if a == b:
                    return False  # une même action produit les deux
                if frozenset({a, b}) not in action_mutex:
                    return False  # une paire compatible existe

        return True

    def buts_realisables(self) -> bool:
        """Vrai si tous les buts sont présents au dernier niveau et non-mutex entre eux."""
        buts_du_probleme = self.probleme.buts
        dernier_niveau_proposition = self.niveaux_propositions[-1]
        dernier_niveau_proposition_mutex = self.niveaux_propositions_mutex[-1]

        if not buts_du_probleme <= dernier_niveau_proposition:
            return False # Les buts ne sont pas atteints

        buts = list(buts_du_probleme)
        for i in range(len(buts)):
            for j in range(i + 1, len(buts)):
                if frozenset({buts[i], buts[j]}) in dernier_niveau_proposition_mutex:
                    return False

        return True

    def graphe_est_stable(self) -> bool:
        """Vrai si le graphe s'est stabilisé (2 derniers niveaux identiques,
        propositions et mutex). Si c'est vrai, cela signifie que les buts ne seront
        pas atteints s'ils ne le sont pas déjà."""
        if len(self.niveaux_propositions) < 2:
            return False
        return (
                self.niveaux_propositions[-1] == self.niveaux_propositions[-2]
                and self.niveaux_propositions_mutex[-1] == self.niveaux_propositions_mutex[-2]
        )

# Test local du fichier
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
        graph.agrandir()
        print(f"--- Après expansion {niveau} ---")
        print(f"  # actions niveau: {len(graph.niveaux_actions[-1])} "
              f"(dont mutex: {len(graph.niveaux_actions_mutex[-1])})")
        print(f"  # propositions niveau: {len(graph.niveaux_propositions[-1])} "
              f"(dont mutex: {len(graph.niveaux_propositions_mutex[-1])})")
        print(f"  buts atteignables et non-mutex ? {graph.buts_realisables()}")
        if graph.buts_realisables():
            break