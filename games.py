# Load the moves.txt file into a dictionary

import re
class Games(dict):
    default_file='fixed_moves.txt'
    def __init__(self, filename=default_file):
        fd = open(filename)
        moves = ''
        game = None
        for i in fd.readlines():
            # Recognize a game header line, e.g. "#29596, longest at 53 moves"
            game_no = re.search(r'#(\d*)', i)
            if game_no:
                if game is not None:
                    self[game] = moves.split()
                moves = ''
                game = int(game_no.group(1))
            else:
                moves += i

        self[game] = moves.split()
