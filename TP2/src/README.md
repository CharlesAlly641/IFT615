# Devoir 2 - IFT615

Implémentation d'un planificateur de tâches en utilisant 
la théorie des graphes de synthèse. Ce fichier contient
une courte présentation de la structure général de notre TP ainsi que la justification de certains de nos choix d'implémentation

## Structure générale

Chaque fichier de notre TP correspond à une étape
de transformation entre le texte d'entrée et le plan final :

```
texte (r_ops.txt, r_fact.txt)
        │  traitement_fichier.py   (tokenizer générique)
        ▼
listes Python imbriquées
        │  parseur_donnees.py      (interprétation du domaine)
        ▼
Operateur / ProblemePlanification (avec variables)
        │  instanciation.py        (substitution des variables)
        ▼
ActionInstanciee (actions concrètes)
        │  planning_graph.py       (construction + mutex)
        ▼
PlanningGraph (niveaux P0-A1-P1-A2-P2-...)
        │  graphplan.py            (recherche à rebours)
        ▼
Plan (liste de noms d'actions) ou None
```

Chaque fichier a une responsabilité claire, ce qui a permis de développer et tester chaque
fonctionnalité en parallèle. Dans chacun des fichiers, on peut retrouver une courte section 
permettant de s'assurer que le fichier effectue bien la tâche pour laquelle il a été écrit.

## Rôle de chaque fichier

- **`traitement_fichier.py`** — Analyseur syntaxique générique : lit le
  texte brut des fichiers r_ops et r_fact et le décortique en
  plusieurs éléments qu'on met dans des listes Python. Rien de spécifique 
  à la planification ou au rocket domain.
- **`parseur_donnees.py`** — Donne un sens aux listes Python : reconnaît les
  blocs `operator`, `preconds`, `effects`, etc., et construit
  `Operateur` et `ProblemePlanification`.
- **`instanciation.py`** — Substitue les variables des opérateurs
  génériques (`<rocket>`) par les objets concrets, pour produire toutes
  les `ActionInstanciee` possibles.
- **`planning_graph.py`** — Construit le graphe niveau par niveau
  (avec la fonction `agrandir()`) et calcule les ensembles mutex (actions et
  propositions).
- **`graphplan.py`** — Implémente les algorithmes `Graphplan` et `EXTRACT-SOLUTION` (recherche à
  rebours avec mémorisation) présentés dans le cours et contient la fonction
  `DoPlan(r_ops, r_facts)` qui retourne  un plan 
   optimal d’actions pour atteindre les objectifs à partir des conditions de départ.
- **`main.py`** — Interface en ligne de commande qui permet d'appeller `DoPlan`. Le mode --trace affiche 
  le détail de la construction du graphe de planification pour les traces à remettre spécifiquement.

## Choix de structure de données : `set` / `frozenset`
### Pourquoi?

Dans le cours, nous décrivions un état (état initial, buts, préconditions, niveau de propositions) 
comme étant un ensemble de faits. Cela implique que l'ordre n'importe pas et que nous ne voulons pas de
doublons. Un `set` permet donc d'écrire directement les opérations dont
l'algorithme a besoin. Par exemple, si nous souhaitons savoir si des conditions sont incluses dans un
autre ensemble, nous pouvons simplement faire preconds <= propositions. Une liste aurait pu être un autre
choix valide mais cela aurait simplement alourdi des opérations traitées simplement avec un set. 

On utilise plus précisément `frozenset` (version immuable du `set`)
quand l'ensemble doit lui-même être stocké dans une autre collection :

- une **paire mutex** est un ensemble non ordonné de deux éléments —
  `frozenset({a1, a2}) == frozenset({a2, a1})` ;
- une **clé de la table de mémorisation** (`(niveau, buts)`) doit être
  hashable, donc immuable, ce qu'un `set` normal ne permet pas.

Le `frozenset` est donc simplement un `set` avec la contrainte
d'immuabilité nécessaire pour ces deux usages.

## Pourquoi Element = Union[str, List["Element"]]
Le texte source a des parenthèses imbriquées. Par exemple, operator contient 
params, qui contient des paires (<object> CARGO)). La récursivité est nécessaire 
pour représenter ça : un Element est soit un mot (str), soit une liste d'Elements qui peuvent 
eux-mêmes être des mots ou d'autres listes, à n'importe quelle profondeur. str seul ne suffirait 
pas, puisqu'il ne pourrait pas représenter un groupement entre parenthèses.

## (À rédiger) Pourquoi tuple dans parseur_données

## Autres choix d'implémentation notables

- **`@dataclass(frozen=True)` pour `ActionInstanciee`** : rend les
  actions immuables et hashables, pour pouvoir les mettre dans des
  `frozenset`.
