import chess
import chess.pgn
import io
import string
import random
import math
import sys

board = chess.Board()

def generate_random_string(length):
    chars = string.ascii_letters + string.digits
    return bytes(''.join(random.choice(chars) for i in range(length)), "utf-8")

def sort_moves(board):
    legal_moves = list(board.legal_moves)
    return sorted(legal_moves, key=lambda move: board.san(move))

def is_checkmate_or_draw(board, move):
    board.push(move)
    result = board.is_checkmate() or len(list(board.legal_moves)) == 0
    board.pop()
    return result


def get_weighted_entropy_distribution(board):
    entropies = []
    total = 0
    for move in sort_moves(board):
        board.push(move)
        responses = len(list(board.legal_moves))
        board.pop()
        entropies.append((move, responses))
        total += responses
    return entropies, total

def filter_moves(board, engine, threshold, depth):
    analysis = engine.analyse(board, chess.engine.Limit(depth=depth), multipv=256)
    current_score = analysis[0]["score"].white().score()
    authorized_moves = []
    a = 0
    for i in analysis:
        score = i["score"].white().score()
        if not current_score:
            if score:
                authorized_moves.append(i["pv"][0])
        elif score and abs(current_score - score ) < threshold:
            authorized_moves.append(i["pv"][0])
    if len(authorized_moves) == 0:
        engine.quit()
        raise ValueError("Impossible to encode your data with this threshold. Try to increase it.\n\nFEN of last position : " + board.fen())
    return sorted(authorized_moves, key=lambda move: board.san(move))


def get_optimal_possible_moves(board, engine=None, threshold=None, depth=None):
    if engine:
        possible_moves = filter_moves(board, engine, threshold, depth)
    else:
        possible_moves = sort_moves(board)
    entropies, total = get_weighted_entropy_distribution(board)
    if total == 0:
        return [m for m, _ in entropies]
    move_weights = [(m, r / total) for m, r in entropies]
    threshold = 0.9*sum([x[1] for x in move_weights])/len(move_weights)
    weak_moves = [m for m, w in move_weights if w < threshold]
    return [m for m, _ in entropies if m not in weak_moves]

def get_possible_moves(board, engine=None, threshold=None, depth=None):
    if engine:
        legal_moves = filter_moves(board, engine, threshold, depth)
    else:
        legal_moves = list(board.legal_moves)
    non_mate_moves = filter(lambda move: not is_checkmate_or_draw(board, move), legal_moves)
    return sorted(list(non_mate_moves), key=lambda move : board.san(move) )

def encode(bytes_string, func, fen=None, engine=None, threshold=50, depth=6):
    if engine:
        engine = chess.engine.SimpleEngine.popen_uci(engine)
    board = chess.Board(fen) if fen else chess.Board()
    bytes_string = b'\x01' + bytes_string
    value = int.from_bytes(bytes_string, byteorder='little')

    while value > 0:
        moves = func(board, engine, threshold, depth)
        base = len(moves)
        if base == 0:
            if engine:
                engine.quit()
            raise ValueError("Impossible to encode your data from this starting position. Try to change it to prevent this error.")

        reste = value % base
        value = value // base
        move = moves[reste]
        board.push(move)
    if engine:
        engine.quit()
    game = chess.pgn.Game()
    return game.from_board(board)

def decode(pgn, func, fen=None, engine=None, threshold=50, depth=6):
    if engine:
        engine = chess.engine.SimpleEngine.popen_uci(engine)
    game = chess.pgn.read_game(io.StringIO(pgn))
    board = game.board()
    if not fen:
        fen = board.fen()

    value = 0
    indices = []
    move_list = list(game.mainline_moves())
    if len(move_list) == 0:
        if engine:
            engine.quit()
        raise ValueError("The PGN you passed have no moves")
    should_start = False

    for move in move_list:
        if board.fen() == fen:
            should_start = True
        if should_start:
            possible_moves = func(board, engine, threshold, depth)
            index = possible_moves.index(move)
            indices.append((index, len(possible_moves)))
        board.push(move)

    if engine:
        engine.quit()
        sys.stdout.flush()

    if len(indices) == 0:
        raise ValueError("Specified FEN was not found in this game.")


    # Reconstruction du nombre à l'envers
    for index, base in reversed(indices):
        value = value * base + index

    byte_length = (value.bit_length() + 7) // 8
    return value.to_bytes(byte_length, byteorder='little')[1:]
