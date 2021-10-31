import generators
from abc import ABCMeta, abstractmethod
import argparse
import time
import random

ROLL = 'r'
HOLD = 'h'
VALID_CHOICE = [ROLL, HOLD]
END_OF_GAME_SCORE = 100

random.seed(0)

class Die(object):
	def roll(self):
		return random.randint(1, 6)

class Player(object):
	__metaclass__ = ABCMeta

	@abstractmethod
	def make_decision(self, current_score, net_score):
		raise NotImplementedError('this is not implemented')

class PlayerFactory(object):
	def get_player(type):
		return HumanPlayer() if type == 'human' else ComputerPlayer()
	get_player = staticmethod(get_player)


class HumanPlayer(Player):
	def make_decision(self, current_score, net_score):
		msg = ''
		while True:
			choice = raw_input(msg)
			if choice in VALID_CHOICE:
				return choice
			else:
				msg = 'Please enter \'{}\' or \'{}\': '.format(ROLL, HOLD)

class ComputerPlayer(Player):
	def make_decision(self, current_score, net_score):
		value = min(25, END_OF_GAME_SCORE - net_score)
		return ROLL if current_score < value else HOLD


class Game(object):
	def __init__(self, human_players, ai_players):
		self.human_players = human_players
		self.ai_players = ai_players
		self.reset()
	
	def reset(self):
		self.die = Die()
		self.players = \
			[PlayerFactory.get_player('human') for x in range(self.human_players)] \
			+ [PlayerFactory.get_player('computer') for x in range(self.ai_players)]
		self.net_score = [0 for x in range(self.human_players + self.ai_players)]
		self.current_turn_score = 0
		self.player_turn_index = 0
		self.max_player = self.human_players + self.ai_players
	
	def add_turn_score(self, score):
		self.current_turn_score += score
		self.net_score[self.player_turn_index] += score

	def hold_score(self):
		self.current_turn_score = 0

	def print_winner_and_reset(self):
		winner_index = self.player_turn_index
		print ('Player {} won!'.format(winner_index + 1))
		self.reset()
		return winner_index

	def is_end_game(self):
		return any(score >= END_OF_GAME_SCORE for score in self.net_score)

	def next_player(self):
		self.current_turn_score = 0
		self.player_turn_index = (self.player_turn_index + 1) % self.max_player

	def apply_rule(self, choice):
		player_name = self.player_turn_index + 1
		if choice == HOLD:
			self.hold_score()
			print ('Player {} net score is now {}'.format(
				player_name, self.net_score[self.player_turn_index]))
			self.next_player()
		elif choice == ROLL:
			roll = self.die.roll()
			print ('Player {} rolled {}'.format(player_name, roll))
			if roll == 1:
				self.add_turn_score(-self.current_turn_score)
				self.next_player()
				print ('Player {} lost turn'.format(player_name))
			else:
				self.add_turn_score(roll)
				print ('Player {} scored {} for this turn and net {}'.format(
					player_name,
					self.current_turn_score,
					self.net_score[self.player_turn_index]))
		print ('')

	def playerTurnToPlay(self):
		print ('It\'s the turn of player {}.'.format(self.player_turn_index + 1))
		print ('Would you like to roll or hold? [{}/{}] '.format(ROLL, HOLD))
		player_net_score = self.net_score[self.player_turn_index]
		choice = self.players[self.player_turn_index].make_decision(
			self.current_turn_score, player_net_score)
		self.apply_rule(choice)

	def run(self):
		while not self.is_end_game():
			self.playerTurnToPlay()
		return self.print_winner_and_reset()

class TimeGameProxy:
	def __init__(self, numPlayers, numComputerPlayers, timed):
		self.game = Game(numPlayers, numComputerPlayers)
		self.timed = timed
		self.start_time = time.time()

	def is_end_game(self):
		elapsed_time = (time.time() - self.start_time) / 60
		return self.game.is_end_game() or (self.timed is not None and elapsed_time >= self.timed)

	def run(self):
		if timed is not None:
			while not self.is_end_game():
				self.game.playerTurnToPlay()
			return self.game.print_winner_and_reset()
		else:
			return self.game.run()

def parseArg():
	parser = argparse.ArgumentParser(description='Pig game.')
	parser.add_argument('--numPlayers', help='how many players?', required=False)
	parser.add_argument('--numComputerPlayers', help='how many computer players?', required=False)
	parser.add_argument('--player1', help='[human/computer]?', required=False)
	parser.add_argument('--player2', help='[human/computer]?', required=False)
	parser.add_argument('--multiGame', help='how many rounds?', required=False)
	parser.add_argument('--timed', help='how long is a round?', required=False)
	return parser.parse_args()

def extractNumberOrDefault(params, testValue, default, isFloat = False):
	try:
		parsed = float(params) if isFloat else int(params)
		return parsed if parsed >= testValue else default
	except:
		return default

def extractNumberOfPlayersFromParams(params):
	player1 = params.player1
	player2 = params.player2
	numPlayers = 0
	numComputerPlayers = 0

	if player1 is None and player2 is None:
		numPlayers = extractNumberOrDefault(params.numPlayers, 0, 0)
		numComputerPlayers = extractNumberOrDefault(params.numComputerPlayers, 0, 0)

		maxPlayer = numPlayers + numComputerPlayers
		if maxPlayer == 0:
			numComputerPlayers = 2
		elif maxPlayer == 1:
			numComputerPlayers += 1
	else:
		if player1 == 'human':
			numPlayers += 1
		else:
			numComputerPlayers += 1
		
		if player2 == 'human':
			numPlayers += 1
		else:
			numComputerPlayers += 1

	return numPlayers, numComputerPlayers

if __name__ == '__main__':
    params = parseArg()

    numPlayers, numComputerPlayers = extractNumberOfPlayersFromParams(params)
    timed = extractNumberOrDefault(params.timed, 1, None, True)
    multiGame = extractNumberOrDefault(params.multiGame, 1, 1)

    round = 0
    winner_round = [0 for _ in range(numPlayers + numComputerPlayers)]

    while round < multiGame:
        game = TimeGameProxy(numPlayers, numComputerPlayers, timed)
        winner_index = game.run()
        winner_round[winner_index] += 1
        round += 1

    for (i, score) in enumerate(winner_round):
        print ('Player {} won {} times'.format(i + 1, score))
