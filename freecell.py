#!/usr/bin/env python

# This generates MS compatible Freecell deals and plays back solutions.
# Original © Copyright 2019 Lawrence E. Bakst All Rights Reserved
# Mods by E. Woudenberg

import random
import ansi
import math
import copy
from io import StringIO

CardRanks = 'A23456789TJQK'
CardSuits = 'CDHS'
SuitsGlyphs = '♣♦♥♠'
DECK_SIZE = 52

class MoveException(Exception):
    pass

# This is intended to be an MS compiler runtime compatible version of rand.

class Random:
    def __init__(self, seed):
        self.test()
        self.state = seed

    def random(self):
        self.state = ((214013 * self.state) + 2531011) % 2147483648 # mod 2^31
        return self.state // 65536

    def test(self):
        self.state = 1
        first5 = [self.random() for i in range(5)]
        if first5 != [41, 18467, 6334, 26500, 19169]:
            print('Caution! Random number generator FAILS to match MS compiler runtime')

# Create a deck of cards
def NewDeck(n=DECK_SIZE):
    return [Card(i) for i in range(1, n+1)]

def GetShuffledDeck(seed):
    shuffled = []
    rand = Random(seed)
    deck = NewDeck()
    while deck:
        idx = rand.random() % len(deck)
        card = deck[idx]
        deck[idx] = deck[-1]
        deck.pop()
        shuffled.append(card)
    return shuffled

# Card is created with the MS "card number" 1-52
class Card:
    def __init__(self, number):
        if number < 1 or number > 52:
            raise Exception(f'Card {number} is not in range')

        self.suit = CardSuits[ (number - 1) % 4 ]
        self.rank = CardRanks[ (number - 1) // 4 ]
        self.rank_index = CardRanks.index(self.rank)
        self.glyph = SuitsGlyphs[ (number - 1) % 4 ]
        self.color = 'red' if self.suit in 'DH' else 'black'

    # Can the newcard be on top of us (next lower rank, opposite color) in a cascade?
    def can_cascade(self, newcard):
        return self.color != newcard.color and (self.rank_index - 1) == newcard.rank_index

    # Can the new card be on top of us (next higher rank, same suit) in homes?
    def can_home(self, newcard):
        return self.suit == newcard.suit and (self.rank_index + 1) == newcard.rank_index

    def as_string(self, glyph=True):
        color_sequence = ansi.fg.__dict__[self.color]
        if glyph:
            return f'{color_sequence}{self.rank}{self.glyph} '
        else:
            return f'{color_sequence}{self.rank}{self.suit} '

    def __repr__(self):
        return f'Card: suit={self.suit} ({self.glyph}) rank={self.rank}'
    
# Columns are used to implement:
# 1) A tableau column (max_length None, cascade True)
# 2) A home cell (max_length None, cascade False [an empty cascade will accept any card])
# 3) A free cell (max_length 1, cascade True)

class Column(list):
    def __init__(self, max_length=None, cascade=True, location='unknown'):
        self.max_length = max_length or DECK_SIZE
        self.cascade = cascade
        self.location = location

    def add_card(self, card):
        if not self.can_take_card(card):
            raise Exception(f'Column botch: {card} cannot be added to {self}')
        self.append(card)

    def add_card_from_dealer(self, card):
        self.append(card)

    def __repr__(self):
        return f'Column at location: "{self.location}" max_length={self.max_length} cascade={self.cascade}'
    
    # Find and move the legally correct number of cards from source column
    # to ourselves, removing them from the source column.
    def add_cards_from_column(self, src_column, max_supermove_size):
        card_count = self.get_column_move_size(src_column, max_supermove_size)
        if card_count:
            src_cards = src_column[-card_count:]
            src_column[-card_count:] = []
            for card in src_cards:
                self.add_card(card)

    # Can the given card be legally added to this columm?
    def can_take_card(self, card):
        if self.max_length and len(self) >= self.max_length:
            return False

        if self.cascade:
            if len(self) == 0:
                return True
            return self[-1].can_cascade(card)

        else:
            if len(self) == 0:
                return card.rank == 'A' and card.glyph == self.location
            return self[-1].can_home(card)

    # Find a legal move from the src column into ours and report 
    # the number of cards it involves. Return 0 if there isn't one.
    def get_column_move_size(self, src_column, supermove_room):
        src_run_length = src_column.get_final_run_length()
        max_cards = min(supermove_room, src_run_length, self.max_length)
        # Loop through possible xfers (trying the largest stretch of cards first
        # since moves to an empty column can start from any card in the string).
        for i in range(max_cards, 0, -1):
            card = src_column.get_card_from_top(depth=i-1)
            if self.can_take_card(card):
                return i
        return 0

    # Sugar
    def can_move_cards(self, src_column, supermove_room):
        return self.get_column_move_size(src_column, supermove_room) != 0

    # How many cards in a row does this cascade column end with?
    def get_final_run_length(self):
        card = self.get_card_from_top()
        if not self.cascade or not card:
            return 0

        run_length = 1
        # Start with the second to last card and step backwards
        for prior_card in self[-2::-1]:
            if not prior_card.can_cascade(card):
                break
            run_length += 1
            card = prior_card
        return run_length

    def get_card_from_row(self, row):
        if row < len(self):
            return self[row]

    def get_card_from_top(self, depth=0):
        if len(self) > depth:
            return self[-1-depth]

# A unifying container for the tableau, frees and homes column groups.

class ColumnGroup(list):
    def find_column_for_card(self, card):
        for i in self:
            if i.can_take_card(card):
                return i

    def get_column_for_location(self, location):
        for i in self:
            if i.location == location:
                return i

    def get_row_count(self):
        return max(len(i) for i in self)

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

class BoardSnapshot:
    def __init__(self, board):
        self.frees = copy.deepcopy(board.frees)
        self.tableau = copy.deepcopy(board.tableau)
        self.homes = copy.deepcopy(board.homes)
        self.move_counter = board.move_counter

    def restore(self, board):
        board.frees = self.frees
        board.tableau  = self.tableau
        board.homes = self.homes
        board.move_counter = self.move_counter

class Board:
    def __init__(self, seed):
        self.frees = ColumnGroup(Column(max_length=1, cascade=True, location=i) for i in 'abcd')
        self.tableau = ColumnGroup(Column(cascade=True, location=i) for i in '12345678')
        self.homes = ColumnGroup(Column(cascade=False, location=i) for i in SuitsGlyphs)
        self.move_counter = 0
        self.history = []

        # Go round-robin, placing cards from the shuffled deck in each column of the tableau.
        deck = GetShuffledDeck(seed)
        for i, card in enumerate(deck):
            self.tableau[i % len(self.tableau)].add_card_from_dealer(card)

    def is_empty(self):
        columns_in_use = sum(1 for i in self.frees + self.tableau if i)
        return columns_in_use == 0

    # Find the correct column for the given source location.
    def get_src_column(self, location):
        for group in self.frees, self.tableau:
            column = group.get_column_for_location(location)
            if column is not None:
                return column

    # Find the correct destination column, given a location and card to place there.
    def get_dst_column(self, location, card):
        # Bonus feature: "f" serves to find any available FreeCell slot.
        if location == 'f':
            for i in self.frees:
                if i.can_take_card(card):
                    return i

        if location != 'h':
            return self.get_src_column(location)

        for i in self.homes:
            if i.can_take_card(card):
                return i

    # The public "move" interface that keeps a history and reports errors.
    def move(self, move, save_history=False):
        if save_history:
            self.snapshot()
        success = True
        try:
            self.compound_move(move)

        except MoveException as e:
            print(e)
            success = False
            if save_history:
                self.undo()

        return success

    # This moves cards between locations (tableau, frees, homes), attempting 
    # to move as many valid cards as it can on tableau-to-tableau moves.
    # The "move" parameter is a two character string: <source><destination>
    # where source can be 1-8 (the tableau), a-d (the frees) and destination 
    # can be all the source locations plus h (homes).
    def compound_move(self, move):
        if len(move) != 2:
            raise MoveException(f'Error, move "{move}" is not two characters')

        src, dst = tuple(move)
        src_column = self.get_src_column(src)
        card = src_column and src_column.get_card_from_top()
        if not card:
            raise MoveException(f'No card at {src}')

        max_supermove_size = self.get_max_supermove_size()

        dst_column = self.get_dst_column(dst, card)

        if dst_column is not None \
            and dst_column.can_move_cards(src_column, max_supermove_size):

            dst_column.add_cards_from_column(src_column, max_supermove_size)
            self.move_counter += 1

        else:
            raise MoveException(f'Illegal move {move}')

    # Hunt for cards on top of the tableau columns and in free cells that can
    # be moved home (unless there are other cards on the tableau that could cascade 
    # directly from them). Generate moves to effect these changes.
    def automatic_moves(self):
        while True:
            for src_column in self.tableau + self.frees:
                card = src_column.get_card_from_top()
                if card and not self.is_card_needed(card):
                    home = self.homes.find_column_for_card(card)
                    if home is not None:
                        yield src_column.location + 'h'
                        break
            else:
                # If we exhaust the list without yielding a move, we're done.
                break

    # Is there a card on the board that this card could cascade onto? Meaning
    # that card could become orphaned if it loses this card as a parent.
    def is_card_needed(self, card):
        # We ignore Aces or 2s as possible dependents. Aces will never depend on 
        # another card because they move directly to home.
        if card.rank_index > CardRanks.index("2"):
            for column in self.tableau:
                for board_card in column:
                    if card.can_cascade(board_card):
                        return True

    # From http://EzineArticles.com/104608 -- Allowed Supermove size is:
    # (1 + number of empty freecells) * 2 ^ (number of empty columns)
    def get_max_supermove_size(self):
        empty_frees = sum(1 for i in self.frees if not i)
        empty_columns = sum(1 for i in self.tableau if not i)
        # Must be some error in the formula -- I had to add max of (empty_frees+1) to it.
        return max(empty_frees + 1, int(math.pow((1 + empty_frees) * 2, empty_columns)))

    def snapshot(self):
        self.history.append(BoardSnapshot(self))

    def undo(self):
        if self.history:
            self.history.pop().restore(self)

    def print(self):
        sheet = PrinterSheet()
        for i in self.frees: 
            sheet.printcard(i.get_card_from_top())

        for i in self.homes: 
            sheet.printcard(i.get_card_from_top())
        sheet.print()

        for row in range(self.tableau.get_row_count()):
            for col in self.tableau: 
                sheet.printcard(col.get_card_from_row(row))
            sheet.print()

        # Place the column numbers at the bottom for easy reading.
        sheet.print(ansi.reset, end='')
        for i in range(1,9):
            sheet.print(f'{i}  ', end='')
        sheet.print()

        sheet.output()


import sys

Moves = ["26", "76", "72", "72", "5a", "27", "57", "67", "1b", "61", "41", "4h", "4h", "41", "45", "34", "3c","6d", "5b"]

def main():
    lines = []
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if filename == 'test':
            lines = Moves
        else:
            lines = open(sys.argv[1]).readlines()

    BoardLog = open('cell.log', 'w')

    board = Board(seed=10913)
    board.print()

    while not board.is_empty():

        # Try getting supplied input first
        move = lines and lines.pop(0).strip()
        if move:
            print(f'{ansi.fg.yellow}# {board.move_counter}. supplied-move: {move}{ansi.reset}')

        # If that's exhausted, ask for manual input
        else:
            print(f'{ansi.fg.green}# {board.move_counter}. manual-move: {ansi.reset}', end='')
            move = input()

        if move == 'u':
            board.undo()
            board.print()
            continue

        BoardLog.write(move+'\n')
        valid = board.move(move, save_history=True)
        if not valid: 
            # Skip automated moves after errors since otherwise an error 
            # at move 0 might allow automated moves to happen.
            continue

        board.print()

        for move in board.automatic_moves():
            print(f'{ansi.fg.red}# {board.move_counter}. auto-move: {move}{ansi.reset}')
            board.move(move)
            board.print()
        
if __name__ == '__main__':
    print('Type "./freecell.py test" to run with the builtin test dataset')
    main()