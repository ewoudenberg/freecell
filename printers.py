# Implement TTY (scrolling) and LINE (horizontal) printers for Freecell boards

import sys
import re
import os
import ansi
from io import StringIO

class PrinterSheet:
    def __init__(self):
        self.output_file = StringIO()

    def print(self, *args, **kwargs):
        print(*args, **kwargs, file=self.output_file)

    def printcard(self, card):
        chars = ansi.bg.green
        if card:
            chars += card.as_string()
        else:
            chars += '   '
        chars += ansi.bg.black
        print(chars, end='', file=self.output_file)

    def output(self):
        print(self.output_file.getvalue(), end='')

    def get_lines(self):
        return self.output_file.getvalue().splitlines()

class TTY:
    def flush(self): pass

    def print_lines(self, lines):
        sys.stdout.write('\n'.join(lines)+'\n')

    def print_header(self, *args, **kwargs):
        print(*args, **kwargs)
        if 'end' not in kwargs:
            print()
        
Ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

def get_printing_length(line):
    return len(Ansi_escape.sub('', line))

class Block(list): 
    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)

    def finalize(self):
        self.rows = len(self)
        self.cols = max(get_printing_length(i) for i in self)

    def get_row(self, row):
        if row >= len(self):
            return ' '*self.cols
        return self[row] + (' ' * (self.cols - get_printing_length(self[row])))

MARGIN = 2 # 2 columns between blocks

def get_terminal_size():
    rows_cols = os.popen('stty size', 'r').read().split()
    return (int(i) for i in rows_cols)

class LinePrinter:
    def __init__(self):
        self.rows, self.cols = get_terminal_size()
        self.current_block = Block()
        self.blocks = []
        self.header = []

    def print_lines(self, lines):
        self.current_block.extend(lines)

    def print_sheet(self, sheet: PrinterSheet):
        self.current_block.extend(sheet.get_lines())
        self.end_block()

    def print_header(self, *args, **kwargs):
        self.header.extend(args)

    def end_block(self):
        self.current_block[0:0] = self.header or [' ']
        self.current_block.finalize()
        self.blocks.append(self.current_block)
        self.current_block = Block()
        self.header = []

    def flush(self):
        while True:
            blocks_that_fit = self.get_blocks_that_fit()
            if not blocks_that_fit:
                break
            self.belo_horizonte(blocks_that_fit)

    def get_blocks_that_fit(self):
        col_budget = self.cols
        to_print = []
        while self.blocks:
            block_cols = self.blocks[0].cols + MARGIN
            if block_cols > col_budget:
                break
            col_budget -= block_cols
            to_print.append(self.blocks.pop(0))
        return to_print

    def belo_horizonte(self, blocks_that_fit):
        rows = max(i.rows for i in blocks_that_fit)
        for row in range(rows):
            for block in blocks_that_fit:
                print(block.get_row(row) + ' '*MARGIN, end='')
            print()
        print()
        print()


