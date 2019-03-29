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
import string

from printers import TTY, PrinterSheet

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

# Card is created with the MS card "number" 1-52
class Card:
    Ranks = 'A23456789TJQK'
    Suits = 'CDHS'
    Glyphs = '♣♦♥♠'

    def __init__(self, number):
        if number < 1 or number > DECK_SIZE:
            raise Exception(f'Card __init__ botch: {number} is not in range')

        number -= 1
        self.suit = Card.Suits[number % 4]
        self.glyph = Card.Glyphs[number % 4]
        self.rank_index = number // 4
        self.rank = Card.Ranks[self.rank_index]
        self.color = 'red' if self.suit in 'DH' else 'black'

    # Can the new_card be on top of us (next lower rank, opposite color) in a tableau?
    # (A tableau can always accept a non-existant card)
    def can_tableau(self, new_card):
        return not new_card or (self.color != new_card.color and self.rank_index - 1 == new_card.rank_index)

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
        # Set our instance properties appropriately based on the column type.
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
    def add_cards_from_column(self, src_column, supermove_room):
        card_count = self.get_column_move_size(src_column, supermove_room)
        if card_count:
            source_cards = src_column.remove_top_cards(card_count)
            for card in source_cards:
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
        return bool( self.get_column_move_size(src_column, supermove_room )

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
    # (Only freecells and cascades have cards removed from them)
    def get_removable_amount(self):
        # Use a slice to pass in a copy of ourselves -- the original is untouched.
        return len(self.remove_tableau(self[:]))

    # Remove all the cards that constitute a tableau and return them.
    def remove_tableau(self, column, top_card=None):
        tableau = []
        if column and column[-1].can_tableau(top_card):
            tableau = self.remove_tableau(column, column.pop())
        if top_card:
            tableau.append(top_card)
        return tableau

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
    
# A ColumnGroup is a unifying container for the 3 distinct groups 
# of columns (the cascades, the freecells and the foundations).
# The constructor takes a list of columns.

class ColumnGroup(list):
    def __init__(self, *args):
        list.__init__(self, *args)

    # Return a column that can accept our card
    def find_column_for_card(self, card):
        for column in self:
            if column.can_accept_card(card):
                return column

    def get_row_count(self):
        return max(len(column) for column in self)

# An exception thrown on illegal user moves
class UserException(Exception): pass

# The Freecell Board 
# Allows standard and non-standard frecell boards to be created and played.
# Ignore_dependencies=True will allow the auto-mover to freely make legal moves to home.

class Board:
    FreeCellNames = 'abcdefgijklmnopqrstuvwxyz' # leaves out "h" (used for home)
    CascadeNames = '123456789' + string.ascii_uppercase

    def __init__(self, seed, printer=TTY(), freecells=4, cascades=8, ignore_dependencies=False):
        if cascades < 1 or cascades > len(Board.CascadeNames) or \
            freecells < 0 or freecells > len(Board.FreeCellNames):
            raise Exception('Board initialization error')
            
        # Use the card glyphs for the foundation cells' real location names.
        self.homes = ColumnGroup(Column(type='HOME', location=i) for i in Card.Glyphs)
        self.frees = ColumnGroup(Column(type='FREECELL', location=i) for i in Board.FreeCellNames[:freecells])
        self.cascades = ColumnGroup(Column(type='CASCADE', location=i) for i in Board.CascadeNames[:cascades])
        self.make_column_maps()        

        self.move_counter = 0
        self.history = []
        self.printer = printer
        self.ignore_dependencies = ignore_dependencies

        # Go round-robin, placing cards from the shuffled deck in each column of the cascades.
        deck = GetShuffledDeck(seed)
        for i, card in enumerate(deck):
            self.cascades[i % len(self.cascades)].add_card_from_dealer(card)

    def make_column_maps(self):
        self.src_column_map = {i.location: i for i in self.cascades + self.frees}
        self.dst_column_map = {i.location: i for i in self.cascades + self.frees + self.homes}

    def is_empty(self):
        columns_in_use = sum(1 for i in self.frees + self.cascades if i)
        return columns_in_use == 0

    # Find the correct source column given a location.
    def get_src_column(self, location):
        return self.src_column_map.get(location)
        
    # Find the correct destination column, given a location and card to place there.
    def get_dst_column(self, location, card):
        if location == 'h':
            location = card.glyph
        return self.dst_column_map.get(location)

    # This moves cards between locations (cascades, frees, homes), attempting 
    # to move as many valid cards as it can on cascade-to-cascade moves.
    # The "move" parameter is a two character string: <source><destination>
    # where <source> can be 1-8 (the cascades), a-d (the frees) and <destination>
    # can be all the source locations plus h (homes).
    # Tis raises a UserException if the move is illegal in any way.
    
    def compound_move(self, move):
        if len(move) != 2:
            raise UserException(f'Error, move "{move}" is not two characters')

        src, dst = move

        src_column = self.get_src_column(src)
        if src_column is None:
            raise UserException(f'Illegal move {move}')

        card = src_column.peek_card_from_top()
        if not card:
            raise UserException(f'No card at {src}')

        dst_column = self.get_dst_column(dst, card)
        if dst_column is None:
            raise UserException(f'Illegal move {move}')

        supermove_room = self.get_supermove_room()
        if not dst_column.can_accept_column(src_column, supermove_room):
            raise UserException(f'Illegal move {move}')
    
        dst_column.add_cards_from_column(src_column, supermove_room)

        self.move_counter += 1

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

            # After we've scanned all the columns without yielding a move, we're done.
            else:
                break

    # Is there a card on the board that this card could cascade onto? (Meaning that 
    # the card could become orphaned if it loses this card as its tableau parent)
    def is_card_needed(self, card):
        # We ignore Aces or 2s as possible dependents. Aces will never depend on 
        # 2s because they move directly to home. Someone told me we can also ignore 2s.
        if card.rank_index > Card.Ranks.index("2") and not self.ignore_dependencies:
            for column in self.cascades + self.frees:
                for board_card in column:
                    if card.can_tableau(board_card):
                        return True

    # From http://EzineArticles.com/104608 -- Allowed Supermove size is:
    # (1 + number of empty freecells) * 2 ^ (number of empty columns)
    def get_supermove_room(self):
        empty_frees = sum(1 for i in self.frees if not i)
        empty_columns = sum(1 for i in self.cascades if not i)
        # Must be some error in the formula -- I had to add max of (empty_frees+1) to it.
        return max(empty_frees + 1, int(math.pow((1 + empty_frees) * 2, empty_columns)))

    def snapshot(self):
        self.history.append(self.get_state())

    def undo(self):
        if self.history:
            self.restore_state(self.history.pop())

    def get_state(self):
        return copy.deepcopy(dict(frees=self.frees, 
                                  homes=self.homes, 
                                  cascades=self.cascades, 
                                  move_counter=self.move_counter))

    def restore_state(self, state):
        self.frees = state['frees']
        self.homes = state['homes']
        self.cascades = state['cascades']
        self.move_counter = state['move_counter']
        self.make_column_maps()

    def print(self):
        sheet = PrinterSheet()

        # Print the top guide (frees and homes locations)
        for i in self.frees + self.homes:
            sheet.print(f'{i.location}  ', end='')
        sheet.print()

        # Print Frees and Homes
        for i in self.frees + self.homes:
            sheet.printcard(i.peek_card_from_top())
        sheet.print()

        # Print the Cascade
        for row in range(self.cascades.get_row_count()):
            for col in self.cascades: 
                sheet.printcard(col.peek_card_from_row(row))
            sheet.print()
        sheet.print(ansi.reset, end='')

        # Place the bottom guide (the cascade numbers)
        for i in self.cascades:
            sheet.print(f'{i.location}  ', end='')
        sheet.print()

        self.printer.print_sheet(sheet)