# © Copyright 2019 Lawrence E. Bakst All Rights Reserved
# The code here generates MS compatible Freecell deals and generates moves for them

import random

# cards are numbered 1-52, so zero is an error
# cards are in suit order so 1-13 are Ace of Hearts thru King of Hearts
# if a card is negative it's facedown, not used for Freecell but needed for Klondike

CardNames = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K"]
RankNames = ["Heart", "Diamond", "Spade", "Club"]
ShortRankNames = ["H", "D", "S", "C"]
MSRankNames = ["C", "D", "H", "S"]
MSRankGlyphs = ["♣", "♦", "♥", "♠"]
Colors = ["Red", "Red", "Black", "Black"]
max = 52

# Create a deck of cards
def NewDeck(n=max):
	return [x for x in range(1, n+1)]

def FullCardName(card):
	#print((card - 1) % 13)
	#print((card - 1) // 13)
	return CardNames[(card - 1) % 13] + " of " + RankNames[(card-1) // 13] + "s"

def CardName(card):
	#print((card - 1) % 13)
	#print((card - 1) // 13)
	return CardNames[(card - 1) % 13] + ShortRankNames[(card-1) // 13]

def RedCard(card):
	return card <= 26

def MSCardName(card):
	card -= 1
	suit = card % 4
	val = card // 4
	return CardNames[val] + MSRankGlyphs[suit]

reset='\033[0m'
bold='\033[01m'
disable='\033[02m'
underline='\033[04m'
reverse='\033[07m'
strikethrough='\033[09m'
invisible='\033[08m'
class fg: 
	black='\033[30m'
	red='\033[31m'
	green='\033[32m'
	orange='\033[33m'
	blue='\033[34m'
	purple='\033[35m'
	cyan='\033[36m'
	lightgrey='\033[37m'
	darkgrey='\033[90m'
	lightred='\033[91m'
	lightgreen='\033[92m'
	yellow='\033[93m'
	lightblue='\033[94m'
	pink='\033[95m'
	lightcyan='\033[96m'
class bg: 
	black='\033[40m'
	red='\033[41m'
	green='\033[42m'
	orange='\033[43m'
	blue='\033[44m'
	purple='\033[45m'
	cyan='\033[46m'
	lightgrey='\033[47m'

# MS suit ordering is club, diamond, heart, spade
def convertToMS(card):
	card -= 1
	offset = [39, 13, 0, 26]
	suit = card % 4
	val = card // 4
	return offset[suit] + val + 1

state = 1
def srand(seed):
	global state
	state = seed

# Suposedly MS compiler runtime compatible version of rand
# first 5 numbers with seed of 1 are 41, 18467, 6334, 26500, 19169
def rand():
	global state
	state = ((214013 * state) + 2531011) % 2147483648 # mod 2^31
	return 	state // 65536

# Knuth-Fisher-Yates shuffle algorithm should be non-biased
# google biased shuffle
# https://blog.codinghorror.com/the-danger-of-naivete/
# https://stackoverflow.com/questions/859253/why-does-this-simple-shuffle-algorithm-produce-biased-results-what-is-a-simple

def Shuffle(deck):
	for i in range(len(deck) - 1, 0, -1):
		card = random.randint(0, i)
		deck[i], deck[card] = deck[card], deck[i]

def MoveCard(frm, to):
	to.push(frm.pop)

class FreeCellGame:
	def __init__(self):
		self.cols = 9
		self.rows = 21
		self.Board = [[-1 for j in range(self.rows)] for i in range(self.cols)]

# Generate a Freecell game, game 5 is easy so it's the default
	def NewGame(self, game=5):
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
		# print the first 6 rows of 8 cards each
		for j in range (0, 6):
			for i in range(1, self.cols):
				#print(self.Board[i])
				card = self.Board[i][j]
				print(MSCardName(card) + " ", end='')
			print()
		# print the last row of 4 cards
		for i in range(1, 5):
			card = self.Board[i][6]
			print(MSCardName(card) + " ", end='')
		print()

# print the board using color and glyphs
	def PrintFancyBoard(self):
		# print the first 6 rows of 8 cards each
		for j in range (0, 6):
			for i in range(1, self.cols):
				print(bg.green, end='')
				#print(self.Board[i])
				card = self.Board[i][j]
				if RedCard(card):
					print(fg.red, end='')
				else:
					print(fg.black, end='')
				print(MSCardName(card) + " ", end='')
				print(bg.black, end='')
			print()
		# print the last row of 4 cards
		for i in range(1, 5):
			print(bg.green, end='')
			card = self.Board[i][6]
			if RedCard(card):
				print(fg.red, end='')
			else:
				print(fg.black, end='')
			print(MSCardName(card-1) + " ", end='')
			print(bg.black, end='')
		print()
		print(reset, end='')

# test board 5
def test():
	a = FreeCellGame()
	a.NewGame(5)
	a.PrintFancyBoard()

