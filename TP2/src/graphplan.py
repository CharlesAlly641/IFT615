"""
L'algorithme principal, fidèle au pseudocode de la diapo 57 : la fonction `DoPlan(r_ops, r_facts)` alterne expansion du graphe (`graphe_planification.py`) et tentative d'extraction de solution en chaînage arrière (recherche des actions satisfaisant chaque but/sous-but, niveau par niveau, avec mémorisation). Retourne le plan optimal ou un échec.
"""