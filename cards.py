# © Copyright 2019 Lawrence E. Bakst All Rights Reserved
# The code here generates MS compatible Freecell deals and plays back solutions.
# Soon to generate and evaluate moves to find solutions.

import random
import ansi

def printf(str, *args):
    print(str % args, end='')

# cards are integers numbered 1-52, so zero is an error.
# cards have 3 attributes, rank (0-12), suit (0-3) and color (True if red, False if black).
# MS uses value ordering, so the first 4 cards are A♣, A♦, A♥, A♠
# I prefer rank ordering but I decided to go with MS.
# if a card is negative, it's facedown, not used for Freecell, but needed for Klondike.
CardNames = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K"]
LongSuitNames = ["Club", "Diamond", "Heart", "Spade"]
SuitNames = ["C", "D", "H", "S"]
SuitGlyphs = ["♣", "♦", "♥", "♠"]
FreeCellNames =  ["a", "b", "c", "d"]

def rank(card):
    return (card - 1) // 4

def suit(card):
    return (card - 1) % 4

# true if red
def color(card):
    return suit(card) == 1 or suit(card) == 2

def isRedCard(card):
    return suit(card) == 1 or suit(card) == 2

def CardName(card, glyph=True):
    if card <= 0:
        return "  "
    if glyph:
        return CardNames[rank(card)] + SuitGlyphs[suit(card)]
    else:
        return CardNames[rank(card)] + SuitNames[suit(card)]

def CardNumber(name):
    return CardNames.index(name[0])*4 + SuitNames.index([name[1]])

#print an ANSI sequence that sets the card color
def ColorCard(card, used=True):
    if not used: return ""
    if isRedCard(card):
        return ansi.Fg.red
    else:
        return ansi.Fg.black

def isDigit(str):
    return str >= "1" and str <= "8"

def isHome(str):
    return str == "h"

def isFreeCell(str):
    return str >= "a" and str <= "d"

def isValidSyntax(m):
    return len(m) == 2 and (isDigit(m[0]) or isHome(m[0]) or isFreeCell(m[0])) and (isDigit(m[1]) or isHome(m[1]) or isFreeCell(m[1]))

# parse a move which is a two character string into a column, index, and home
# Returns a tuple(colum, index, home) that describes the from or to of a move
# fix the 4
# move to FeeeCell class
# talk with rick about home = l == "h"
# talk with rick about not genning up a return value
def GetCIH(l):
    col, idx, home = -1, -1, False
    if l >= "1" and l <= "8":
        col = int(l) - 1
    elif l >= "a" and l <= "d":
        col = -1
        idx = ord(l) - ord("a")
    elif l == "h":
        home = True # home = l == "h"
    return (col, idx, home)

def MoveName(src, dst):
    return src.name + dst.name

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

# A deck of cards implemented as a list. The only things you can do are Take() and Shuffle().
class Deck(list):
    def __init__(self):
        self.deck = list(range(1, 53)) # [x for x in range(1, n+1)]

    def Take(self):
        return(self.deck.pop())

    def Peek(self, i=-1):
        return(self.deck[i])

    # Knuth-Fisher-Yates shuffle algorithm should be non-biased
    # google biased shuffle
    # https://blog.codinghorror.com/the-danger-of-naivete/
    # https://stackoverflow.com/questions/859253/why-does-this-simple-shuffle-algorithm-produce-biased-results-what-is-a-simple
    # currently not used as the MS compatible code shuffeling during the deal
    def Shuffle(deck):
        __init__(self)
        for i in range(len(deck) - 1, 0, -1):
            card = random.randint(0, i)
            self.deck[i], self.deck[card] = self.deck[card], self.deck[i]

    # This is the way that MS shuffles cards, assumes cards are dealt a certain way
    # as we do in Setup()
    def MSShuffle(game):
        srand(game)
        left = len(self.deck)
        tmp = Deck()
        for i in range(52):
            idx = rand() % left
            card = tmp[idx]
            left -= 1
            tmp[idx] = tmp[left]
            #print(CardName(card-1), " ", end='')
            #self.tableau[(i%8)+1][i//8] = card
            self.deck.append(card)
            #print(CardName(c) + " ", end='')

# A pile of cards implmented as a list.
class Pile(list):
    def __init__(self, kind, name, suit):
        if not kind in ["tableau", "freecell", "foundation"]:
            raise("Pile: invalid kind")
        self.kind = kind
        self.name = name
        self.suit = suit # only used for foundations

    def isEmpty(self):
        return(len(self) == 0)

    def Put(self, card):
        self.append(card)

    def Take(self):
        return(self.pop())

    def Count(self):
        return(len(self))

    # the top card of a pile coild also be called the bottom card of tableau
    # we simple return the last in the list
    def TopCard(self):
        if len(self) == 0:
            return 0
        return(self[-1])

    def Move(self, to, cnt):
        rev = self[::-1][0:cnt]
        to.extend(rev[::-1])
        for i in range(cnt):
            self.Take()

    # return the cards on a tableau that are "in order"
    def OrderedCards(self):
        lst = self[::-1]
        l = len(lst)
        #print(l, lst)
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
        l2 = lst[:cnt+1]
        #print(cnt+1, l2)
        return l2

    def NumOrderedCards(self):
        oc = self.OrderedCards()
        #print(oc)
        return len(oc)

    # how many cards can be moved from a tableau onto topCard
    def MatchingCards(self, topCard):
        oc = self.OrderedCards()
        if topCard == 0:
            return len(oc)
        cnt = 1
        for card in oc:
            if rank(topCard) == rank(card) + 1 and color(topCard) != color(card):
                break
            cnt += 1
        #print("MatchingCards: ", cnt, topCard, oc)
        return cnt

    # can card be moved onto a pile
    def CanGoOnto(self, card):
        if self.kind == "freecell":
            return len(self) == 0
        elif self.kind == "foundation":
            # check if card can go to foundation
            return (rank(card) == 0 and suit(card) == self.suit) or (len(self) > 0 and rank(self.TopCard()) == rank(card) - 1 and suit(self.TopCard()) == suit(card))
        elif self.kind == "tableau":
            return len(self) > 0 and rank(self.TopCard()) == rank(card) + 1 and color(self.TopCard()) != color(card)
        else: 
            raise("CanGoOnto: bad tableau")


# The board of a Freecell game.
class FreeCellBoard():
    def __init__(self, tableaux, freecells, foundations):
        self.tableau = [Pile("tableau", name, 0) for name in tableaux]
        self.freecells = [Pile("freecell", name, 0) for name in freecells]
        self.foundations = []
        cnt = 0
        for name in foundations:
            pile = Pile("foundation", name, cnt)
            self.foundations.append(pile)
            cnt += 1

    def freecellcnt(self):
        cnt = 0
        for p in self.freecells:
            cnt += len(p)
        return len(self.freecells) - cnt

    def freetabcnt(self):
        cnt = 0
        for p in self.tableau:
            if len(p) == 0:
                cnt += 1
        return cnt

    def longestCol(self):
        return max([len(l) for l in self.tableau])

    def pad(self, col, padlen):
        c = list(col)
        for i in range(padlen - len(c)):
            c.append("   ")
        return c

    def Setup(self, game):
        left = 52
        n = 52
        srand(game)
        deck = list(range(1, n+1))
        for i in range(52):
            idx = rand() % left
            card = deck[idx]
            left -= 1
            deck[idx] = deck[left]
            #print(CardName(card-1), " ", end='')
            #self.tableau[(i%8)+1][i//8] = card
            self.tableau[(i%8)].Put(card)
            #print(CardName(c) + " ", end='')


    def TableauCardNamesInRows(self, fancy=False):
        lcl = self.longestCol()
        cols = []
        for pile in self.tableau:
            col = []
            for card in pile:
                col.append(ColorCard(card, fancy) + CardName(card)+" ")
            cols.append(self.pad(col, lcl))
        # transpose the cols into rows
        rows = [''.join(chars) for chars in zip(*cols)]
        return rows

    def PrintBoard(self):
        str = ""
        for deck in self.freecells:
            str += CardName(deck.TopCard())+" "
        for deck in self.foundations:
            str += CardName(deck.TopCard())+" "
        print(str)
        for line in self.TableauCardNamesInRows():
            print(line)

    def PrintFancyBoard(self):
        str = ""
        gbg = ansi.Bg.green
        bgb = ansi.Bg.black
        #gbg = ansi.Bbg.green
        #bgb = ansi.Bbg.black
        for deck in self.freecells:
            str += ColorCard(deck.TopCard()) + CardName(deck.TopCard())+" "
        for deck in self.foundations:
            str += ColorCard(deck.TopCard()) + CardName(deck.TopCard())+" "
        print(gbg, str, bgb)
        for line in self.TableauCardNamesInRows(True):
            print(gbg, line, bgb)
        #print(ansi.Fg.w, line, bgb)
        print(ansi.reset, end="")

    def PutHome(self, card):
        card = self.tableau[fm["col"]].Take()
        self.foundations[suit(card)].Put(card)

    # Given a move in "standard notation" move a single card, no auto, no compund, no super moves
    # NB doesn't yet check validity of the move
    def move(self, m, cnt=1):
        col, idx, home = GetCIH(m[0])
        #print(fm, to)
        if m[1] == "h": # special case, move a card to it's home foundation 
            card = self.tableau[col].Take()
            self.foundations[suit(card)].Put(card)
        else:
            #get from card from freecell or tableau
            if idx > -1:
                card = self.freecells[idx].Take() # Board[0][fm["idx"]].pop()
            else:
                #print(self.board.tableau[fm["col"]])
                card = self.tableau[col].Take()
            # put card in new location in a freecell or tableau
            col, idx, home = GetCIH(m[1])
            if  idx > -1:
                self.freecells[idx].Put(card)
            else:
                self.tableau[col].Put(card)

    # move cnt cards from and to the locations specified by m
    # no validation
    def cmove(self, m, cnt):
        if cnt == 1:
            self.move(m)
        else:
            # two lines below broken?
            fcol, idx, home = GetCIH(m[0])
            tcol, idx, home = GetCIH(m[1])
            self.tableau[fcol].Move(self.tableau[tcol], cnt)

    # Return how many cards can be moved from the supplied source column
    # and returns the count of cards that can be moved.
    # The count is moderated by the available freecells and the top card
    # in the destination.
    # Does not do supermoves yet.
    def compoundMove(self, m):
        if m[0] < "1" or m[0] > "8" or m[1] < "1" or m[1] > "8":
            return 1
        src = int(m[0]) - 1
        dst = int(m[1]) - 1
        #print("compoundMove", col, freecells, freepiles)
        cardCount = self.tableau[src].NumOrderedCards()
        cardCount2 = min(cardCount, self.freecellcnt() + 1)
        oc = self.tableau[src].OrderedCards()
        mc = self.tableau[src].MatchingCards(self.tableau[dst].TopCard())
        #print("compoundMove: ", src, dst, cardCount, cardCount2, mc)
        return cardCount2

    # what are all the possible moves for a given card returned as a list of moves
    # if h is a valid move, it will be first in the list
    # Doesn't do supermoves yet. FIX FIX FIX
    def possibleMoves(self, fm, card):
        ret = []
        # check if card can go to foundation
        cr, cs, cc = rank(card), suit(card), color(card)
        if cr == 0 or (len(self.foundations[cs]) > 0 and rank(self.foundations[cs].TopCard()) + 1 == cr):
            #print("possibleMoves: h")
            ret.append(fm + "h")

        # check if card can go to other tableau
        cnt = -1
        for col in self.tableau:
            cnt += 1
            if len(col) > 0:
                bc = col[-1] # bottom card
                r, s, c = rank(bc), suit(bc), color(bc)
                if not (r - 1 == cr and c != cc):
                    continue
            ret.append(fm + str(cnt+1))
        return ret

# list of possible moves in order of (my guess at) potential to lead to a solution
# 1. tableau to foundation
# 2. freecell to foundation
# 3. tableau to freecell
# 4. tableau to tableau
# 5. freecell to tableau
# GOING TO IMPROVE THIS CODE, should be cartesian product but there is one execption
    def MoveList(self):
        moves = []
        ofc = self.OpenFreeCells()

        # 1. check tableau for moves to the foundations
        for col in self.tableau:
            card = col.TopCard()
            for p in self.foundations:
                if p.CanGoOnto(card):
                    moves.append(MoveName(col, p))

        # 2. check freecells for moves to the tableau
        for col in self.freecells:
            card = col.TopCard()
            for p in self.foundations:
                if p.CanGoOnto(card):
                    moves.append(MoveName(col, p))

        # 3. check tableau for moves to the foundations
        for col in self.tableau:
            card = col.TopCard()
            for p in self.freecells:
                if p.CanGoOnto(card):
                    moves.append(MoveName(col, p))

        # 4. check tableau for moves to the empty tableau FIX FIX FIX
        # needs to handle the multiple cards case
        for col in self.tableau:
            card = col.TopCard()
            for p in self.tableau:
                if p.CanGoOnto(card):
                    moves.append(MoveName(col, p))

        # 5. check freecells for moves to the tableau
        for col in self.freecells:
            card = col.TopCard()
            for p in self.tableau:
                if p.CanGoOnto(card):
                    moves.append(MoveName(col, p))

        return moves




#            #print(i, r, v, c, CardName(card))
#            if len(self.foundations[s]) < 1 and r != 0:
#                continue
#            moves.extend(self.possibleMoves(chr(ord("0") + cnt), card))
#            for i in ofc:
#                moves.extend(self.possibleMoves(chr(ord("0") + cnt), card))

        # check the freecells for cards that can be moved to foundations
#       cnt = 0
#      for deck in self.freecells:
#            if len(deck) == 1:
#               card = deck.TopCard()
#                moves.extend(elf.possibleMoves(fc[cnt], card))
#        return moves

    # Determine how many cards could be placed beneath the supplied card and return that number.
    def dependsOn(self, card):
        cnt = 0
        for col in self.tableau:
            if len(col) < 1:
                continue # skip empty columns
            #print(i, ": ", self.Board[i])
            for c in col:
                if rank(card) > 0 and rank(c) == rank(card) -1 and color(c) != color(card):
                    cnt += 1
        #check freecells
        for deck in self.freecells:
            if len(deck) == 1:
                c = deck.TopCard()
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
            for col in self.tableau:
                if len(col) < 1:
                    continue # skip empty columns
                card = col.TopCard()
                r, s, c = rank(card), suit(card), color(card)

                #print(i, r, v, c, CardName(card))
                if len(self.foundations[s]) < 1 and r != 0:
                    continue

                moves = self.possibleMoves("", card)
                cnt = self.dependsOn(card)
                #print("autoMoves: card=", CardName(card), "moves: ", moves, "cnt: ", cnt)
                if len(moves) > 0 and moves[0] == "h" and (cnt == 0 or r < 2):
                    #  move card to foundation
                    #print("autoMoves: tableau", i)
                    # use move
                    card = col.Take()
                    self.foundations[s].Put(card)
                    iter += 1
            # check the freecells for cards that can be moved to foundations
            for deck in self.freecells:
                if len(deck) == 1:
                    card = deck.TopCard()
                    moves = self.possibleMoves("", card)
                    cnt = self.dependsOn(card)
                    # this code almost copy/paste from above, fix
                    if len(moves) > 0 and moves[0] == "h" and (cnt == 0 or r < 2):
                        #  move card to foundation
                        #print("autoMoves: freecell", i)
                        card = deck.Take()
                        self.foundations[suit(card)].Put(card)
                        iter += 1

            if iter == 0:
                break
            # loop again, more cards might be to moved

    # returns true if the games has been solved.
    def Solved(self):
        topCards = [p.TopCard() for p in self.foundations]
        return topCards == [49, 50, 51, 52]

    # return a list of empty freecell indicies
    def OpenFreeCells(self):
        lst = []
        cnt = -1
        for pile in self.foundations:
            cnt += 1
            if pile.isEmpty():
                lst.append(cnt)
        return lst

tableaux = ["1", "2", "3", "4", "5", "6", "7", "8"]
freecells = ["a", "b", "c", "d"]
foundations = ["h", "h", "h", "h"]

class FreeCellGame:
    def __init__(self):
        self.board = FreeCellBoard(tableaux, freecells, foundations)

# Generate a new Freecell game and set up the board, game 5 is easy so it's the default
    def NewGame(self, game=5):
        self.board.Setup(game)

    def PrintBoard(self):
        self.board.PrintBoard()

    def PlayGame(self):
        self.board.PrintFancyBoard()
        #print(moves)
        moveCnt = 1
        moves = []
        while True:
            printf("move[%d]: ", moveCnt)
            #print("move: ", m)
            move = input()
            if not isValidSyntax(move):
                print("move has invalid syntax")
                continue
            cards = self.board.compoundMove(move)
            #print("compoundMove: ", cards)
            #self.autoMoves()
            #print("")
            self.board.cmove(move, cards)
            #print("move(", moveCnt, "): ", m) fix fix fix
            #print("possible moves: ", self.board.MoveList())
            self.board.autoMoves()
            #print("")
            #self.PrintBoard()
            self.board.PrintFancyBoard()
            if self.board.Solved():
                break
            moveCnt += 1

    #play moves and pause after each move and show the board
    def PlayMoves(self, moves):
        self.board.PrintFancyBoard()
        toss = input()
        #print(moves)
        moveCnt = 1
        for m in moves:
            printf("movelist[%d]: %s\n", moveCnt, self.board.MoveList())
            #print("move: ", m)
            cards = self.board.compoundMove(m)
            #print("compoundMove: ", cards)
            #self.autoMoves()
            #print("")
            self.board.cmove(m, cards)
            #print("move(", moveCnt, "): ", m) fix fix fix
            printf("move[%d]: %s\n", moveCnt, m)
            #print("possible moves: ", self.board.MoveList())
            self.board.autoMoves()
            #print("")
            #self.PrintBoard()
            self.board.PrintFancyBoard()
            toss = input()
        return self.board

moves = ["26", "76", "72", "72", "5a", "27", "57", "67", "1b", "61", "41", "4h", "4h", "41", "45", "34", "3c","6d", "5b"]
def test():
    game = 10913
    a = FreeCellGame()
    a.NewGame(game)
    b = a.PlayMoves(moves)
    if not b.Solved():
        printf("game %d, Not Solved\n", game)
    printf("game %d, Solved\n", game)

def play(game=10913):
    a = FreeCellGame()
    a.NewGame(game)
    a.PlayGame()

def Test():
    a = FreeCellGame()
    a.NewGame(10913)
    a.PrintBoard()
    toss = input()
    a.board.move("26")
    a.PrintBoard()
    a.board.move("1a")
    a.PrintBoard()
    a.board.move("1b")
    a.PrintBoard()
    a.board.move("8h")
    a.PrintBoard()



