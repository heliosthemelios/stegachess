"""Module utilitaire pour la stéganographie dans les parties d'échecs.

Ce module contient toutes les fonctions d'encodage et de décodage permettant
de cacher des données binaires dans des parties d'échecs en utilisant l'ordre
des coups légaux comme système de numération à base variable.
"""

import chess  # Bibliothèque pour la logique des échecs
import chess.pgn  # Pour la gestion du format PGN
import io  # Pour la manipulation des flux de données
import string
import random  # Pour la génération de données de test
import math
import sys

# Plateau d'échecs global (non utilisé dans le code principal)
board = chess.Board()

def generate_random_string(length):
    """Génère une chaîne aléatoire pour les tests.
    
    Args:
        length: Longueur de la chaîne à générer
        
    Returns:
        bytes: Chaîne aléatoire encodée en UTF-8
    """
    # Utilise lettres (majuscules et minuscules) + chiffres
    chars = string.ascii_letters + string.digits
    return bytes(''.join(random.choice(chars) for i in range(length)), "utf-8")

def sort_moves(board):
    """Trie les coups légaux par ordre alphabétique de leur notation SAN.
    
    Le tri est crucial pour l'encodage/décodage : il garantit que l'ordre
    des coups est le même à l'encodage et au décodage.
    
    Args:
        board: Plateau d'échecs (chess.Board)
        
    Returns:
        list: Liste des coups triés par notation SAN (Standard Algebraic Notation)
    """
    legal_moves = list(board.legal_moves)
    return sorted(legal_moves, key=lambda move: board.san(move))

def is_checkmate_or_draw(board, move):
    """Vérifie si un coup mène à un échec et mat ou une position sans coups légaux.
    
    Ces positions terminent la partie et empêchent de continuer l'encodage,
    donc elles sont filtrées.
    
    Args:
        board: Plateau d'échecs
        move: Coup à vérifier
        
    Returns:
        bool: True si le coup termine la partie, False sinon
    """
    board.push(move)  # Joue le coup temporairement
    result = board.is_checkmate() or len(list(board.legal_moves)) == 0
    board.pop()  # Annule le coup
    return result


def get_weighted_entropy_distribution(board):
    """Calcule la distribution d'entropie des coups possibles.
    
    L'entropie d'un coup est mesurée par le nombre de réponses possibles.
    Plus un coup a de réponses possibles, plus il offre d'opportunités
    d'encodage pour la suite, améliorant ainsi la compression.
    
    Args:
        board: Plateau d'échecs
        
    Returns:
        tuple: (liste de tuples (coup, nombre_réponses), total des réponses)
    """
    entropies = []
    total = 0
    for move in sort_moves(board):
        board.push(move)  # Joue le coup temporairement
        responses = len(list(board.legal_moves))  # Compte les réponses possibles
        board.pop()  # Annule le coup
        entropies.append((move, responses))
        total += responses
    return entropies, total

def filter_moves(board, engine, threshold, depth):
    """Filtre les coups pour ne garder que ceux qui sont raisonnables d'un point de vue tactique.
    
    Utilise un moteur d'échecs pour évaluer les coups et ne garde que ceux
    dont l'évaluation est proche du meilleur coup (dans un seuil de centipions).
    Cela rend la partie encodée plus crédible.
    
    Args:
        board: Plateau d'échecs
        engine: Moteur d'échecs (UCI)
        threshold: Seuil en centipions (100 = 1 pion)
        depth: Profondeur de recherche du moteur
        
    Returns:
        list: Liste des coups autorisés, triés
        
    Raises:
        ValueError: Si aucun coup ne satisfait le seuil
    """
    # Analyse multi-PV : obtient l'évaluation de tous les coups légaux
    analysis = engine.analyse(board, chess.engine.Limit(depth=depth), multipv=256)
    current_score = analysis[0]["score"].white().score()  # Score du meilleur coup
    authorized_moves = []
    a = 0
    for i in analysis:
        score = i["score"].white().score()
        # Gère les cas où le score est un mat (None)
        if not current_score:
            if score:
                authorized_moves.append(i["pv"][0])
        # Garde les coups dont l'évaluation est proche du meilleur
        elif score and abs(current_score - score ) < threshold:
            authorized_moves.append(i["pv"][0])
    # Vérifie qu'on a au moins un coup valide
    if len(authorized_moves) == 0:
        engine.quit()
        raise ValueError("Impossible to encode your data with this threshold. Try to increase it.\n\nFEN of last position : " + board.fen())
    return sorted(authorized_moves, key=lambda move: board.san(move))


def get_optimal_possible_moves(board, engine=None, threshold=None, depth=None):
    """Obtient les coups optimaux pour la compression (mode --compress).
    
    Filtre les coups qui offrent peu de réponses possibles (faible entropie)
    pour privilégier ceux qui permettent plus d'encodage par la suite.
    Cela réduit le nombre total de coups nécessaires.
    
    Args:
        board: Plateau d'échecs
        engine: Moteur d'échecs optionnel pour filtrer les coups tactiques
        threshold: Seuil en centipions pour le filtrage tactique
        depth: Profondeur de recherche du moteur
        
    Returns:
        list: Liste des coups optimaux pour la compression
    """
    # Filtre d'abord par pertinence tactique si un moteur est fourni
    if engine:
        possible_moves = filter_moves(board, engine, threshold, depth)
    else:
        possible_moves = sort_moves(board)
    # Calcule l'entropie de chaque coup
    entropies, total = get_weighted_entropy_distribution(board)
    if total == 0:
        return [m for m, _ in entropies]
    # Normalise les poids (nombre de réponses / total)
    move_weights = [(m, r / total) for m, r in entropies]
    # Calcule un seuil : 90% de la moyenne des poids
    threshold = 0.9*sum([x[1] for x in move_weights])/len(move_weights)
    # Identifie les coups faibles (sous le seuil)
    weak_moves = [m for m, w in move_weights if w < threshold]
    # Retourne tous les coups sauf les faibles
    return [m for m, _ in entropies if m not in weak_moves]

def get_possible_moves(board, engine=None, threshold=None, depth=None):
    """Obtient tous les coups possibles pour l'encodage (mode normal, sans compression).
    
    Filtre uniquement les coups qui terminent la partie (mat ou pat) car ils
    empêcheraient de continuer l'encodage.
    
    Args:
        board: Plateau d'échecs
        engine: Moteur d'échecs optionnel pour filtrer les coups tactiques
        threshold: Seuil en centipions pour le filtrage tactique
        depth: Profondeur de recherche du moteur
        
    Returns:
        list: Liste des coups possibles, triés
    """
    # Filtre par pertinence tactique si un moteur est fourni
    if engine:
        legal_moves = filter_moves(board, engine, threshold, depth)
    else:
        legal_moves = list(board.legal_moves)
    # Retire les coups qui terminent la partie
    non_mate_moves = filter(lambda move: not is_checkmate_or_draw(board, move), legal_moves)
    return sorted(list(non_mate_moves), key=lambda move : board.san(move) )

def encode(bytes_string, func, fen=None, engine=None, threshold=50, depth=6):
    """Encode des données binaires dans une partie d'échecs.
    
    Principe : Convertit les bytes en un grand nombre, puis utilise une numération
    à base variable où chaque position (coup) a une base égale au nombre de coups
    possibles à ce moment. Le reste de la division donne l'index du coup à jouer.
    
    Args:
        bytes_string: Données binaires à encoder
        func: Fonction pour obtenir les coups possibles (get_possible_moves ou get_optimal_possible_moves)
        fen: Position de départ optionnelle (FEN)
        engine: Chemin vers un moteur d'échecs UCI optionnel
        threshold: Seuil en centipions pour le filtrage tactique
        depth: Profondeur de recherche du moteur
        
    Returns:
        chess.pgn.Game: Partie d'échecs contenant les données encodées
        
    Raises:
        ValueError: Si l'encodage est impossible (position bloquée)
    """
    # Initialise le moteur si fourni
    if engine:
        engine = chess.engine.SimpleEngine.popen_uci(engine)
    # Crée le plateau avec la position de départ
    board = chess.Board(fen) if fen else chess.Board()
    # Ajoute un byte de début (0x01) pour éviter les problèmes avec les zéros de tête
    bytes_string = b'\x01' + bytes_string
    # Convertit les bytes en un grand nombre entier
    value = int.from_bytes(bytes_string, byteorder='little')

    # Boucle principale d'encodage : continue tant qu'il reste des données
    while value > 0:
        # Obtient les coups possibles pour cette position
        moves = func(board, engine, threshold, depth)
        base = len(moves)  # Nombre de coups = base de numération
        # Vérifie qu'on a au moins un coup possible
        if base == 0:
            if engine:
                engine.quit()
            raise ValueError("Impossible to encode your data from this starting position. Try to change it to prevent this error.")

        # Calcule le reste : donne l'index du coup à jouer
        reste = value % base
        value = value // base  # Prépare pour le prochain coup
        move = moves[reste]  # Sélectionne le coup correspondant
        board.push(move)  # Joue le coup
    # Ferme le moteur si utilisé
    if engine:
        engine.quit()
    # Convertit le plateau en objet partie PGN
    game = chess.pgn.Game()
    return game.from_board(board)

def decode(pgn, func, fen=None, engine=None, threshold=50, depth=6):
    """Décode les données cachées dans une partie d'échecs.
    
    Principe inverse de l'encodage : pour chaque coup de la partie, trouve son
    index dans la liste des coups possibles, puis reconstruit le nombre original
    en utilisant la formule : valeur = valeur * base + index
    
    Args:
        pgn: Partie d'échecs au format PGN (string)
        func: Fonction pour obtenir les coups possibles (doit être la même qu'à l'encodage)
        fen: Position de départ optionnelle (doit être la même qu'à l'encodage)
        engine: Chemin vers un moteur d'échecs UCI optionnel
        threshold: Seuil en centipions pour le filtrage tactique
        depth: Profondeur de recherche du moteur
        
    Returns:
        bytes: Données binaires décodées
        
    Raises:
        ValueError: Si le PGN est vide ou si la FEN n'est pas trouvée
    """
    # Initialise le moteur si fourni
    if engine:
        engine = chess.engine.SimpleEngine.popen_uci(engine)
    # Parse le PGN pour obtenir l'objet partie
    game = chess.pgn.read_game(io.StringIO(pgn))
    board = game.board()  # Obtient la position de départ
    if not fen:
        fen = board.fen()  # Utilise la position de départ du PGN

    # Initialisation du décodage
    value = 0
    indices = []  # Liste des (index, base) pour chaque coup
    move_list = list(game.mainline_moves())  # Tous les coups de la partie
    # Vérifie que la partie contient des coups
    if len(move_list) == 0:
        if engine:
            engine.quit()
        raise ValueError("The PGN you passed have no moves")
    should_start = False  # Flag pour commencer le décodage à la bonne position

    # Parcourt tous les coups de la partie
    for move in move_list:
        # Attend d'atteindre la position de départ spécifiée
        if board.fen() == fen:
            should_start = True
        if should_start:
            # Obtient les coups possibles à cette position
            possible_moves = func(board, engine, threshold, depth)
            # Trouve l'index du coup joué
            index = possible_moves.index(move)
            # Enregistre (index, base) pour la reconstruction
            indices.append((index, len(possible_moves)))
        board.push(move)  # Joue le coup

    # Ferme le moteur si utilisé
    if engine:
        engine.quit()
        sys.stdout.flush()

    # Vérifie que la FEN de départ a été trouvée
    if len(indices) == 0:
        raise ValueError("Specified FEN was not found in this game.")


    # Reconstruction du nombre à l'envers (de la fin vers le début)
    # Formule : valeur = (valeur * base) + index
    for index, base in reversed(indices):
        value = value * base + index

    # Convertit le nombre en bytes
    byte_length = (value.bit_length() + 7) // 8  # Calcule le nombre de bytes nécessaires
    # Retire le byte de début (0x01) ajouté lors de l'encodage
    return value.to_bytes(byte_length, byteorder='little')[1:]
