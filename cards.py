# © Copyright 2019 Lawrence E. Bakst All Rights Reserved
# The code here generates MS compatible Freecell deals, makes moves, generates moves
# and evaluates them.

import random
import ansi

# cards are numbered 1-52, so zero is an error.
# My preferece would be that cards are in suit order so 1-13 are Ace of Hearts thru King of Hearts.
# However MS uses card order so I decided to go with that to avoid a mapping layer.
# if a card is negative it's facedown, not used for Freecell but needed for Klondike.

CardNames = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K"]
#RankNames = ["Heart", "Diamond", "Spade", "Club"]
#ShortRankNames = ["H", "D", "S", "C"]
MSRankNames = ["C", "D", "H", "S"]
MSRankGlyphs = ["♣", "♦", "♥", "♠"]
#Colors = ["Red", "Red", "Black", "Black"]
rankmap = [1, 2, 0, 3]
max = 52

# Create a deck of cards
def NewDeck(n=max):
	return [x for x in range(1, n+1)]

def value(card):
	return (card - 1) // 4

def rank(card):
	return (card - 1) % 4

# true if red
def color(card):
	return rank(card) == 1 or rank(card) == 2

def MSRedCard(card):
	card -= 1
	suit = card % 4
	if suit == 1 or suit == 2:
		return True
	return False

def MSCardName(card):
	card -= 1
	suit = card % 4
	val = card // 4
	return CardNames[val] + MSRankGlyphs[suit]


# MS suit ordering is club, diamond, heart, spade
# I don't think they knew that suits have an order
def convertToMS(card):
	card -= 1
	offset = [39, 13, 0, 26]
	suit = card % 4
	val = card // 4
	return offset[suit] + val + 1

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
	return 	state // 65536

# Knuth-Fisher-Yates shuffle algorithm should be non-biased
# google biased shuffle
# https://blog.codinghorror.com/the-danger-of-naivete/
# https://stackoverflow.com/questions/859253/why-does-this-simple-shuffle-algorithm-produce-biased-results-what-is-a-simple
# not really used as the ms compatible code does it a different way
def Shuffle(deck):
	for i in range(len(deck) - 1, 0, -1):
		card = random.randint(0, i)
		deck[i], deck[card] = deck[card], deck[i]

# code to implement a FreeCellGame
class FreeCellGame:
	def __init__(self):
		self.cols = 9
		self.rows = 21
		self.freecells = 4
		self.freetabs = 0

# Generate a new Freecell game and set up the board, game 5 is easy so it's the default
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
				print(MSCardName(card) + " ", end='')
			else:
				print("   ", end='')
		print()

		j  = 0
		pcnt = 0
		while True:
			for i in range(1, self.cols):
				if j < len(self.Board[i]):
					card = self.Board[i][j]
					print(MSCardName(card) + " ", end='')
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
		for i in range(8):
			if len(self.Board[0][i]) > 0:
				card = self.Board[0][i][-1]
				CardColor(card)
				print(MSCardName(card) + " ", end='')
			else:
				print("   ", end='')
		print(ansi.bg.black, end='')
		print()

		# print the tableau
		j  = 0
		pcnt = 0
		while True:
			print(ansi.bg.green, end='')
			for i in range(1, self.cols):
				if j < len(self.Board[i]):
					card = self.Board[i][j]
					CardColor(card)
					pcnt += 1
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
			v, r, c = value(card), rank(card), color(card)
			card = self.Board[fcih[0]].pop()
			self.Board[0][rankmap[r]].append(card)
		else:
			print(fcih)
			print(tcih)
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
	# automatically move cards and the bottom of the tableau to the foundations
	def autoMoves(self):
		for i in range(1, self.cols):
			if len(self.Board[i]) < 1:
				continue # skip empty columns
			card = self.Board[i][-1]
			r, v = rankmap[rank(card)], value(card)
			#print(i, r, v)
			if len(self.Board[0][r]) < 1 and v != 0:
				continue
			if v == 0 or (len(self.Board[0][r]) > 0 and value(self.Board[0][r][-1]) + 1 == v):
				print("auto move ", i, "h", )
				self.Board[0][r].append(card)
				self.Board[i].pop()





# test board 5
def test1():
	a = FreeCellGame()
	a.NewGame(5)
	a.PrintFancyBoard()

def test2():
	a = FreeCellGame()
	a.NewGame(10913)
	a.PrintFancyBoard()

def test3():
	a = FreeCellGame()
	a.NewGame(10913)
	a.PrintFancyBoard()
	a.move("2a")
	a.move("a6")
	a.move("4h")
	a.move("8h")
	a.move("2a")
	a.PrintFancyBoard()

def test4():
	a = FreeCellGame()
	a.NewGame(10913)
	a.PrintFancyBoard()
	a.move("26")
	a.move("76")
	a.move("72")
	a.move("72")
	a.move("72")
	a.move("5a")
	a.move("27")
	a.move("57")
	a.move("67")
	a.move("1b")
	a.move("61")
	a.move("41")
	a.move("4h")
	a.move("4h")
	a.move("41")
	a.move("45")
	a.move("34")
	a.move("3c")
	a.move("6d")
	a.move("5b")
	a.PrintFancyBoard()


