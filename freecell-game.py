#!/usr/bin/env python

# User interface to the Freecell game engine

import sys
import os
import getopt
import ansi

from printers import TTY, LinePrinter, PrinterSheet
from freecell import Board
from games import Games

Solved_Games = Games()

def usage():
    example_games = ', '.join(f'{i}' for i in list(Solved_Games.keys())[:20])
    print(f'''\nusage: freecell.py [options]

Generate MS compatible Freecell deals and play them.

    Options:
       -f or --freecells n - set number of freecells (0-{len(Board.FreeCellNames)} default: 4)
       -c or --cascades n - set number of cascades (1-{len(Board.CascadeNames)} default: 8)
       -p or --play-back n - play back game number n (e.g. {example_games})
       -P play back all available solved games
       -g or --game n - play game n (default: {Opts.game})
       -F or --file <file> - take input from a file (default: keyboard)
       -i or --ignore-dependencies - make the auto-mover ignore dependencies on other cards on the board
       -M or --possible-moves - show possible moves before waiting for user input
       -h --help print this help sheet
    Try e.g. "{sys.argv[0]} -p {Opts.game}" to run with a builtin game

Game features:

 o Plays a standard MS freecell game, using the standard 2 character move syntax:
     <source><destination> where source is "1-9", "a-d" and destination adds "h" for home.
 o The character '#' when used as a destination indicates the first available freecell.
 o Use the single character "u" to undo a move.
 o The game logs all user moves to the file "moves.log". These can be played back with the
   option "-F moves.log".

FAILING GAMES:
    ./freecell-game.py -P --skip 7,10,63,86,96,1072,1150,1734,2670,3294,3342,3349,3631 --jump 3294

''')
    sys.exit(1)

class Options:
    def __init__(self):
        try:
            optslist, self.argv = getopt.getopt(sys.argv[1:], 'f:c:p:g:F:hiMP', 
                    ['freecells=', 'cascades=', 'play-back=', 'game=', 'file=',
                     'help', 'ignore-dependencies', 'possible-moves','skip=','jump='])

        except getopt.GetoptError as err:
                print(f'*** {err} ***\n')
                usage()
 
        first_game = list(Solved_Games.keys())[0]

        self.freecells = 4
        self.cascades = 8
        self.play_back = False
        self.game = first_game
        self.input = None
        self.ignore_dependencies = False
        self.help = False
        self.possible_moves = False
        self.play_all = False
        self.skips = []
        self.jump = 0

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
            elif arg in ('--possible-moves', '-M'):
                self.possible_moves = True
            elif arg in ('-P',):
                self.play_all = True
            elif arg in ('--skip'):
                self.skips = [int(i) for i in val.split(',')]
            elif arg in ('--jump'):
                self.jump = int(val)
            elif arg in ('-h', '--help'):
                self.help = True

        if self.input and self.play_back:
            print('*** Cannot specify both --input and --playback ***')
            self.help = False

Opts = Options()

def print_possible_moves(board):
    print('Available moves: ', end='')
    for i in board.get_possible_moves():
        print(f'{i} ', end='')
    print()

def freecell():
    moves = []

    if Opts.play_back:
        if Opts.game not in Solved_Games:
            print(f'*** Game "{Opts.game}" not available for playback ***')
            usage()
        moves = Solved_Games[Opts.game]

    if Opts.input:
        if not os.path.exists(Opts.input):
            print(f'*** File "{Opts.input}"" does not exist ***')
            usage()
        moves = open(Opts.input).readlines()

    if Opts.play_all:
        for i in Solved_Games:
            if i > Opts.jump and i not in Opts.skips:
                play(i, Solved_Games[i])
    else:
        play(Opts.game, moves)

def play(seed, moves):
    movesLog = open('moves.log', 'w')
    printer = LinePrinter()

    print(f'\n*** Game #{seed} ***\n')

    board = Board(seed=seed, printer=printer, 
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
            # If a supplied move is invalid, bail out.
            if is_supplied_move:
                printer.flush()
                return
            # Skip automated moves after errors since otherwise an error 
            # at move 0 might allow automated moves to happen.
            continue

        board.print()

        for move in board.automatic_moves():
            printer.print_header(f'{ansi.fg.red}# {board.move_counter}. auto-move: {move}{ansi.reset}')
            board.move(move)
            board.print()

    printer.flush()
        
def main():
    if Opts.help:
        usage()

    try:
        freecell()
    except Exception as e:
        print(f'*** {e} ***')
        usage()

if __name__ == '__main__':
    main()