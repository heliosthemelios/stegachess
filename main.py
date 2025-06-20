import argparse
import sys
from utils import encode, decode, get_possible_moves, get_optimal_possible_moves, generate_random_string

def main():
    parser = argparse.ArgumentParser(description="Encode or decode data into a chess game.")

    parser.add_argument("-i", "--input", required=True,
                        help="Specify the path from the input file you want to encode/decode.")

    parser.add_argument("-e", "--encode", action="store_true",
                        help="Use the encode function.")
    parser.add_argument("-d", "--decode", action="store_true",
                        help="Use the decode function.")

    parser.add_argument("-c", "--compress", action="store_true",
                        help="Try to chose moves with a lot of entropy to limit the size of the final game.")
    parser.add_argument("-o", "--output", default=None,
                        help="Specify the path to the output file. If not specified, output is logged to stdout.")
    parser.add_argument("-f", "--fen", default=None,
                        help="Specify the FEN, AKA the starting position.")

    parser.add_argument("--engine", type=str, default=None,
                        help="The engine used to calculate more logical moves.")
    parser.add_argument("--depth", type=int, default=6,
                        help="The depth of the engine calculation. Use with --engine.")
    parser.add_argument("--threshold", type=int, default=50,
                        help="The threshold of centipawn accepted to filter moves. Use with --engine.")

    args = parser.parse_args()

    if args.encode == args.decode:
        parser.error("You must specify either --encode or --decode, but not both.")

    move_func = get_optimal_possible_moves if args.compress else get_possible_moves

    fen = args.fen
    engine = args.engine
    threshold = args.threshold
    depth = args.depth

    if args.encode:
        with open(args.input, "rb") as f:
            byte_data = f.read()
        game = encode(
            byte_data,
            move_func,
            fen=fen,
            engine=engine,
            threshold=threshold,
            depth=depth
        )
        output = str(game)

    elif args.decode:
        with open(args.input, "r", encoding="utf-8") as f:
            pgn_data = f.read()
        result_bytes = decode(
            pgn_data,
            move_func,
            fen=fen,
            engine=engine,
            threshold=threshold,
            depth=depth
        )
        output = result_bytes

    if args.output:
        mode = "wb" if isinstance(output, bytes) else "w"
        with open(args.output, mode) as f:
            f.write(output)
    else:
        if isinstance(output, bytes):
            print(output)
        else:
            print(output)


def main2():
    for i in range(10):
        rs = generate_random_string(1000)
        print(f"Test {i} (1Ko)")
        uncompressed = len(list(encode(bytes(rs), get_possible_moves).mainline_moves()))
        compressed = len(list(encode(bytes(rs), get_optimal_possible_moves).mainline_moves()))
        print(f"{uncompressed} moves for uncompressed version")
        print(f"{compressed} moves for compressed version")
        print("Efficacity : " + str(round(100 - compressed*100 / uncompressed, 2)) + "% Compressed !\n")
        



if __name__ == "__main__":
    main()
