#!/usr/bin/env python

# This generates MS compatible Freecell deals and plays back solutions.

# CC BY-SA 2019 E. Woudenberg (prompted by work from Lawrence E. Bakst)

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

import copy
import random
import string

import ansi
from printers import TTY, PrinterSheet

# An exception thrown on illegal user moves
class UserException(Exception): pass

# An exception thrown when the game engine has an internal error
class GameException(Exception): pass

# Create a deck of cards

DECK_SIZE = 52

def NewDeck(n=DECK_SIZE):
    return [Card(i) for i in range(n)]

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

# Card is created with a card "number" 0-51

class Card:
    Ranks = 'A23456789TJQK'
    Suits = 'CDHS'
    Glyphs = '♣♦♥♠'

    def __init__(self, number):
        if number < 0 or number >= DECK_SIZE:
            raise GameException(f'Card __init__ botch: {number} is not in range')

        self.suit = Card.Suits[number % 4]
        self.glyph = Card.Glyphs[number % 4]
        self.rank_index = number // 4
        self.rank = Card.Ranks[self.rank_index]
        self.color = 'red' if self.suit in 'DH' else 'black'

    # Can the new_card be on top of us (next lower rank, opposite color) in a tableau?
    def can_tableau(self, new_card):
        return self.color != new_card.color and self.rank_index - 1 == new_card.rank_index

    # Can the new card be on top of us (next higher rank, same suit) in homes?
    def can_home(self, new_card):
        return self.suit == new_card.suit and self.rank_index + 1 == new_card.rank_index

    def as_string(self, glyph=True):
        color_sequence = ansi.fg.__dict__[self.color]
        return f'{color_sequence}{self.rank}{self.glyph if glyph else self.suit} '

    def __repr__(self): # for debugging
        return f'Card: suit={self.suit} ({self.glyph}) rank={self.rank}'
    
Infinite = float('Inf')

# Columns are used to implement the free cells, suit foundations ("homes"), and cascades.

class Column(list):
    def __init__(self, type=None, location=''):
        type_configurations = dict(FREECELL=dict(cascade=True, max_length=1),
                                   HOME=dict(cascade=False, max_length=Infinite, as_a_move_location='h'),
                                   CASCADE=dict(cascade=True, max_length=Infinite))

        if type not in type_configurations:
            raise GameException(f'Column.__init__ botch: unknown type "{type}"')
                        
        self.location = self.as_a_move_location = location
        self.type = type

        # Set our instance properties appropriately based on the column type.
        self.__dict__.update(type_configurations[type])

    def add_card(self, card):
        if not self.can_accept_card(card):
            raise GameException(f'Column.add_card botch: {card} cannot be added to {self}')
        self.append(card)

    def add_card_from_dealer(self, card):
        self.append(card)

    def get_remaining_room(self):
        return self.max_length - len(self)

    # Remove cards from the source column and add them to ourself.
    def add_cards_from_column(self, src_column, card_count):
        source_cards = src_column.remove_top_cards(card_count)
        for card in source_cards:
            self.add_card(card)

    # Can the given card be legally added to this columm?
    def can_accept_card(self, new_card):
        if self.get_remaining_room() == 0:
            return False

        top_card = self.peek_card_on_top()

        if self.cascade:
            if not top_card:
                return True
            return top_card.can_tableau(new_card)

        else:
            if not top_card:
                return new_card.rank == 'A' and new_card.glyph == self.location
            return top_card.can_home(new_card)

    # Can some cards from the given column be added to this column, given the amount
    # of movement room?
    def can_accept_column(self, src_column, movement_room):
        return self.get_column_move_size(src_column, movement_room) != 0

    # Find a legal move from the src column into ours and report
    # the number of cards it involves. Return 0 if there isn't one.
    def get_column_move_size(self, src_column, movement_room):
        src_cards = src_column.peek_movable_cards()
        src_length = len(src_cards)
        max_length = min(src_length, movement_room, self.get_remaining_room())

        # Scan the source cards for a card we can accept, starting with 
        # the largest stretch of cards first since moves to an empty column 
        # can start from any card in the tableau.
        for run_length in range(max_length, 0, -1):
            if self.can_accept_card(src_cards[-run_length]):
                return run_length
        return 0

    # Get a list of all the cards that could be removed from the top of a column.
    def peek_movable_cards(self):
        tableau = Column(type='CASCADE')
        # Examine each card of the column in bottom-to-top order:
        for card in self:
            if not tableau.can_accept_card(card):
                tableau.clear()
            tableau.add_card(card)
        return tableau

    def peek_card_in_row(self, row):
        if row < len(self):
            return self[row]

    def peek_card_on_top(self):
        if len(self):
            return self[-1]

    def remove_top_cards(self, card_count):
        if card_count < 1:
            GameException('Column.remove_top_cards botch: card_count < 1')
        cards = self[-card_count:]
        self[-card_count:] = []
        return cards

    def __repr__(self):
        return f'{self.type}({self.location}), length={len(self)} top={self.peek_card_on_top()}'
    
# A ColumnGroup is a unifying container for columns. There are 3 of 
# them: one each for the cascades, the freecells and the foundations.
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

# The Freecell Board, it allows standard and non-standard freecell 
# boards to be created and played. Setting Ignore_dependencies=True
# will allow the auto-mover to freely make any legal moves to home.

class Board:
    FreeCellNames = 'abcdefgijklmnopqrstuvwxyz' # leaves out "h" (used for home)
    CascadeNames = '123456789' + string.ascii_uppercase

    def __init__(self, seed, printer=TTY(), freecells=4, cascades=8, ignore_dependencies=False):
        if cascades < 1 or cascades > len(Board.CascadeNames) or \
            freecells < 0 or freecells > len(Board.FreeCellNames):
            raise GameException('Board initialization error')
            
        # Use the card glyphs for the foundation columns' real location names.
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
        self.src_columns = {i.location: i for i in self.cascades + self.frees}
        self.dst_columns = {i.location: i for i in self.cascades + self.frees + self.homes}

    def is_empty(self):
        columns_in_use = sum(1 for i in self.frees + self.cascades if i)
        return columns_in_use == 0

    # Find the correct source column given a location.
    def get_src_column(self, location):
        return self.src_columns.get(location)
        
    # Find the correct destination column, given a location and card to place there.
    # Special feature -- '#' as a destination finds the first available freecell.
    def get_dst_column(self, location, card):
        if location == '#':
            return self.frees.find_column_for_card(card)
        # Translate the "home" move location into its real column location
        if location == 'h':
            location = card.glyph
        return self.dst_columns.get(location)

    # This moves cards between locations (cascades, frees, homes), attempting 
    # to move as many valid cards as it can on cascade-to-cascade moves.
    # The "move" parameter is a two character string: <source><destination>
    # where <source> can be 1-35 (the cascades), a-gi-z (the frees) 
    # and <destination> can be all the source locations plus h (homes).
    # This raises a UserException if the move is illegal in any way.
    
    def internal_move(self, move):
        if len(move) != 2:
            raise UserException(f'Error, move "{move}" is not two characters')

        src, dst = move

        src_column = self.get_src_column(src)
        if src_column is None:
            raise UserException(f'No such source {src}')

        card = src_column.peek_card_on_top()
        if not card:
            raise UserException(f'No card at {src}')

        dst_column = self.get_dst_column(dst, card)
        if dst_column is None:
            raise UserException(f'No such destination {dst}')

        movement_room = self.get_movement_room(dst_column)
        movable_cards = dst_column.get_column_move_size(src_column, movement_room)

        if movable_cards == 0:
            raise UserException(f'Illegal move {move}')
    
        dst_column.add_cards_from_column(src_column, movable_cards)

        self.move_counter += 1

    # The public "move" interface that keeps a history and reports errors.
    def move(self, move, save_history=False):
        if save_history:
            self.snapshot()

        success = True
        try:
            self.internal_move(move)

        except UserException as e:
            print(e)
            success = False
            if save_history:
                self.undo()

        return success

    # Hunt for cards on top of the cascades and in free cells that can
    # be moved home, avoiding ones that may still be depended upon.
    # Generate moves to effect these changes.
    def automatic_moves(self):
        while True:
            for src_column in self.src_columns.values():
                card = src_column.peek_card_on_top()
                if card and self.card_is_safe_to_move(card):
                    dst_column = self.homes.find_column_for_card(card)
                    if dst_column is not None:
                        yield src_column.as_a_move_location + dst_column.as_a_move_location
                        break
            
            else: # After we've scanned all the columns without yielding a move, we're done.
                break

    # Return all the moves currently allowed on the board.
    def get_possible_moves(self):
        for src_column in self.src_columns.values():
            for dst_column in self.dst_columns.values():
                movement_room = self.get_movement_room(dst_column)
                if dst_column.can_accept_column(src_column, movement_room):
                    yield src_column.as_a_move_location + dst_column.as_a_move_location

    # Is there no card on the board that could follow this card in a tableau?
    # (Such a card could become orphaned if it loses this card as its tableau base)
    def card_is_safe_to_move(self, card):
        # We ignore Aces or 2s as possible dependents. Aces will never depend on 
        # 2s because they move directly to home. Someone told me we can also ignore 2s.
        if card.rank_index > Card.Ranks.index("2") and not self.ignore_dependencies:
            for column in self.src_columns.values():
                for board_card in column:
                    if card.can_tableau(board_card):
                        return False
        return True

    # The number of cards that can be moved at one time is given by:
    # (1 + number of empty freecells) * 2 ^ (number of empty columns)
    # (The destination column is excluded from the empty column count)
    def get_movement_room(self, dst_column):
        empty_frees = sum(1 for i in self.frees if not i)
        empty_columns = sum(1 for i in self.cascades if not i and i.location != dst_column.location)
        return (1 + empty_frees) * 2**empty_columns

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

        # Print Frees and Homes
        for i in self.frees + self.homes:
            sheet.printcard(i.peek_card_on_top())
        sheet.print()

        # Print the top guide (frees and homes locations)
        sheet.print(ansi.reset, end='')
        for i in self.frees + self.homes:
            sheet.print(f'{i.location}  ', end='')
        sheet.print()

        # Print the Cascade
        for row in range(self.cascades.get_row_count()):
            for col in self.cascades: 
                sheet.printcard(col.peek_card_in_row(row))
            sheet.print()
        sheet.print(ansi.reset, end='')

        # Place the bottom guide (the cascade numbers)
        for i in self.cascades:
            sheet.print(f'{i.location}  ', end='')
        sheet.print()

        self.printer.print_sheet(sheet)
