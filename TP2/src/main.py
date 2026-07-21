"""
Devoir 2 - IFT615 : Intelligence artificielle
Membres de l'équipe :
    Charles Ally (ALLC7158),
    Alexy Beaulieu (BEAA6878),
    Justine d'Astous (DASJ6993),
    Alex Phan (PHAA1597),
"""

"""
principal.py
-------------
Point d'entrée du programme (IFT615 - Devoir 2, rocket domain).

Usage :
    python principal.py <r_ops.txt> <r_facts.txt>            plan seulement
    python principal.py <r_ops.txt> <r_facts.txt> --trace    trace complète
    python principal.py <r_ops.txt> <r_facts.txt> --trace > traces/trace_cas3.txt

Le mode --trace affiche le détail de la construction du graphe de
planification (niveaux de propositions et d'actions, ensembles mutex,
tentatives d'extraction), comme demandé pour les deux cas à remettre
(complexité 3 et complexité 9). Sans --trace, seul le plan final est
affiché, au format des fichiers simulation_factX.txt fournis.
"""

import sys
import time

from parseur_donnees import charger_probleme
from instanciation import ground_all_operators
from planning_graph import PlanningGraph
from graphplan import DoPlan, _extract_solution, _flatten_plan


def afficher_plan(plan):
    """Affiche le plan au format attendu (cf. simulation_factX.txt)."""
    print()
    print("PLAN : ")
    print()
    if plan is None:
        print(" (aucun plan n'existe pour ce problème)")
    elif not plan:
        print(" (plan vide : les buts sont déjà satisfaits dans l'état initial)")
    else:
        for action in plan:
            print(f" {action}")
    print()


def afficher_probleme(probleme, actions):
    print("/*---------------------------------------------------------------*/")
    print("/* ---------------------- Problème à résoudre -------------------*/")
    print("/*---------------------------------------------------------------*/")
    print()
    print("Objets du domaine :")
    for type_objet, objets in probleme.objets_par_type.items():
        print(f"  {type_objet:8} : {', '.join(objets)}")
    print()
    print(f"Conditions initiales ({len(probleme.etat_initial)} faits) :")
    for fait in sorted(probleme.etat_initial):
        print(f"  ({' '.join(fait)})")
    print()
    print(f"Objectifs ({len(probleme.buts)}) :")
    for but in sorted(probleme.buts):
        print(f"  ({' '.join(but)})")
    print()
    print(f"Actions instanciées à partir des opérateurs : {len(actions)}")
    print()


def executer_avec_trace(fichier_ops, fichier_facts):
    """Rejoue l'algorithme en affichant le détail de chaque étape."""
    probleme = charger_probleme(fichier_ops, fichier_facts)
    actions = ground_all_operators(probleme)
    graphe = PlanningGraph(probleme, actions)
    memo = {}

    afficher_probleme(probleme, actions)

    print("/*---------------------------------------------------------------*/")
    print("/* ------------- Construction du graphe de planification --------*/")
    print("/*---------------------------------------------------------------*/")
    print()
    print(f"Niveau 0 (propositions) : {len(graphe.prop_levels[0])} propositions "
          f"(état initial), 0 paire mutex")
    print()

    depart = time.time()
    taille_memo_precedente = None

    while True:
        if graphe.goals_reachable():
            print("  -> Tous les buts sont présents et non-mutex à ce niveau.")
            print("     Tentative d'extraction (recherche à rebours)...")

            debut_extraction = time.time()
            solution = _extract_solution(graphe, probleme.buts, graphe.depth, memo)
            duree = time.time() - debut_extraction

            if solution is not None:
                plan = _flatten_plan(solution)
                print(f"     EXTRACTION RÉUSSIE en {duree:.2f}s "
                      f"({len(plan)} actions, {len(solution)} niveaux).")
                print()
                print("     Détail des niveaux du plan (actions parallèles) :")
                for i, niveau in enumerate(solution, start=1):
                    noms = sorted(a.name for a in niveau)
                    print(f"       Niveau {i} : {', '.join(noms) if noms else '(aucune action)'}")
                print()
                print(f"Temps total : {time.time() - depart:.2f}s")
                return plan

            print(f"     Échec de l'extraction à ce niveau ({duree:.2f}s). "
                  f"Table de mémorisation : {len(memo)} entrées.")

            if graphe.has_leveled_off() and len(memo) == taille_memo_precedente:
                print()
                print("  -> Le graphe et la table de mémorisation sont tous deux "
                      "stabilisés :")
                print("     aucune expansion supplémentaire ne peut changer le "
                      "résultat.")
                print(f"Temps total : {time.time() - depart:.2f}s")
                return None

            taille_memo_precedente = len(memo)
            print()

        elif graphe.has_leveled_off() and graphe.depth > 0:
            print("  -> Le graphe est stabilisé et les buts ne sont toujours pas "
                  "tous présents")
            print("     et non-mutex : ils ne le seront jamais -> aucun plan "
                  "n'existe.")
            print(f"Temps total : {time.time() - depart:.2f}s")
            return None

        graphe.expand()

        niveau = graphe.depth
        actions_niveau = graphe.action_levels[-1]
        vraies_actions = [a for a in actions_niveau if a.operator_name != "NOOP"]
        propositions = graphe.prop_levels[-1]

        print(f"Niveau {niveau} (actions) : {len(actions_niveau)} actions "
              f"({len(vraies_actions)} réelles + {len(actions_niveau) - len(vraies_actions)} no-op), "
              f"{len(graphe.action_mutex_levels[-1])} paires mutex")
        print(f"Niveau {niveau} (propositions) : {len(propositions)} propositions, "
              f"{len(graphe.prop_mutex_levels[-1])} paires mutex")

        nouvelles = propositions - graphe.prop_levels[-2]
        if nouvelles:
            apercu = sorted(f"({' '.join(p)})" for p in nouvelles)
            print(f"  Nouvelles propositions ({len(nouvelles)}) : "
                  f"{', '.join(apercu[:6])}{' ...' if len(apercu) > 6 else ''}")

        if not graphe.goals_reachable():
            manquants = probleme.buts - propositions
            if manquants:
                print(f"  Buts pas encore atteignables : {len(manquants)}")
            else:
                print("  Tous les buts sont présents, mais certains sont mutex "
                      "entre eux -> on étend.")
        print()


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        print("Erreur : il faut fournir les deux fichiers d'entrée.")
        print("Exemple : python principal.py ../exemples_fournis/r_ops.txt "
              "../nos_cas_de_test/mon_fact3.txt --trace")
        sys.exit(1)

    fichier_ops = sys.argv[1]
    fichier_facts = sys.argv[2]
    mode_trace = "--trace" in sys.argv[3:]

    if mode_trace:
        plan = executer_avec_trace(fichier_ops, fichier_facts)
    else:
        plan = DoPlan(fichier_ops, fichier_facts)

    print()
    print("/*---------------------------------------------------------------*/")
    print("/* --------------------------- Plan final -----------------------*/")
    print("/*---------------------------------------------------------------*/")
    afficher_plan(plan)


if __name__ == "__main__":
    main()