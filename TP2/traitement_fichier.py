"""
Le parseur générique de S-expressions. Deux fonctions principales : `tokenize()` (découpe le texte en tokens `(`, `)` et atomes, en gérant les `\r\n` et les commentaires `/* ... */`) et `parse_all()` (transforme les tokens en listes Python imbriquées). Ne connaît rien au rocket domain — réutilisable tel quel. **Déjà écrit.**
"""