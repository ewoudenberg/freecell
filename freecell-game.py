#!/usr/bin/env python

# User interface to the Freecell game engine

import sys
import getopt
import ansi

from printers import TTY, LinePrinter, PrinterSheet
from freecell import Board

Games = {
10913: '''
    26 76 72 72 5a 27 57 67 1b 61 41 4h 4h 
    41 45 34 3c 6d 5b''',
26693: '''
    8a	81	2b	26	72	4c	45	74	78	76
    71	51	71	15	27	26	27	21	12	1d
    17	12	17	18	3h	13	d3	b1	81	68
    6b	5h	6h	68	2h	ch	21	32	3c	3d
    38	43	52	85	86'''
}

def usage():
    print(f'''\nusage: freecell.py [options]
    Options:
       -f n or --freecells=n - set number of freecells (0-{len(Board.FreeCellNames)} default: 4)
       -c n or --cascades=n - set number of cascades (1-{len(Board.CascadeNames)} default: 8)
       -p n or --play-back=n - play back game number n (only 10913 and 26693 work)
       -g n or --game n - play game n (default: 10913)
       -F <file> --file <file> - take input from a file (default: keyboard)
       -i or --ignore-dependencies - auto-moves ignore dependencies on other cards on the board
       -h --help print this help sheet
    Try "./freecell.py -p 10913" to rn with the builtin test
''')
    sys.exit(1)

class Options:
    def __init__(self):
        try:
            optslist, self.argv = getopt.getopt(sys.argv[1:], 'f:c:p:g:F:hi', 
                    ['freecells=', 'cascades=', 'play-back=', 'game=', 'file=',
                     'help', 'ignore-dependencies'])

        except getopt.GetoptError as err:
                print(f'*** {err} ***\n')
                usage()
 
        self.freecells = 4
        self.cascades = 8
        self.play_back = False
        self.game = 10913
        self.input = None
        self.ignore_dependencies = False

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
            else:
                usage()

        if self.input and self.play_back:
            print('*** Cannot specify both --input and --playback ***')
            usage()

Opts = Options()

def play():
    moves = []
    printer = LinePrinter()

    if Opts.play_back:
        if Opts.game not in Games:
            print(f'*** Game {Opts.game} not available for playback ***')
            usage()
        moves = Games[Opts.game].split()

    if Opts.input:
        if not os.path.exists(input):
            print(f'*** File {Opts.input} does not exist ***')
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
        if move:
            printer.print_header(f'{ansi.fg.yellow}# {board.move_counter}. supplied-move: {move}{ansi.reset}')

        # If that's exhausted, ask for manual input
        else:
            printer.flush()
            print('your move? ', end='')
            move = input()
            printer.print_header(f'{ansi.fg.green}# {board.move_counter}. manual-move: {move}{ansi.reset}')

        movesLog.write(move+'\n')

        if move == 'u':
            board.undo()
            board.print()
            continue

        valid = board.move(move, save_history=True)
        if not valid: 
            # Skip automated moves after errors since otherwise an error 
            # at move 0 might allow automated moves to happen.
            continue

        board.print()

        for move in board.automatic_moves():
            board.move(move)
            printer.print_header(f'{ansi.fg.red}# {board.move_counter}. auto-move: {move}{ansi.reset}')
            board.print()

    printer.flush()
        

def main():
    try:
        play()
    except Exception as e:
        print(f'*** {e} ***')
        usage()

if __name__ == '__main__':
    main()