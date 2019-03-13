# some pyhon code that implements flipping coin(s)
import random

# Coins keep track of the the number of heads and tails they've had
class Coin:
	def __init__(self, head_odds=0.5):
		self.head_odds = head_odds
		self.heads = 0
		self.tails = 0

	def headp(self):
		return random.random() <= self.head_odds

	def flip(self, n=1):
		print(n)
		for i in range(n):
			if self.headp():
				self.heads += 1
			else:
				self.tails += 1
		return self.heads, self.tails

# A CoinSet is a list of coins that all have the same fairness
class CoinSet:
	def __init__(self, head_odds=0.5, n=10):
		self.coins = [ Coin(head_odds) for x in range(n) ]

# trial flips all the coins in the coinset and returns the number of heads and tails
# see the binomial theorem at work
	def trial(self, trials=10):
		headc = tailc = 0
		for r in range(trials):
			for c in self.coins:
				if c.headp():
					headc += 1
				else:
					tailc += 1
		return headc, tailc
