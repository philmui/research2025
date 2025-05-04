##################################################################
# simulation.py
#
# This file has the main abstractions for the simulations.
# It contains the base strategy class and the factory class for
# creating simulations.
#
# @author: Theodore Mui
# @version: 1.0
# @since: 2025-05-03
#
##################################################################

import json
import random
import numpy as np
from itertools import combinations
import logging
# Default constants for prisoner's dilemma payoffs
# These can be overridden by config values
# (T)emptation, (R)eward, (P)unishment, (S)ucker
DEFAULT_T, DEFAULT_R, DEFAULT_P, DEFAULT_S = 5, 3, 1, 0

class Strategy:
    """Base class for all prisoner's dilemma strategies"""
    def __init__(self, name):
        self.name = name
        self.history = []
        self.opponent_history = []
        self.score = 0
    
    def make_move(self):
        """Return 'C' for cooperate or 'D' for defect"""
        raise NotImplementedError("Subclasses must implement make_move()")
    
    def record_result(self, my_move, opponent_move, score):
        """Record the moves and update score"""
        self.history.append(my_move)
        self.opponent_history.append(opponent_move)
        self.score += score
    
    def reset(self):
        """Reset for a new game"""
        self.history = []
        self.opponent_history = []
        self.score = 0

class AllCooperateStrategy(Strategy):
    """Always cooperates"""
    def make_move(self):
        return 'C'

class AllDefectStrategy(Strategy):
    """Always defects"""
    def make_move(self):
        return 'D'

class TitForTatStrategy(Strategy):
    """Cooperates on first move, then copies opponent's previous move"""
    def make_move(self):
        if not self.opponent_history:
            return 'C'  # Cooperate on first move
        return self.opponent_history[-1]

class TitForTwoTatStrategy(Strategy):
    """Only defects if opponent defects twice in a row"""
    def make_move(self):
        if len(self.opponent_history) < 2:
            return 'C'
        if self.opponent_history[-1] == 'D' and self.opponent_history[-2] == 'D':
            return 'D'
        return 'C'

class TwoTitForTatStrategy(Strategy):
    """Defects twice if opponent defects once"""
    def make_move(self):
        if not self.opponent_history:
            return 'C'
        if 'D' in self.opponent_history[-1:]:
            return 'D'
        return 'C'

class RandomStrategy(Strategy):
    """Randomly cooperates or defects"""
    def make_move(self):
        return random.choice(['C', 'D'])

class PavlovStrategy(Strategy):
    """Win-Stay, Lose-Shift strategy"""
    def make_move(self):
        if not self.opponent_history:
            return 'C'
        
        # If last round was a "win" (T or R payoff), repeat last move
        # Otherwise change move
        last_move = self.history[-1]
        last_opponent = self.opponent_history[-1]
        
        if (last_move == 'C' and last_opponent == 'C') or (last_move == 'D' and last_opponent == 'C'):
            return last_move  # Was good outcome, repeat
        else:
            return 'D' if last_move == 'C' else 'C'  # Switch strategy

class GrudgerStrategy(Strategy):
    """Cooperates until opponent defects, then always defects"""
    def make_move(self):
        if 'D' in self.opponent_history:
            return 'D'
        return 'C'

# Map of strategy names to their classes
STRATEGY_MAP = {
    'all_cooperate': AllCooperateStrategy,
    'all_defect': AllDefectStrategy,
    'tit_for_tat': TitForTatStrategy,
    'tit_for_2_tat': TitForTwoTatStrategy,
    '2_tit_for_tat': TwoTitForTatStrategy,
    'random': RandomStrategy,
    'pavlov': PavlovStrategy,
    'grudger': GrudgerStrategy
}

class PrisonersDilemmaSimulation:
    """Simulation for Prisoner's Dilemma games"""
    
    def __init__(self, config):
        self.config = config
        self.agents = []
        self.round = 0
        self.results = {
            'rounds': [],
            'scores': {},
            'strategy_performance': {},
            'overall_cooperation': 0,
            'overall_defection': 0
        }
        self.initialize_agents()
    
    def initialize_agents(self):
        """Create agents based on configuration"""
        self.agents = []
        
        for strategy_name, count in self.config['strategies'].items():
            if strategy_name in STRATEGY_MAP:
                for i in range(count):
                    agent_id = f"{strategy_name}_{i+1}"
                    self.agents.append({
                        'id': agent_id,
                        'strategy': STRATEGY_MAP[strategy_name](strategy_name),
                        'type': strategy_name
                    })
                    # Initialize score tracking in results
                    self.results['scores'][agent_id] = []
            else:
                logging.warning(f"Unknown strategy: {strategy_name}")
        
        # Initialize strategy performance tracking
        for strategy in STRATEGY_MAP.keys():
            self.results['strategy_performance'][strategy] = {
                'avg_score': 0,
                'total_cooperation': 0,
                'total_defection': 0
            }
    
    def run_round(self):
        """Run a single round of the simulation"""
        self.round += 1
        round_results = {'round': self.round, 'interactions': []}
        
        # For prisoner's dilemma, agents interact in pairs
        for agent1, agent2 in combinations(self.agents, 2):
            # Get moves from both agents
            move1 = agent1['strategy'].make_move()
            move2 = agent2['strategy'].make_move()
            
            # Calculate scores based on moves
            score1, score2 = self.calculate_score(move1, move2)
            
            # Record moves and scores for both agents
            agent1['strategy'].record_result(move1, move2, score1)
            agent2['strategy'].record_result(move2, move1, score2)
            
            # Track cooperation/defection for strategy performance
            self.track_strategy_stats(agent1['type'], move1)
            self.track_strategy_stats(agent2['type'], move2)
            
            # Overall stats
            if move1 == 'C':
                self.results['overall_cooperation'] += 1
            else:
                self.results['overall_defection'] += 1
                
            if move2 == 'C':
                self.results['overall_cooperation'] += 1
            else:
                self.results['overall_defection'] += 1
            
            # Record this interaction
            round_results['interactions'].append({
                'agent1': agent1['id'],
                'agent2': agent2['id'],
                'move1': move1,
                'move2': move2,
                'score1': score1,
                'score2': score2
            })
        
        # Record agent scores for this round
        for agent in self.agents:
            self.results['scores'][agent['id']].append(agent['strategy'].score)
        
        # Add round results to simulation results
        self.results['rounds'].append(round_results)
        
        return round_results
    
    def track_strategy_stats(self, strategy_type, move):
        """Track strategy performance statistics"""
        if move == 'C':
            self.results['strategy_performance'][strategy_type]['total_cooperation'] += 1
        else:
            self.results['strategy_performance'][strategy_type]['total_defection'] += 1
    
    def calculate_score(self, move1, move2):
        """Calculate scores for a pair of moves"""
        # Get custom payoff values from config if they exist, otherwise use defaults
        payoffs = self.config.get('payoffs', {})
        T = payoffs.get('T', DEFAULT_T)  # Temptation (defect while opponent cooperates)
        R = payoffs.get('R', DEFAULT_R)  # Reward (both cooperate)
        P = payoffs.get('P', DEFAULT_P)  # Punishment (both defect)
        S = payoffs.get('S', DEFAULT_S)  # Sucker (cooperate while opponent defects)
        
        if move1 == 'C' and move2 == 'C':
            return R, R  # Both cooperate: Reward
        elif move1 == 'C' and move2 == 'D':
            return S, T  # Player 1 cooperates, Player 2 defects: Sucker, Temptation
        elif move1 == 'D' and move2 == 'C':
            return T, S  # Player 1 defects, Player 2 cooperates: Temptation, Sucker
        else:  # Both defect
            return P, P  # Punishment
    
    def run_simulation(self, rounds=None):
        """Run the full simulation for specified number of rounds"""
        if rounds is None:
            rounds = self.config.get('rounds', 100)
        
        for _ in range(rounds):
            self.run_round()
        
        # Calculate final statistics
        self.calculate_final_stats()
        
        return self.results
    
    def calculate_final_stats(self):
        """Calculate final statistics for the simulation"""
        # Calculate average scores per strategy
        strategy_scores = {}
        for agent in self.agents:
            strategy = agent['type']
            if strategy not in strategy_scores:
                strategy_scores[strategy] = []
            strategy_scores[strategy].append(agent['strategy'].score)
        
        # Update strategy performance with average scores
        for strategy, scores in strategy_scores.items():
            self.results['strategy_performance'][strategy]['avg_score'] = np.mean(scores)
            
            # Calculate cooperation rate
            total_moves = (self.results['strategy_performance'][strategy]['total_cooperation'] + 
                          self.results['strategy_performance'][strategy]['total_defection'])
            
            if total_moves > 0:
                coop_rate = self.results['strategy_performance'][strategy]['total_cooperation'] / total_moves
                self.results['strategy_performance'][strategy]['cooperation_rate'] = coop_rate
            else:
                self.results['strategy_performance'][strategy]['cooperation_rate'] = 0
    
    def reset(self):
        """Reset the simulation to initial state"""
        self.round = 0
        self.results = {
            'rounds': [],
            'scores': {},
            'strategy_performance': {},
            'overall_cooperation': 0,
            'overall_defection': 0
        }
        
        # Reset all agents
        for agent in self.agents:
            agent['strategy'].reset()
        
        self.initialize_agents()

class UltimatumGameSimulation:
    """Simulation for Ultimatum Game"""
    
    def __init__(self, config):
        self.config = config
        self.agents = []
        self.round = 0
        self.results = {
            'rounds': [],
            'scores': {},
            'strategy_performance': {}
        }
        self.initialize_agents()
    
    def initialize_agents(self):
        """Initialize agents for ultimatum game"""
        # Implementation would be similar to PrisonersDilemma but with
        # different strategies specific to ultimatum game
        pass
        
    # Additional methods would be implemented similar to PrisonersDilemma
    # but adapted for Ultimatum Game rules

class GameOfChickenSimulation:
    """Simulation for Game of Chicken"""
    
    def __init__(self, config):
        self.config = config
        self.agents = []
        self.round = 0
        self.results = {
            'rounds': [],
            'scores': {},
            'strategy_performance': {}
        }
        self.initialize_agents()
    
    def initialize_agents(self):
        """Initialize agents for Game of Chicken"""
        # Implementation would be similar to PrisonersDilemma but with
        # different strategies specific to Game of Chicken
        pass
        
    # Additional methods would be implemented similar to PrisonersDilemma
    # but adapted for Game of Chicken rules

class SimulationFactory:
    """Factory class to create the appropriate simulation based on game type"""
    
    @staticmethod
    def create_simulation(config):
        game_type = config.get('game_type', 'prisoners_dilemma')
        
        if game_type == 'prisoners_dilemma':
            return PrisonersDilemmaSimulation(config)
        elif game_type == 'ultimatum_game':
            return UltimatumGameSimulation(config)
        elif game_type == 'game_of_chicken':
            return GameOfChickenSimulation(config)
        else:
            raise ValueError(f"Unknown game type: {game_type}")
