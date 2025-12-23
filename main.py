"""Stegachess - Outil de stéganographie pour encoder/décoder des données dans des parties d'échecs

Ce module permet de cacher des données binaires dans des parties d'échecs en utilisant
l'ordre des coups comme méthode d'encodage.
"""

import argparse  # Pour parser les arguments de ligne de commande
import sys
from utils import encode, decode, get_possible_moves, get_optimal_possible_moves, generate_random_string

def main():
    """Fonction principale pour encoder ou décoder des données dans une partie d'échecs.
    
    Gère les arguments de ligne de commande et orchestre le processus d'encodage/décodage.
    """
    # Création du parser d'arguments pour l'interface en ligne de commande
    parser = argparse.ArgumentParser(description="Encode or decode data into a chess game.")

    # Argument obligatoire : chemin du fichier d'entrée
    parser.add_argument("-i", "--input", required=True,
                        help="Specify the path from the input file you want to encode/decode.")

    # Mode d'opération : encoder ou décoder (mutuellement exclusifs)
    parser.add_argument("-e", "--encode", action="store_true",
                        help="Use the encode function.")
    parser.add_argument("-d", "--decode", action="store_true",
                        help="Use the decode function.")

    # Option de compression : utilise l'entropie pour réduire le nombre de coups
    parser.add_argument("-c", "--compress", action="store_true",
                        help="Try to chose moves with a lot of entropy to limit the size of the final game.")
    # Fichier de sortie (optionnel, sinon affichage sur stdout)
    parser.add_argument("-o", "--output", default=None,
                        help="Specify the path to the output file. If not specified, output is logged to stdout.")
    # Position de départ personnalisée en notation FEN (Forsyth-Edwards Notation)
    parser.add_argument("-f", "--fen", default=None,
                        help="Specify the FEN, AKA the starting position.")

    # Options du moteur d'échecs pour générer des coups plus réalistes
    parser.add_argument("--engine", type=str, default=None,
                        help="The engine used to calculate more logical moves.")
    parser.add_argument("--depth", type=int, default=6,
                        help="The depth of the engine calculation. Use with --engine.")
    parser.add_argument("--threshold", type=int, default=50,
                        help="The threshold of centipawn accepted to filter moves. Use with --engine.")

    # Parse les arguments de la ligne de commande
    args = parser.parse_args()

    # Vérifie qu'on a exactement un mode (encode XOR decode)
    if args.encode == args.decode:
        parser.error("You must specify either --encode or --decode, but not both.")

    # Sélection de la fonction de génération de coups selon le mode compression
    move_func = get_optimal_possible_moves if args.compress else get_possible_moves

    # Récupération des paramètres optionnels
    fen = args.fen
    engine = args.engine
    threshold = args.threshold
    depth = args.depth

    # Mode encodage : convertit les données binaires en partie d'échecs
    if args.encode:
        # Lecture du fichier d'entrée en mode binaire
        with open(args.input, "rb") as f:
            byte_data = f.read()
        # Encodage des données dans une partie d'échecs
        game = encode(
            byte_data,
            move_func,
            fen=fen,
            engine=engine,
            threshold=threshold,
            depth=depth
        )
        # Conversion de la partie en format PGN (Portable Game Notation)
        output = str(game)

    # Mode décodage : extrait les données d'une partie d'échecs
    elif args.decode:
        # Lecture du fichier PGN contenant la partie d'échecs
        with open(args.input, "r", encoding="utf-8") as f:
            pgn_data = f.read()
        # Décodage des données cachées dans la partie
        result_bytes = decode(
            pgn_data,
            move_func,
            fen=fen,
            engine=engine,
            threshold=threshold,
            depth=depth
        )
        output = result_bytes

    # Gestion de la sortie (fichier ou stdout)
    if args.output:
        # Mode d'écriture : binaire pour les bytes, texte pour les strings
        mode = "wb" if isinstance(output, bytes) else "w"
        with open(args.output, mode) as f:
            f.write(output)
    else:
        # Affichage sur la sortie standard
        if isinstance(output, bytes):
            print(output)
        else:
            print(output)


def main2():
    """Fonction de test pour comparer l'efficacité de la compression.
    
    Génère 10 chaînes aléatoires de 1Ko et compare le nombre de coups
    nécessaires avec et sans compression.
    """
    """Fonction de test pour comparer l'efficacité de la compression.
    
    Génère 10 chaînes aléatoires de 1Ko et compare le nombre de coups
    nécessaires avec et sans compression.
    """
    for i in range(10):
        # Génère une chaîne aléatoire de 1000 caractères
        rs = generate_random_string(1000)
        print(f"Test {i} (1Ko)")
        # Encode sans compression
        uncompressed = len(list(encode(bytes(rs), get_possible_moves).mainline_moves()))
        # Encode avec compression (optimisation de l'entropie)
        compressed = len(list(encode(bytes(rs), get_optimal_possible_moves).mainline_moves()))
        print(f"{uncompressed} moves for uncompressed version")
        print(f"{compressed} moves for compressed version")
        # Calcule et affiche le pourcentage de compression
        print("Efficacity : " + str(round(100 - compressed*100 / uncompressed, 2)) + "% Compressed !\n")
        



if __name__ == "__main__":
    main()
