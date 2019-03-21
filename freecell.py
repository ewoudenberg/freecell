# © Copyright 2019 Lawrence E. Bakst All Rights Reserved
# The code here generates MS compatible Freecell deals and plays back solutions.
# Soon to generate and evaluate moves to find solutions.

import random
import ansi

# cards are numbered 1-52, so zero is an error.
# My preferece would be that cards are in suit order so 1-13 are Ace of Hearts thru King of Hearts.
# However, MS uses card order so I decided to go with that to avoid a mapping layer.
# if a card is negative it's facedown, not used for Freecell but needed for Klondike.

#new system
CardRanks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K"]
MSSuitNames = ["C", "D", "H", "S"]
MSSuitGlyphs = ["♣", "♦", "♥", "♠"]
REDS = 'DH'
rankmap = [0, 1, 2, 3]
DECK_SIZE = 52

class MoveException(Exception):
    pass

# old system
#RankNames = ["Heart", "Diamond", "Spade", "Club"]
#ShortRankNames = ["H", "D", "S", "C"]
#Colors = ["Red", "Red", "Black", "Black"]

# Create a deck of cards
def NewDeck(n=DECK_SIZE):
    return list(range(1, n+1))

# Return the rank of a card given its MS number
def rank(card):
    return CardRanks[ (card - 1) // 4 ]

# Return the suit of a card given its MS number
def suit(card):
    return MSSuitNames[ (card - 1) % 4 ]

def glyph(card):
    return MSSuitGlyphs[ (card - 1) % 4 ]

# true if red
def color(card):
    return suit(card) in REDS

def MSRedCard(card):
    card -= 1
    suit = card % 4
    if suit == 1 or suit == 2:
        return True
    return False

def MSCardName(card, glyph=True):
    card -= 1
    suit = card % 4
    val = card // 4
    if glyph:
        return CardRanks[val] + MSSuitGlyphs[suit]
    else:
        return CardRanks[val] + MSSuitNames[suit]


# MS suit ordering is club, diamond, heart, spade
# I don't think they knew that suits have an order
def convertToMS(card):
    card -= 1
    offset = [39, 13, 0, 26]
    suit = card % 4
    val = card // 4
    return offset[suit] + val + 1

#print an ANSI sequence that sets the card color
def CardColor(card):
    if MSRedCard(card):
        print(ansi.fg.red, end='')
    else:
        print(ansi.fg.black, end='')

# Returns a tuple(colum, index, home) that describes the from or to of a move
def GetCIH(l):
    col = -1
    idx = -1
    home = False
    if l >= "1" and l <= "8":
        col = int(l)
    elif l >= "a" and l <= "d":
        col = 0
        idx = ord(l) - 97 + 4
    elif l == "h":
        home = True
    return (col, idx, home)

# Suposedly MS compiler runtime compatible version of rand
# first 5 numbers with seed of 1 are 41, 18467, 6334, 26500, 19169
state = 1
def srand(seed):
    global state
    state = seed

def rand():
    global state
    state = ((214013 * state) + 2531011) % 2147483648 # mod 2^31
    return  state // 65536
















# code to implement a FreeCellGame
class FreeCellGame:
    def __init__(self):
        self.cols = 9
        self.rows = 21
        self.freecells = 4
        self.freetabs = 0

# Generate a new Freecell game and set up the board, game 5 is easy so it's the default
# Conceptuall board is 8 columns x as many rows are needed, a maxiumum of 21 (13+8) I believe.
# In fact the board here is 9 columns because the top row is implemented as column 0.
# The top row contains the 4 foundations in rows 0-4, and the 4 freecells in rows 4-8.
# In each of the 8 rows of column 0 there is a list where cards are placed ussing append().
# All the other columns, which are the cascaeds, have just a single list where we do pop() and append.
    def NewGame(self, game=5):
        self.Board = [[-1 for j in range(self.rows)] for i in range(self.cols)]
        self.Board[0] = [[] for i in range(8)]
        #print(self.Board) 
        deck = NewDeck()
        # Shuffle(deck)
        left = 52
        #print(game)
        srand(game)
        for i in range(52):
            idx = rand() % left
            card = deck[idx]
            left -= 1
            deck[idx] = deck[left]
            #print(MSCardName(card-1), " ", end='')
            print (card)
            self.Board[(i%8)+1][i//8] = card
            #print(CardName(c) + " ", end='')
        #print(self.Board)
        #remove -1 filler now
        for i in range(self.cols):
            while len(self.Board[i]) > 0:
                if (self.Board[i][len(self.Board[i])-1]) == -1:
                    self.Board[i].pop()
                else:
                    break

    # print the board in the standard way
    def PrintBoard(self):
        for i in range(8):
            if len(self.Board[0][i]) > 0:
                card = self.Board[0][i][-1]
                print(MSCardName(card, False) + " ", end='')
            else:
                print("   ", end='')
        print()

        j  = 0
        pcnt = 0
        while True:
            for i in range(1, self.cols):
                if j < len(self.Board[i]):
                    card = self.Board[i][j]
                    print(MSCardName(card, False) + " ", end='')
                    pcnt += 1
                else:
                    print("   ", end='')
            print()
            j += 1
            if pcnt == 0:
                break
            pcnt = 0

    # print the board using color and glyphs
    def PrintFancyBoard(self):
        # the top row of freecells and foundations piles is stored in column 0
        print(ansi.bg.green, end='')
        for i in [4, 5, 6, 7, 0, 1, 2, 3]:
            if len(self.Board[0][i]) > 0:
                card = self.Board[0][i][-1]
                CardColor(card)
                print(MSCardName(card) + " ", end='')
            else:
                print("   ", end='')
        print(ansi.bg.black, end='')
        print()

        # print the cascades
        j  = 0
        pcnt = 0
        while True:
            print(ansi.bg.green, end='')
            for i in range(1, self.cols):
                if j < len(self.Board[i]):
                    card = self.Board[i][j]
                    CardColor(card)
                    print(MSCardName(card) + " ", end='')
                    pcnt += 1
                else:
                    print("   ", end='')
            print(ansi.bg.black, end='')
            print()
            j += 1
            if pcnt == 0:
                break
            pcnt = 0
        print()
        print(ansi.reset, end='')

    # move a single card, no auto, no compund, no super moves
    # the move is in "standard notation"
    # NB doesn't yet check validity of the move
    def move(self, m):
        fcih = GetCIH(m[0])
        tcih = GetCIH(m[1])
        if tcih[2]: # special case, move a card to it's foundation home
            card = self.Board[fcih[0]][-1]
            v, r, c = rank(card), suit(card), color(card)
            card = self.Board[fcih[0]].pop()
            self.Board[0][rankmap[r]].append(card)
        else:
            #print(fcih)
            #print(tcih)
            #get from card
            if fcih[1] > -1:
                card = self.Board[0][fcih[1]].pop()
                self.freecells += 1
            else:
                card = self.Board[fcih[0]].pop()
                if len(self.Board[fcih[0]]) == 0:
                    self.freetabs += 1
            # put card in new location
            if tcih[1] > -1:
                self.Board[0][tcih[1]].append(card)
                self.freecells -= 1
            else:
                if len(self.Board[tcih[0]]) == 0:
                    self.freetabs -= 1
                self.Board[tcih[0]].append(card)

    # move cnt cards from and to the locations specified by m
    def cmove(self, m, cnt):
        if cnt == 1:
            self.move(m)
        else:
            fcih = GetCIH(m[0])
            tcih = GetCIH(m[1])
            cards = self.Board[fcih[0]][::-1][0:cnt]
            #print("cards", cards)
            self.Board[tcih[0]].extend(cards[::-1])
            for i in range(cnt):
                self.Board[fcih[0]].pop()

    # see if more than one card can be moves from the supplied col
    # returns the count of cards that can be moved
    # bug needs to respect freecells available. FIX FIX FIX
    # also doesn't do supermoves yet. FIX FIX FIX
    def compoundMove(self, m, freecells, freepiles):
        if m[0] < "1" and m[0] > "8":
            return 1
        col = int(m[0])
        #print("compoundMove", col, freecells, freepiles)
        lst = self.Board[col][::-1]
        #print(lst)
        l = len(lst)
        cnt = 0
        for card in lst:
            if l > 1:
                card2 = lst[cnt + 1]
                if rank(card2) == rank(card) + 1 and color(card2) != color(card):
                    cnt += 1
                    l -= 1
                    continue
                else:
                    break
        return cnt+1

    # what are all the possible moves for a given card returned as a list of moves
    # if h is a valid move, it will be first in the list
    # Doesn't do supermoves yet. FIX FIX FIX
    def possibleMoves(self, card):
        ret = []
        # check if card can go to foundation
        cr, cv, cc = rankmap[suit(card)], rank(card), color(card)
        if cv == 0 or (len(self.Board[0][cr]) > 0 and rank(self.Board[0][cr][-1]) + 1 == cv):
            #print("possibleMoves: h")
            ret.append("h")

        # check if card can go to other tableau
        for i in range(1, self.cols):
            if len(self.Board[i]) < 1:
                continue # skip empty columns
            bc = self.Board[i][-1] # bottom card
            r, v, c = rankmap[suit(bc)], rank(bc), color(bc)
            if v - 1 == cv and c != cc:
                ret.append(str(i))
        return ret

    # Determine how many cards might be placed beneath the supplied card and return that number.
    def mightNeed(self, card):
        cnt = 0
        for i in range(1, self.cols):
            if len(self.Board[i]) < 1:
                continue # skip empty columns
            #print(i, ": ", self.Board[i])
            for c in self.Board[i]:
                if rank(card) > 0 and rank(c) == rank(card) -1 and color(c) != color(card):
                    cnt += 1
        for i in range(0, 4):
            if len(self.Board[0][i]) == 1:
                c = self.Board[0][i][-1]
                #print(c, card)
                if rank(c) == rank(card) -1 and color(c) != color(card):
                    cnt += 1
        return cnt

    # This method was the most difficult part of this project
    # Automatically move cards from the bottom of the cascades and freecells to the foundations
    def autoMoves(self):
        while True:
            iter = 0
            # check cascades
            for i in range(1, self.cols):
                if len(self.Board[i]) < 1:
                    continue # skip empty columns
                card = self.Board[i][-1] # bottom card of column
                r, v, c = rankmap[suit(card)], rank(card), color(card)

                #print(i, r, v, c, MSCardName(card))
                if len(self.Board[0][r]) < 1 and v != 0:
                    continue

                moves = self.possibleMoves(card)
                cnt = self.mightNeed(card)
                #print("autoMoves: card=", MSCardName(card), "moves: ", moves, "cnt: ", cnt)
                if len(moves) > 0 and moves[0] == "h" and (cnt == 0 or v < 2):
                    #  move card to foundation
                    #print("autoMoves: tableau", i)
                    self.Board[0][r].append(card)
                    self.Board[i].pop()
                    iter += 1
            # check the freecells for cards that can be moved to foundations
            for i in range(4, 8):
                if len(self.Board[0][i]) > 0:
                    card = self.Board[0][i][-1]
                    moves = self.possibleMoves(card)
                    cnt = self.mightNeed(card)
                    # this code almost copy/paste from above, fix
                    if len(moves) > 0 and moves[0] == "h" and (cnt == 0 or v < 2):
                        #  move card to foundation
                        #print("autoMoves: freecell", i)
                        self.Board[0][rankmap[suit(card)]].append(card)
                        self.Board[0][i].pop()
                        iter += 1

            if iter == 0:
                break
            # might be more cards to move, try again

    #play moves and pause after each move and show the board
    def play(self, moves):
        self.PrintFancyBoard()
        toss = input()
        #print(moves)
        moveCnt = 1
        for m in moves:
            #print("move: ", m)
            cards = self.compoundMove(m, self.freecells, 0)
            #print("compoundMove: ", cards)
            #self.autoMoves()
            #print("")
            self.cmove(m, cards)
            #print("move(", moveCnt, "): ", m) fix fix fix
            print("move:", m)
            self.autoMoves()
            #print("")
            self.PrintFancyBoard()
            toss = input()

moves = ["26", "76", "72", "72", "5a", "27", "57", "67", "1b", "61", "41", "4h", "4h", "41", "45", "34", "3c","6d", "5b"]
def test():
    a = FreeCellGame()
    a.NewGame(10913)
    a.play(moves)

def test1():
    a = FreeCellGame()
    a.NewGame(5)
    a.PrintFancyBoard()

def test2():
    a = FreeCellGame()
    a.NewGame(10913)
    a.PrintFancyBoard()






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

        self.suit = suit(number)
        self.rank = rank(number)
        self.value = CardRanks.index(self.rank)
        self.glyph = glyph(number)
        # print (f'card number={number} suit={self.suit} rank={self.rank}')

    def color(self):
        return 'red' if self.suit in 'DH' else 'black'

    def can_cascade(self, newcard):
        return self.color() != newcard.color() and (self.value - 1) == newcard.value

    def can_home(self, newcard):
        return self.suit == newcard.suit and (self.value + 1) == newcard.value

    def as_string(self, glyph=True):
        color = ansi.fg.__dict__[self.color()]
        if glyph:
            return f'{color}{self.rank}{self.glyph} '
        else:
            return f'{color}{self.rank}{self.suit} '
    
# Implements:
# 1) A cascade (max_length None, cascade True)
# 2) A home (max_length None, cascade False)
# 3) A free cell (max_length 1, cascade DONT CARE)

class Column(list):
    def __init__(self, max_length=None, cascade=True):
        self.max_length = max_length
        self.cascade = cascade

    def add_card(self, card):
        if not self.can_take_card(card):
            raise Exception(f'Column botch: {card} cannot be added to {self}')
        self.append(card)

    def add_card_from_dealer(self, card):
        self.append(card)

    def can_take_card(self, card):
        if self.max_length and len(self) == self.max_length:
            return False
        if self.cascade:
            if len(self) == 0:
                return True
            return self[-1].can_cascade(card)
        else:
            if len(self) == 0:
                return card.rank == 'A'
            return self[-1].can_home(card)

    def card_in_row(self, row):
        if row < len(self):
            return self[row]

    def top_card(self):
        if self:
            return self[-1]

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
        self.homes = ColumnGroup({i: Column(cascade=False) for i in 'hxyz'})
        self.frees = ColumnGroup({i: Column(max_length=1) for i in 'abcd'})
        self.tableau = ColumnGroup({i: Column(cascade=True) for i in '12345678'})

    def setup(self, seed):
        deck = GetShuffledDeck(seed)
        tableau_size = len(self.tableau)
        tableau = list(self.tableau.values())
        for i in range(len(deck)):
            tableau[i % tableau_size].add_card_from_dealer(deck[i])

    def print(self):
        for i in self.frees.values(): printcard(i.top_card())
        for i in self.homes.values(): printcard(i.top_card())
        print()
        for i in range(self.tableau.get_row_count()):
            for j in self.tableau.values(): printcard(j.card_in_row(i))
            print()
        print(ansi.reset, end='')
        for i in range(1,9):
            print(f'{i}  ', end='')
        print()

    def get_src_column(self, location):
        for i in self.frees, self.tableau:
            if location in i:
                return i[location]

    def get_dst_column(self, location, card):
        if location != 'h':
            return self.get_src_column(location)

        for i in self.homes.values():
            if i.can_take_card(card):
                return i

    # "move" parameter is a two character string: <source><destination>
    # where source or destination can be 1-8 (the tableau), a-d (the frees) or h (homes)
    def raw_move(self, move):
        src, dst = tuple(move)
        sc = self.get_src_column(src)
        card = sc and sc.top_card()
        if not card:
            raise MoveException(f'No card at {move}')

        dc = self.get_dst_column(dst, card)
        if dc is not None and dc.can_take_card(card):
            dc.add_card(card)
            sc.pop()
        else:
            raise MoveException(f'Illegal move {move}')

import sys

if __name__ == '__main__':
    board = Board()
    board.setup(seed=10913)
    lines = []
    if len(sys.argv) > 1:
        lines = open(sys.argv[1]).readlines()
    log = open('cell.log', 'w')
    while True:
        board.print()
        move = (lines and lines.pop(0).strip()) or input()
        log.write(move+'\n')
        log.flush()
        try:
            board.raw_move(move)
        except MoveException as e:
            print(f'{e}')
    