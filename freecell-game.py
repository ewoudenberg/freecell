#!/usr/bin/env python

# User interface to the Freecell game engine

import sys
import os
import getopt
import ansi

from printers import TTY, LinePrinter, PrinterSheet
from freecell import Board

def usage():
    available_games = ', '.join(f'{i}' for i in Games.keys())
    print(f'''\nusage: freecell.py [options]

Generate MS compatible Freecell deals and play them.

    Options:
       -f or --freecells n - set number of freecells (0-{len(Board.FreeCellNames)} default: 4)
       -c or --cascades n - set number of cascades (1-{len(Board.CascadeNames)} default: 8)
       -p or --play-back n - play back game number n (only these are avaialble: {available_games})
       -g or --game n - play game n (default: {Opts.game})
       -F or --file <file> - take input from a file (default: keyboard)
       -i or --ignore-dependencies - make the auto-mover ignore dependencies on other cards on the board
       -P or --possible-moves - show possible moves before waiting for user input
       -h --help print this help sheet
    Try e.g. "{sys.argv[0]} -p {Opts.game}" to run with a builtin game

Game features:

 o Plays a standard MS freecell game, using the standard 2 character move syntax:
     <source><destination> where source is "1-9", "a-d" and destination adds "h" for home.
 o The character '#' when used as a destination indicates the first available freecell.
 o Use the single character "u" to undo a move.
 o The game logs all user moves to the file "moves.log". These can be played back with the
   option "-F moves.log".

''')
    sys.exit(1)

class Options:
    def __init__(self):
        try:
            optslist, self.argv = getopt.getopt(sys.argv[1:], 'f:c:p:g:F:hiP', 
                    ['freecells=', 'cascades=', 'play-back=', 'game=', 'file=',
                     'help', 'ignore-dependencies', 'possible-moves'])

        except getopt.GetoptError as err:
                print(f'*** {err} ***\n')
                usage()
 
        first_game = list(Games.keys())[0]

        self.freecells = 4
        self.cascades = 8
        self.play_back = False
        self.game = first_game
        self.input = None
        self.ignore_dependencies = False
        self.help = False
        self.possible_moves = False

        for arg, val in optslist:
            if arg in ('--freecells', '-f'):
                self.freecells = int(val)
            elif arg in ('--cascades', '-c'):
                self.cascades = int(val)
            elif arg in ('--play-back', '-p'):
                self.play_back = True
                self.game = int(val)
            elif arg in ('--game', '-g'):
                self.game = int(val)
            elif arg in ('--file', '-F'):
                self.input = val
            elif arg in ('--ignore-dependencies', '-i'):
                self.ignore_dependencies = True
            elif arg in ('--possible-moves', '-P'):
                self.possible_moves = True
            elif arg in ('-h', '--help'):
                self.help = True

        if self.input and self.play_back:
            print('*** Cannot specify both --input and --playback ***')
            self.help = False

def print_possible_moves(board):
    print('Available moves: ', end='')
    for i in board.get_possible_moves():
        print(f'{i} ', end='')
    print()

def play():
    printer = LinePrinter()
    moves = []

    if Opts.play_back:
        if Opts.game not in Games:
            print(f'*** Game "{Opts.game}" not available for playback ***')
            usage()
        moves = Games[Opts.game].split()

    if Opts.input:
        if not os.path.exists(Opts.input):
            print(f'*** File "{Opts.input}"" does not exist ***')
            usage()
        moves = open(Opts.input).readlines()

    movesLog = open('moves.log', 'w')

    board = Board(seed=Opts.game, printer=printer, 
                  freecells=Opts.freecells, cascades=Opts.cascades,
                  ignore_dependencies=Opts.ignore_dependencies)
    board.print()

    while not board.is_empty():

        
        # Try using any supplied input first
        move = moves and moves.pop(0).strip()
        is_supplied_move = bool(move)

        if not is_supplied_move:
            # If that's exhausted, ask the user for input
            printer.flush()
            if Opts.possible_moves:
                print_possible_moves(board)
            print('Your move? ', end='')
            move = input()

        movesLog.write(move+'\n')

        if move == 'u':
            board.undo()
            board.print()
            continue

        if is_supplied_move:
            printer.print_header(f'{ansi.fg.yellow}# {board.move_counter}. supplied-move: {move}{ansi.reset}')
        else:
            printer.print_header(f'{ansi.fg.green}# {board.move_counter}. manual-move: {move}{ansi.reset}')

        valid = board.move(move, save_history=True)
        if not valid: 
            # Skip automated moves after errors since otherwise an error 
            # at move 0 might allow automated moves to happen.
            continue

        board.print()

        for move in board.automatic_moves():
            printer.print_header(f'{ansi.fg.red}# {board.move_counter}. auto-move: {move}{ansi.reset}')
            board.move(move)
            board.print()

    printer.flush()
        
# A few solved games from https://freecellgamesolutions.com

Games = {
    10913: '''
        26 76 72 72 5a 27 57 67 1b 61 41 4h 4h 
        41 45 34 3c 6d 5b''',
    26693: '''
        8a	81	2b	26	72	4c	45	74	78	76
        71	51	71	15	27	26	27	21	12	1d
        17	12	17	18	3h	13	d3	b1	81	68
        6b	5h	6h	68	2h	ch	21	32	3c	3d
        38	43	52	85	86''',
    29596: '''
        7a	7b	3c	32	73	63	5d	57	46	42
        47	c7	67	5c	57	d7	b5	45	4b	47
        37	35	1d	14	34	24	c1	23	2c	28
        21	24	26	b2	62	32	a4	13	18	16
        1a	a1	c1	51	52	85	65	86	82	82
        83	73	78''',
    31465: '''
        62	6a	1b	16	18	18	13	1c	61	6d
        c6	a6	d6	4a	4c	41	4d	48	7h	6h
        6h	d6	4d	b4	d4	18	7b	7h	57	5d
        51	c5	75	7h	31	3c	3h	3h	34	c4
        63	81	86	87	8c	85	8h	54	58	25
        2d	2b'''
}

Opts = Options()

def main():
    if Opts.help:
        usage()

    try:
        play()
    except Exception as e:
        print(f'*** {e} ***')
        usage()

if __name__ == '__main__':
    main()