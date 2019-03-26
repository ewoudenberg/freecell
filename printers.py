# Implement TTY (scrolling) and LINE (horizontal) printers for Freecell boards

import sys
import re
from get_terminal_size import get_terminal_size

class TTY:
    def flush(self): pass

    def print_lines(self, lines):
        sys.stdout.write('\n'.join(lines)+'\n')

    def print_footer(self, *args, **kwargs):
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

class LinePrinter:
    def __init__(self):
        self.cols, self.rows = get_terminal_size()
        self.current_block = Block()
        self.blocks = []

    def print_lines(self, lines):
        self.current_block.extend(lines)

    def print_footer(self, *args, **kwargs):
        self.current_block.extend(args)
        self.end_block()

    def end_block(self):
        self.current_block.finalize()
        self.blocks.append(self.current_block)
        self.current_block = Block()

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


