#!/usr/bin/env python

import sys
import ansi

from printers import TTY, LinePrinter, PrinterSheet
from freecell import Board

Moves = {
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

def main():
    lines = []
    game = 26693
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if filename == 'test':
            lines = Moves[game].split()
        else:
            lines = open(sys.argv[1]).readlines()

    BoardLog = open('cell.log', 'w')

    printer = LinePrinter()
    board = Board(seed=game, printer=printer)
    board.print()

    while not board.is_empty():

        # Try using any supplied input first
        move = lines and lines.pop(0).strip()
        if move:
            printer.print_header(f'{ansi.fg.yellow}# {board.move_counter}. supplied-move: {move}{ansi.reset}')

        # If that's exhausted, ask for manual input
        else:
            printer.flush()
            print('your move? ', end='')
            move = input()
            printer.print_header(f'{ansi.fg.green}# {board.move_counter}. manual-move: {move}{ansi.reset}')

        BoardLog.write(move+'\n')

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
        
if __name__ == '__main__':
    print('Type "./freecell.py test" to run with the builtin test dataset')
    main()