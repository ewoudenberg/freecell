# some pyhon code that implements flipping coin(s)
import random

# Coins keep track of the the number of heads and tails they've had
class Coin:
	head_odds = 0.5
	heads = 0
	tails = 0

	def headp(self):
		odds = random.random()
		if odds <= self.head_odds:
			return True
		else:
			return False

	def flip(self):
		odds = random.random()
		if self.headp():
			self.heads += 1
		else:
			self.tails += 1
		return self.heads, self.tails

	def flips(self, n=1):
		for i in range(n):
			self.flip()
		return self.heads, self.tails

	def __init__(self, head_odds=0.5):
		self.head_odds = head_odds

# A CoinSet is a list of coins that all have the same fairness
class CoinSet:
	coins = []

	def __init__(self, head_odds=0.5, n=10):
		for x in range(n):
			self.coins.append(Coin(head_odds))

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
