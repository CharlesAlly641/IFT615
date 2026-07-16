"""
La couche métier par-dessus `sexpr.py`. Contient la classe `Operator` (nom, params typés, préconditions, add/del-effects) et les fonctions `parse_operators()`, `parse_facts()`, `load_problem()` qui lisent respectivement `r_ops.txt` et `r_factX.txt` pour produire : le dict des opérateurs, les objets typés (PLACE/ROCKET/CARGO), l'état initial et les buts. **Déjà écrit.**
"""