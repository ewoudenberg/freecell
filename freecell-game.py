#!/usr/bin/env python

# User interface to the Freecell game engine

import getopt
import os
import sys
from collections import defaultdict

import ansi
from freecell import Board, GameException
from games import Games
from printers import TTY, LinePrinter, PrinterSheet

Solved_Games = Games()

def usage():
    example_games = ', '.join(f'{i}' for i in list(Solved_Games.keys())[:20])
    print(f'''\nusage: freecell.py [options]

Generate MS compatible Freecell deals and play them.

    Options:
       -f or --freecells n - set number of freecells (0-{len(Board.FreeCellNames)} default: 4)
       -c or --cascades n - set number of cascades (1-{len(Board.CascadeNames)} default: 8)
       -p or --play-back n - play back game number n (e.g. {example_games})
       -P - play back all available solved games in moves file.
       -g or --game n - play game n (default: {Opts.game})
       -F or --file <file> - take input from a file (default: keyboard)
       -i or --ignore-dependencies - make the auto-mover ignore dependencies on other cards on the board
       -A or --available-moves - show possible moves before waiting for user input
       -M or --moves-file - load moves from given file (default "{Games.default_file}")
       -t or --tty - use tty printer (default line printer)
       --no-automoves - turn off automover
       -h or --help - print this help sheet
    Try e.g. "{sys.argv[0]} -p {Opts.game}" to run with a builtin game

Game features:

 o Plays a standard MS freecell game, using the standard 2 character move syntax:
     <source><destination> where source is "1-9", "a-d" and destination adds "h" for home.
 o The character '#' when used as a destination indicates the first available freecell.
 o Use the single character "u" to undo a move and "r" to redo a previously undone move.
 o The game logs all user moves to the file "moves.log". These can be played back with the
   option "-F moves.log".
''')
    sys.exit(1)

class Options:
    def __init__(self):
        global Solved_Games

        self.freecells = 4
        self.cascades = 8
        self.play_back = False
        first_game = list(Solved_Games.keys())[0]
        self.game = first_game
        self.input = None
        self.ignore_dependencies = False
        self.help = False
        self.possible_moves = False
        self.play_all = False
        self.skips = []
        self.jump = 0
        self.tty = False
        self.no_automoves = False

        try:
            optslist, self.argv = getopt.getopt(sys.argv[1:], 'f:c:p:g:F:hiPAM:t', 
                    ['freecells=', 'cascades=', 'play-back=', 'game=', 'file=',
                     'help', 'ignore-dependencies', 'available-moves','skip=','jump=',
                     'moves-file=', 'tty','no-automoves'])

        except getopt.GetoptError as err:
                print(f'\n*** {err} ***\n')
                self.help = True
                return
 
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
            elif arg in ('--available-moves', '-A'):
                self.possible_moves = True
            elif arg in ('--moves-file', '-M'):
                Solved_Games = Games(val)
            elif arg in ('-P',):
                self.play_all = True
            elif arg in ('--skip'):
                self.skips = [int(i) for i in val.split(',')]
            elif arg in ('--jump'):
                self.jump = int(val)
            elif arg in ('--tty', '-t'):
                self.tty = True
            elif arg in ('--no-automoves',):
                self.no_automoves = True
            elif arg in ('--help', '-h'):
                self.help = True

        if self.input and self.play_back:
            print('*** Cannot specify both --input and --playback ***')

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
        passings = defaultdict(int)
        for i in Solved_Games:
            if i > Opts.jump and i not in Opts.skips:
                result = play(i, Solved_Games[i])
                passings[result] += 1

        print(f'Number that completed {passings[True]}', file=sys.stderr)
        print(f'Number that failed to complete {passings[False]}', file=sys.stderr)

    else:
        play(Opts.game, moves)

# The central game-play UI loop.
# Plays one game by instantiating a board and feeding moves to it.
# Moves are read the supplied list or user input.
# The user commands (undo/redo) are processed here.

def play(seed, moves):
    movesLog = open('moves.log', 'w')
    printer = TTY() if Opts.tty else LinePrinter() 

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
            # If supplied input is exhausted, ask the user for input
            printer.flush()
            if Opts.possible_moves:
                print_possible_moves(board)
            print('Your move? ', end='')
            move = input()

        movesLog.write(move+'\n')

        if move == 'u':
            success = board.undo()
            if not success:
                print('Nothing to undo')
            else:
                board.print()
            continue

        if move == 'r':
            success = board.redo()
            if not success:
                print('Nothing to redo')
            else:
                board.print()
            continue

        move_type = 'supplied' if is_supplied_move else 'manual'
        color = ansi.fg.yellow if is_supplied_move else ansi.fg.green
        printer.print_header(f'{color}# {board.move_counter}. {move_type}-move: {move}{ansi.reset}')

        valid = board.move(move, save_history=not is_supplied_move)
        if not valid:
            # If a supplied move is invalid, bail out.
            if is_supplied_move:
                printer.flush()
                print(f'*** Failed Game #{seed} ***')
                return False
            # Skip automated moves after errors since otherwise an error 
            # at move 0 might allow automated moves to happen.
            continue

        board.print()

        if not Opts.no_automoves:
            for move in board.automatic_moves():
                printer.print_header(f'{ansi.fg.red}# {board.move_counter}. auto-move: {move}{ansi.reset}')
                board.move(move)
                board.print()

    printer.flush()

    print(f'\n*** Completed Game #{seed} ***\n')
    return True        
        
def main():
    if Opts.help:
        usage()

    try:
        freecell()
    except GameException as e:
        print(f'*** Internal Game Engine Error: {e} ***')
        usage()

if __name__ == '__main__':
    main()
