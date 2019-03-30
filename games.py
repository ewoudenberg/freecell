# Load the moves.txt file into a dictionary

class Games(dict):
    def __init__(self):
        fd = open('moves.txt')
        moves = ''
        game = None
        for i in fd.readlines():
            # Parse: #17768 Adrian Ettlinger 
            if i.startswith('#'):
                if game is not None:
                    self[game] = moves.split()
                moves = ''
                game = int(i.split()[0][1:])
            else:
                moves += i

        self[game] = moves
