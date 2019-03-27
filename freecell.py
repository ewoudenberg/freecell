#!/usr/bin/env python

# This generates MS compatible Freecell deals and plays back solutions.

# CC BY-SA 2019 E. Woudenberg (prompted by interest from Lawrence E. Bakst)

'''
(Freecell Game Details from Wikipedia)

Construction and layout

- One standard 52-card deck is used.
- There are four open cells and four open foundations. Some alternate rules use between one and ten cells.
- Cards are dealt face-up into eight cascades, four of which comprise seven cards each and four of which 
  comprise six cards each. Some alternate rules will use between four and ten cascades.

Building during play

- The top card of each cascade begins a tableau.
- Tableaux must be built down by alternating colors.
- Foundations are built up by suit.

Moves

- Any cell card or top card of any cascade may be moved to build on a tableau, or moved to an empty cell, 
  an empty cascade, or its foundation.
- Complete or partial tableaus may be moved to build on existing tableaus, or moved to empty cascades, by 
  recursively placing and removing cards through intermediate locations. Computer implementations often show 
  this motion, but players using physical decks typically move the tableau at once.
'''

import random
import ansi
import math
import copy
import sys

from printers import TTY, LinePrinter, PrinterSheet

# Create a deck of cards

DECK_SIZE = 52

def NewDeck(n=DECK_SIZE):
    return [Card(i) for i in range(1, n+1)]

def GetShuffledDeck(seed):
    deck = NewDeck()
    rand = Random(seed)
    while deck:
        idx = rand.random() % len(deck)
        yield deck[idx]
        deck[idx] = deck[-1]
        deck.pop()

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

CardRanks = 'A23456789TJQK'
CardSuits = 'CDHS'
CardGlyphs = '♣♦♥♠'

# Card is created with the MS card "number" 1-52
class Card:
    def __init__(self, number):
        if number < 1 or number > DECK_SIZE:
            raise Exception(f'Card __init__ botch: {number} is not in range')

        number -= 1
        self.suit = CardSuits[number % 4]
        self.glyph = CardGlyphs[number % 4]
        self.rank_index = number // 4
        self.rank = CardRanks[self.rank_index]
        self.color = 'red' if self.suit in 'DH' else 'black'

    # Can the new_card be on top of us (next lower rank, opposite color) in a tableau?
    def can_tableau(self, new_card):
        return self.color != new_card.color and self.rank_index - 1 == new_card.rank_index

    # Can the new card be on top of us (next higher rank, same suit) in homes?
    def can_home(self, new_card):
        return self.suit == new_card.suit and self.rank_index + 1 == new_card.rank_index

    def as_string(self, glyph=True):
        color_sequence = ansi.fg.__dict__[self.color]
        if glyph:
            return f'{color_sequence}{self.rank}{self.glyph} '
        else:
            return f'{color_sequence}{self.rank}{self.suit} '

    def __repr__(self): # for debugging
        return f'Card: suit={self.suit} ({self.glyph}) rank={self.rank}'
    
Infinite = float('Inf')

# Columns are used to implement the free cells, suit foundations ("homes"), and cascades.

class Column(list):
    def __init__(self, type=None, location=''):
        type_configurations = dict(FREECELL=dict(cascade=True, max_length=1),
                                   HOME=dict(cascade=False, max_length=Infinite),
                                   CASCADE=dict(cascade=True, max_length=Infinite))

        if type not in type_configurations:
            raise Exception(f'Column __init__ botch: unknown type "{type}"')
                        
        self.location = location
        self.type = type
        self.__dict__.update(type_configurations[type])

    def add_card(self, card):
        if not self.can_accept_card(card):
            # We should never get here
            raise Exception(f'Column.add_card botch: {card} cannot be added to {self}')
        self.append(card)

    def add_card_from_dealer(self, card):
        self.append(card)

    # Find and move the legally correct number of cards from the source column
    # to ourselves, removing them from the source column.
    def add_cards_from_column(self, src_column, max_supermove_size):
        card_count = self.get_column_move_size(src_column, max_supermove_size)
        if card_count:
            for card in src_column.remove_top_cards(card_count):
                self.add_card(card)

    # Can the given card be legally added to this columm?
    def can_accept_card(self, new_card):
        if len(self) >= self.max_length:
            return False

        top_card = self.peek_card_from_top()

        if self.cascade:
            if not top_card:
                return True
            return top_card.can_tableau(new_card)

        else:
            if not top_card:
                return new_card.rank == 'A' and new_card.glyph == self.location
            return top_card.can_home(new_card)

    # Can some cards from the given column be added to this column, given the amount
    # of supermove room?
    def can_accept_column(self, src_column, supermove_room):
        return self.get_column_move_size(src_column, supermove_room) != 0

    # Find a legal move from the src column into ours and report 
    # the number of cards it involves. Return 0 if there isn't one.
    def get_column_move_size(self, src_column, supermove_room):
        src_removable_cards = src_column.get_removable_amount()
        max_cards = min(supermove_room, src_removable_cards, self.max_length-len(self))
        # Loop through possible xfers (trying the largest stretch of cards first
        # since moves to an empty column can start from any card in the string).
        for i in range(max_cards, 0, -1):
            card = src_column.peek_card_from_top(depth=i-1)
            if self.can_accept_card(card):
                return i
        return 0

    # How many cards in a row could we remove from this column?
    def get_removable_amount(self):
        run_length = 0
        top_card = self.peek_card_from_top()
        if top_card:
            run_length += 1
            # From how deep do the cards cascade?
            while True:
                deeper_card = self.peek_card_from_top(run_length)
                if not deeper_card or not deeper_card.can_tableau(top_card):
                    break
                top_card = deeper_card
                run_length += 1
        return run_length

    def peek_card_from_row(self, row):
        if row < len(self):
            return self[row]

    def peek_card_from_top(self, depth=0):
        if depth < len(self):
            return self[-1-depth]

    def remove_top_cards(self, card_count):
        cards = self[-card_count:]
        self[-card_count:] = []
        return cards

    def __repr__(self):
        return f'{self.type}({self.location}), length={len(self)} top={self.peek_card_from_top()}'
    
# A ColumnGroup is a unifying container for the 3 groups 
# of columns (the cascades, the freecells and the homes).
# The constructor takes a list of columns.

class ColumnGroup(list):
    def __init__(self, *args):
        list.__init__(self, *args)
        self.column_lookup_table = {i.location: i for i in self}

    def find_column_for_card(self, card):
        for column in self:
            if column.can_accept_card(card):
                return column

    def get_column_for_location(self, location):
        return self.column_lookup_table.get(location)

    def get_row_count(self):
        return max(len(column) for column in self)



class BoardSnapshot:
    def __init__(self, board):
        self.frees = copy.deepcopy(board.frees)
        self.cascades = copy.deepcopy(board.cascades)
        self.homes = copy.deepcopy(board.homes)
        self.move_counter = board.move_counter

    def restore(self, board):
        board.frees = self.frees
        board.cascades  = self.cascades
        board.homes = self.homes
        board.move_counter = self.move_counter

# An exception thrown on illegal user moves
class UserException(Exception): pass

FreeCellNames = 'abcd'
CascadeNames = '12345678'

class Board:
    def __init__(self, seed, printer=TTY()
    ):
        self.homes = ColumnGroup(Column(type='HOME', location=i) for i in CardGlyphs)
        self.frees = ColumnGroup(Column(type='FREECELL', location=i) for i in FreeCellNames)
        self.cascades = ColumnGroup(Column(type='CASCADE', location=i) for i in CascadeNames)
        self.move_counter = 0
        self.history = []
        self.printer = printer

        # Go round-robin, placing cards from the shuffled deck in each column of the cascades.
        deck = GetShuffledDeck(seed)
        for i, card in enumerate(deck):
            self.cascades[i % len(self.cascades)].add_card_from_dealer(card)

    def is_empty(self):
        columns_in_use = sum(1 for i in self.frees + self.cascades if i)
        return columns_in_use == 0

    # Find the correct column for the given source location.
    def get_src_column(self, location):
        for group in self.frees, self.cascades:
            column = group.get_column_for_location(location)
            if column is not None:
                return column

    # Find the correct destination column, given a location and card to place there.
    def get_dst_column(self, location, card):
        # Bonus feature: "f" serves to find any available FreeCell slot.
        if location == 'f':
            for i in self.frees:
                if i.can_accept_card(card):
                    return i

        if location != 'h':
            return self.get_src_column(location)

        for i in self.homes:
            if i.can_accept_card(card):
                return i

    # The public "move" interface that keeps a history and reports errors.
    def move(self, move, save_history=False):
        if save_history:
            self.snapshot()

        success = True
        try:
            self.compound_move(move)

        except UserException as e:
            print(e)
            success = False
            if save_history:
                self.undo()

        return success

    # This moves cards between locations (cascades, frees, homes), attempting 
    # to move as many valid cards as it can on cascade-to-cascade moves.
    # The "move" parameter is a two character string: <source><destination>
    # where <source> can be 1-8 (the cascades), a-d (the frees) and <destination>
    # can be all the source locations plus h (homes).
    def compound_move(self, move):
        if len(move) != 2:
            raise UserException(f'Error, move "{move}" is not two characters')

        src, dst = move
        src_column = self.get_src_column(src)
        card = src_column and src_column.peek_card_from_top()
        if not card:
            raise UserException(f'No card at {src}')

        dst_column = self.get_dst_column(dst, card)
        max_supermove_size = self.get_max_supermove_size()
        
        if dst_column is None \
            or not dst_column.can_accept_column(src_column, max_supermove_size):
            raise UserException(f'Illegal move {move}')
    
        dst_column.add_cards_from_column(src_column, max_supermove_size)
        self.move_counter += 1

    # Hunt for cards on top of the cascades columns and in free cells that can
    # be moved home (unless there are other cards on the cascades that could cascade 
    # directly from them). Generate moves to effect these changes.
    def automatic_moves(self):
        while True:
            for src_column in self.cascades + self.frees:
                card = src_column.peek_card_from_top()
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
        # 2s because they move directly to home. Someone told me we can also ignore 2s.
        if card.rank_index > CardRanks.index("2"):
            for column in self.cascades + self.frees:
                for board_card in column:
                    if card.can_tableau(board_card):
                        return True

    # From http://EzineArticles.com/104608 -- Allowed Supermove size is:
    # (1 + number of empty freecells) * 2 ^ (number of empty columns)
    def get_max_supermove_size(self):
        empty_frees = sum(1 for i in self.frees if not i)
        empty_columns = sum(1 for i in self.cascades if not i)
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
            sheet.printcard(i.peek_card_from_top())

        for i in self.homes: 
            sheet.printcard(i.peek_card_from_top())
        sheet.print()

        for row in range(self.cascades.get_row_count()):
            for col in self.cascades: 
                sheet.printcard(col.peek_card_from_row(row))
            sheet.print()

        # Place the column numbers at the bottom for easy reading.
        sheet.print(ansi.reset, end='')
        for i in range(1,9):
            sheet.print(f'{i}  ', end='')
        sheet.print()

        self.printer.print_sheet(sheet)

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

    printer = LinePrinter()
    board = Board(seed=10913, printer=printer)
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