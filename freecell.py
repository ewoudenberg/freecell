#!/usr/bin/env python

# Original © Copyright 2019 Lawrence E. Bakst All Rights Reserved
# Mods by E. Woudenberg
# The code here generates MS compatible Freecell deals and plays back solutions.

import random
import ansi
import math

CardRanks = 'A23456789TJQK'
CardSuits = 'CDHS'
SuitsGlyphs = '♣♦♥♠'
DECK_SIZE = 52

class MoveException(Exception):
    pass

# Create a deck of cards
def NewDeck(n=DECK_SIZE):
    return list(range(1, n+1))

# This is supposedly an MS compiler runtime compatible version of rand
# first 5 numbers with seed of 1 are 41, 18467, 6334, 26500, 19169
state = 1
def srand(seed):
    global state
    state = seed

def rand():
    global state
    state = ((214013 * state) + 2531011) % 2147483648 # mod 2^31
    return  state // 65536

def GetShuffledDeck(seed):
    shuffled = []
    srand(seed)
    deck = NewDeck()
    while deck:
        idx = rand() % len(deck)
        card = deck[idx]
        deck[idx] = deck[-1]
        deck.pop()
        shuffled.append(Card(number=card))
    return shuffled

def printcard(card):
    chars = ansi.bg.green
    if card:
        chars += card.as_string()
    else:
        chars += '   '
    chars += ansi.bg.black
    print(chars, end='')

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
    
# A Column implements:
# 1) A cascade (max_length None, cascade True)
# 2) A home (max_length None, cascade False)
# 3) A free cell (max_length 1, cascade False)

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
        max_cards = min(supermove_room, src_column.get_final_run_length(), self.max_length)
        # Loop through possible xfers, trying the largest stretch of cards first.
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

# Bundle up the columns in a dictionary, indexed by their name
# e.g. "a" through "d", "1" through "8"
class ColumnGroup(dict):
    def find_column_for_card(self, card):
        for i in self.values():
            if i.can_take_card(card):
                return i

    def get_row_count(self):
        longest = 0
        for i in self.values():
            longest = max(longest, len(i))
        return longest

class Board:
    def __init__(self):
        self.frees = ColumnGroup({i: Column(max_length=1, cascade=True, location=i) for i in 'abcd'})
        self.tableau = ColumnGroup({i: Column(cascade=True, location=i) for i in '12345678'})
        self.homes = ColumnGroup({i: Column(cascade=False, location=i) for i in SuitsGlyphs})

    # Go round-robin, placing cards from the shuffled deck in each column of the tableau.
    def setup(self, seed):
        deck = GetShuffledDeck(seed)
        tableau = list(self.tableau.values())
        tableau_size = len(tableau)
        for i, card in enumerate(deck):
            tableau[i % tableau_size].add_card_from_dealer(card)

    def print(self):
        for i in self.frees.values(): 
            printcard(i.get_card_from_top())

        for i in self.homes.values(): 
            printcard(i.get_card_from_top())
        print()

        for row in range(self.tableau.get_row_count()):
            for col in self.tableau.values(): 
                printcard(col.get_card_from_row(row))
            print()

        # Place the column numbers at the bottom for easy reading.
        print(ansi.reset, end='')
        for i in range(1,9):
            print(f'{i}  ', end='')

        print()

    def is_empty(self):
        in_use_frees = len([i for i in self.frees.values() if i])
        in_use_columns = len([i for i in self.tableau.values() if i])
        return in_use_frees + in_use_columns == 0

    # Find the correct column for the given source location.
    def get_src_column(self, location):
        for group in self.frees, self.tableau:
            if location in group:
                return group[location]

    # Find the correct destination column, given a location and card to place there.
    def get_dst_column(self, location, card):
        # Bonus feature: "f" serves to find any available FreeCell slot.
        if location == 'f':
            for i in self.frees.values():
                if i.can_take_card(card):
                    return i

        if location != 'h':
            return self.get_src_column(location)

        for i in self.homes.values():
            if i.can_take_card(card):
                return i

    # From http://EzineArticles.com/104608 -- Allowed Supermove size is:
    # (1 + number of empty freecells) * 2 ^ (number of empty columns)
    def get_max_supermove_size(self):
        empty_frees = len([i for i in self.frees.values() if not i])
        empty_columns = len([i for i in self.tableau.values() if not i])
        # Must be some error in the formula -- I had to take max of empty_frees here
        return max(empty_frees + 1, int(math.pow((1 + empty_frees) * 2, empty_columns)))

    # The "move" parameter is a two character string: <source><destination>
    # where source or destination can be 1-8 (the tableau), a-d (the frees) or h (homes).
    # This attempts to move as many valid cards as it can on a tableau-to-tableau move
    def compound_move(self, move):
        src, dst = tuple(move)
        src_column = self.get_src_column(src)
        card = src_column and src_column.get_card_from_top()
        if not card:
            raise MoveException(f'No card at {move}')

        max_supermove_size = self.get_max_supermove_size()

        dst_column = self.get_dst_column(dst, card)

        if dst_column is not None \
            and dst_column.can_move_cards(src_column, max_supermove_size):

            dst_column.add_cards_from_column(src_column, max_supermove_size)

        else:
            raise MoveException(f'Illegal move {move}')

    # Is there are card on the board that this card could cascade onto?
    def is_card_needed(self, card):
        # (We don't have to worry about a "2" since Aces [what a "2" would 
        # cascade onto] can always move off the board to home.)
        if card.rank_index > 1:
            for column in self.tableau.values():
                for board_card in column:
                    if card.can_cascade(board_card):
                        return True

    # Hunt for cards on top of the tableau columns and in free cells that can
    # be moved home (unless there are other cards on the tableau that could cascade 
    # directly from them). Generate moves to effect these changes.
    def automatic_moves(self):
        while True:
            for location, src_column in list(self.tableau.items()) + list(self.frees.items()):
                card = src_column.get_card_from_top()
                if card and not self.is_card_needed(card):
                    dst_column = self.homes.find_column_for_card(card)
                    if dst_column is not None:
                        yield f'{location}h'
                        break
            else:
                # If we exhaust the list without yielding a move, we're done.
                break

import sys

def do_move(board, move):
    try:
        board.compound_move(move)
    except MoveException as e:
        print(f'{e}')

Moves = ["26", "76", "72", "72", "5a", "27", "57", "67", "1b", "61", "41", "4h", "4h", "41", "45", "34", "3c","6d", "5b"]

def main():
    board = Board()
    board.setup(seed=10913)
    lines = []
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if filename == 'test':
            lines = Moves
        else:
            lines = open(sys.argv[1]).readlines()

    BoardLog = open('cell.log', 'w')
    board.print()

    while not board.is_empty():
        move = lines and lines.pop(0).strip() or input()
        if len(move) > 2:
            print(f'Bad Move: {move}')
            continue
        print(f'{ansi.fg.green}manual-move: {move}{ansi.reset}')
        BoardLog.write(move+'\n')
        do_move(board, move)
        board.print()

        for move in board.automatic_moves():
            print(f'{ansi.fg.red}auto-move: {move}{ansi.reset}')
            do_move(board, move)
            board.print()
        

if __name__ == '__main__':
    print('Type ./freecell.py test to run with the builtin test dataset')
    main()