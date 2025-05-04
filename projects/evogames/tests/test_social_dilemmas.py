"""
Unit tests for social dilemmas simulation module.

These tests verify the correctness of the social dilemma simulations
and ensure that agent strategies behave as expected.
"""

import unittest
import json
import os
import sys

# Add the parent directory to sys.path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from social_dilemmas import (
    SocialDilemmaFactory, TragedyOfCommonsSimulation, FreeRiderSimulation, 
    PublicGoodsSimulation, SustainableHarvester, GreedyHarvester,
    AdaptiveHarvester, FairShareHarvester, ConsistentContributor,
    FreeRider, PartialContributor, ConditionalContributor
)

class TestTragedyOfCommons(unittest.TestCase):
    """Test cases for Tragedy of the Commons simulation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'dilemma_type': 'tragedy_commons',
            'rounds': 10,
            'strategies': {
                'sustainable': 2,
                'greedy': 2,
                'adaptive': 2,
                'fair_share': 2
            },
            'parameters': {
                'resource_size': 1000,
                'regeneration_rate': 5,
                'harvest_limit': 30
            }
        }
        self.simulation = TragedyOfCommonsSimulation(self.config)
    
    def test_initialization(self):
        """Test that simulation initializes correctly."""
        self.assertEqual(len(self.simulation.agents), 8)
        self.assertEqual(self.simulation.resource_size, 1000)
        self.assertEqual(self.simulation.regeneration_rate, 0.05)
        self.assertEqual(self.simulation.harvest_limit, 30)
    
    def test_run_simulation(self):
        """Test that simulation runs for the specified number of rounds."""
        results = self.simulation.run_simulation()
        
        # Check rounds
        self.assertEqual(self.simulation.round, 10)
        self.assertEqual(len(results['rounds']), 10)
        
        # Check resource level tracking
        self.assertEqual(len(results['resource_levels']), 11)  # Initial + 10 rounds
        
        # Check strategy performance statistics
        self.assertTrue('strategy_performance' in results)
        self.assertTrue('sustainable' in results['strategy_performance'])
        self.assertTrue('greedy' in results['strategy_performance'])
        self.assertTrue('adaptive' in results['strategy_performance'])
        self.assertTrue('fair_share' in results['strategy_performance'])
    
    def test_harvester_behaviors(self):
        """Test that harvesters behave according to their strategies."""
        # Create and test individual harvesters
        sustainable = SustainableHarvester(1, 30)
        greedy = GreedyHarvester(2, 30)
        fair_share = FairShareHarvester(3, 30)
        
        # At full resource health
        self.assertLessEqual(sustainable.decide_harvest(1000, 1000, 30), 30)
        self.assertGreater(greedy.decide_harvest(1000, 1000, 30), 30)
        self.assertEqual(fair_share.decide_harvest(1000, 1000, 30), 30)
        
        # At depleted resource health
        self.assertLess(sustainable.decide_harvest(200, 1000, 30), 30)


class TestFreeRiderProblem(unittest.TestCase):
    """Test cases for Free Rider Problem simulation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'dilemma_type': 'free_rider',
            'rounds': 10,
            'strategies': {
                'contributor': 2,
                'free_rider': 2,
                'partial': 2,
                'conditional': 2
            },
            'parameters': {
                'project_cost': 1000,
                'benefit_multiplier': 2,
                'threshold': 75
            }
        }
        self.simulation = FreeRiderSimulation(self.config)
    
    def test_initialization(self):
        """Test that simulation initializes correctly."""
        self.assertEqual(len(self.simulation.agents), 8)
        self.assertEqual(self.simulation.project_cost, 1000)
        self.assertEqual(self.simulation.benefit_multiplier, 2)
        self.assertEqual(self.simulation.threshold, 750)
    
    def test_contributor_behaviors(self):
        """Test that contributors behave according to their strategies."""
        fair_share = 100  # Assuming 1000 cost / 10 agents
        
        # Test consistent contributor
        contributor = ConsistentContributor(1, fair_share)
        self.assertEqual(contributor.decide_contribution(0, 1000, 750, 50), fair_share)
        
        # Test free rider
        free_rider = FreeRider(2, fair_share)
        self.assertEqual(free_rider.decide_contribution(0, 1000, 750, 50), 0)
        
        # Test partial contributor
        partial = PartialContributor(3, fair_share)
        contribution = partial.decide_contribution(0, 1000, 750, 50)
        self.assertGreater(contribution, 0)
        self.assertLess(contribution, fair_share)
        
        # Test conditional contributor first round (should be fair share)
        conditional = ConditionalContributor(4, fair_share)
        self.assertEqual(conditional.decide_contribution(0, 1000, 750, 0), fair_share)


class TestPublicGoodsDilemma(unittest.TestCase):
    """Test cases for Public Goods Dilemma simulation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'dilemma_type': 'public_goods',
            'rounds': 10,
            'strategies': {
                'full': 2,
                'zero': 2,
                'random': 2,
                'matching': 2
            },
            'parameters': {
                'endowment': 50,
                'multiplier': 2,
                'distribution': 'equal'
            }
        }
        self.simulation = PublicGoodsSimulation(self.config)
    
    def test_initialization(self):
        """Test that simulation initializes correctly."""
        self.assertEqual(len(self.simulation.agents), 8)
        self.assertEqual(self.simulation.endowment, 50)
        self.assertEqual(self.simulation.multiplier, 2)
        self.assertEqual(self.simulation.distribution, 'equal')
    
    def test_run_round(self):
        """Test that a round runs correctly."""
        round_data = self.simulation.run_round()
        
        # Check that round data has expected structure
        self.assertEqual(round_data['round'], 1)
        self.assertTrue('contributions' in round_data)
        self.assertTrue('payoffs' in round_data)
        
        # Check that contributions were recorded
        self.assertEqual(len(round_data['contributions']), 8)
        self.assertEqual(len(round_data['payoffs']), 8)


class TestSocialDilemmaFactory(unittest.TestCase):
    """Test cases for SocialDilemmaFactory."""
    
    def test_create_tragedy_commons(self):
        """Test creation of Tragedy of Commons simulation."""
        config = {'dilemma_type': 'tragedy_commons'}
        simulation = SocialDilemmaFactory.create_simulation(config)
        self.assertIsInstance(simulation, TragedyOfCommonsSimulation)
    
    def test_create_free_rider(self):
        """Test creation of Free Rider simulation."""
        config = {'dilemma_type': 'free_rider'}
        simulation = SocialDilemmaFactory.create_simulation(config)
        self.assertIsInstance(simulation, FreeRiderSimulation)
    
    def test_create_public_goods(self):
        """Test creation of Public Goods simulation."""
        config = {'dilemma_type': 'public_goods'}
        simulation = SocialDilemmaFactory.create_simulation(config)
        self.assertIsInstance(simulation, PublicGoodsSimulation)
    
    def test_invalid_type(self):
        """Test that invalid dilemma type raises ValueError."""
        config = {'dilemma_type': 'invalid_type'}
        with self.assertRaises(ValueError):
            SocialDilemmaFactory.create_simulation(config)


if __name__ == '__main__':
    unittest.main()