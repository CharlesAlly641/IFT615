
graph = {
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

def validation(graph):
    for ville, voisins in graph.items():
        for voisin, dist in voisins.items():
            if ville not in graph[voisin]:
                print(f"Manquant: {voisin} -> {ville}")
            if graph[voisin][ville] != dist:
                print(f"Distance différente: {ville}-{voisin}")


if __name__ == '__main__':
    validation(graph)
