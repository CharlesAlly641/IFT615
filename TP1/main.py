# Devoir 1 - IFT615 : Intelligence artificielle
# Membres de l'équipe : Charles Ally, Justine d'Astous

from os import write
import numpy as np

#Entrée des données du graphe
def initialiser():
    dict_distances = {
    'A' : {'Z' : 75, 'S' : 140, 'T' : 118},
    'Z' : {'A' : 75, 'O' : 71},
    'O' : {'Z' : 71, 'S' : 151},
    'S' : {'A' : 140, 'O' : 151, 'F' : 99, 'R' : 80},
    'T' : {'A' : 118, 'L' : 111},
    'L' : {'T' : 111, 'R' : 91, 'M' : 70},
    'M' : {'L' : 70, 'D' : 75},
    'D' : {'M' : 75, 'C' : 120},
    'C' : {'D' : 120, 'R' : 146, 'G' : 153, 'P' : 138},
    'R' : {'L' : 91, 'C' : 146, 'S' : 80, 'P' : 97},
    'P' : {'R' : 97, 'C' : 138, 'B' : 101},
    'G' : {'C' : 153, 'B' : 90, 'E' : 218},
    'B' : {'P' : 101, 'G' : 90, 'F' : 211, 'U' : 85},
    'E' : {'G' : 218, 'H' : 86},
    'H' : {'E' : 86, 'U' : 98},
    'U' : {'B' : 85, 'H' : 98, 'V' : 142},
    'F' : {'B' : 211, 'S' : 99, 'N' : 187},
    'N' : {'F' : 187, 'I' : 87},
    'I' : {'N' : 87, 'V' : 92},
    'V' : {'I' : 92, 'U' : 142},
}
    dict_coordonnees = {
    "A": { "x": 170, "y": 420 },
    "Z": { "x": 200, "y": 490 },
    "O": { "x": 250, "y": 540 },
    "S": { "x": 310, "y": 400 },
    "T": { "x": 130, "y": 315 },
    "L": { "x": 240, "y": 315 },
    "M": { "x": 190, "y": 265 },
    "D": { "x": 190, "y": 190 },
    "C": { "x": 310, "y": 190 },
    "R": { "x": 350, "y": 340 },
    "P": { "x": 430, "y": 270 },
    "G": { "x": 460, "y": 120 },
    "B": { "x": 500, "y": 200 },
    "E": { "x": 730, "y": 150 },
    "H": { "x": 680, "y": 220 },
    "U": { "x": 585, "y": 200 },
    "F": { "x": 410, "y": 390 },
    "N": { "x": 570, "y": 480 },
    "I": { "x": 600, "y": 400 },
    "V": { "x": 650, "y": 325 }
}

    return dict_distances, dict_coordonnees

def reconstruire_chemin(x, liste_close):
    solution = []
    final = x[0]
    with open('trace2.txt', 'a') as f:
        f.write(f"Solution : ")
        while x[2] != None:
            solution.append(x[0])
            for noeud in liste_close:
                if noeud[0] == x[2]:
                    x = noeud
                    break
        solution.append(x[0])
        solution.reverse()
        for ville in solution:
            if ville != final:
                f.write(f"{ville} -> ")
        f.write(f"{ville}\n")

def calculer_heuristique(depart, arrivee, coordo):
    coordonnee_x = coordo[depart]["x"] - coordo[arrivee]["x"]
    coordonnee_y = coordo[depart]["y"] - coordo[arrivee]["y"]
    return np.sqrt(coordonnee_x ** 2 + coordonnee_y ** 2)


def meilleur_chemin(depart, arrivee, distance_points, coordonnees):
#   nomenclature open  : (point, g(n), parent, f(n))
#   nomenclature close : (point, g(n), parent)
    liste_open = [(depart, 0, None, calculer_heuristique(depart, arrivee, coordonnees))]
    liste_close = []
    compteur = 1

    while liste_open:
        with open('trace2.txt', 'a') as f:
            f.write(f"Iteration #{compteur} Open: {[t[:3] for t in liste_open]}\n")
            f.write(f"Iteration #{compteur} Close: {[t[:2] for t in liste_close]}\n")

        x = liste_open.pop(0)
        if x[0] == arrivee:
            print(f'Chemin trouvé vers {arrivee}')
            reconstruire_chemin(x, liste_close)
            break
        else:
            # Générer les enfants de x
            enfants = distance_points[x[0]]
            for enfant in enfants:
                noeud_dans_open = None
                noeud_dans_close = None

                for noeud in liste_open:
                    if noeud[0] == enfant:
                        noeud_dans_open = noeud
                        break
                for noeud in liste_close:
                    if noeud[0] == enfant:
                        noeud_dans_close = noeud
                        break
                g = x[1] + distance_points[x[0]][enfant]
                h = calculer_heuristique(enfant, arrivee, coordonnees)
                f = g + h

                if not noeud_dans_open and not noeud_dans_close:
                    # L'enfant n'est ni dans open, ni dans close
                    liste_open.append((enfant, g, x[0], f))

                elif noeud_dans_open:
                    # L'enfant est dans open, on vérifie si le nouveau chemin est meilleur
                    if g < noeud_dans_open[1]:
                        liste_open.remove(noeud_dans_open)
                        liste_open.append((enfant, g, x[0], f))

                elif noeud_dans_close:
                    # L'enfant est dans close, on vérifie si le nouveau chemin est meilleur
                    if g < noeud_dans_close[1]:
                        liste_close.remove(noeud_dans_close)
                        liste_open.append((enfant, g, x[0], f))

            liste_close.append(x)
            liste_open.sort(key=lambda noeud: noeud[3])
            compteur += 1

    return 'erreur'

if __name__ == '__main__':
    d, c = initialiser()
    source = input('Ville de départ: ').strip().upper()
    destination = input('Ville d\'arrivée : ').strip().upper()
    if source in d and destination in c:
        meilleur_chemin(source, destination, d, c)
    else:
        print('Erreur : La ville de départ ou d\'arrivée n\'existe pas dans le graphe.')