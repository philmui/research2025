import os
import json
import logging
from datetime import datetime

def get_data_dir():
    """Get the data directory path"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir

def save_config(config_data, filename=None):
    """Save a configuration to a JSON file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"config_{timestamp}.json"
    
    filepath = os.path.join(get_data_dir(), filename)
    
    try:
        with open(filepath, 'w') as f:
            json.dump(config_data, f, indent=2)
        return {'success': True, 'filename': filename}
    except Exception as e:
        logging.error(f"Error saving configuration: {str(e)}")
        return {'success': False, 'error': str(e)}

def load_config(filename):
    """Load a configuration from a JSON file"""
    filepath = os.path.join(get_data_dir(), filename)
    
    try:
        if not os.path.exists(filepath):
            return {'success': False, 'error': 'File not found'}
        
        with open(filepath, 'r') as f:
            config_data = json.load(f)
        return {'success': True, 'data': config_data}
    except Exception as e:
        logging.error(f"Error loading configuration: {str(e)}")
        return {'success': False, 'error': str(e)}

def get_config_list():
    """Get a list of available configuration files"""
    data_dir = get_data_dir()
    configs = []
    
    try:
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(data_dir, filename)
                with open(filepath, 'r') as f:
                    config = json.load(f)
                
                configs.append({
                    'filename': filename,
                    'name': config.get('name', 'Unnamed'),
                    'game_type': config.get('game_type', 'Unknown'),
                    'created': datetime.fromtimestamp(os.path.getctime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return {'success': True, 'configs': configs}
    except Exception as e:
        logging.error(f"Error getting configuration list: {str(e)}")
        return {'success': False, 'error': str(e)}

def save_results(results, config_id=None, filename=None):
    """Save simulation results to a JSON file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"config_{config_id}_" if config_id else ""
        filename = f"{prefix}results_{timestamp}.json"
    
    filepath = os.path.join(get_data_dir(), filename)
    
    try:
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        return {'success': True, 'filename': filename}
    except Exception as e:
        logging.error(f"Error saving results: {str(e)}")
        return {'success': False, 'error': str(e)}

def load_results(filename):
    """Load simulation results from a JSON file"""
    filepath = os.path.join(get_data_dir(), filename)
    
    try:
        if not os.path.exists(filepath):
            return {'success': False, 'error': 'File not found'}
        
        with open(filepath, 'r') as f:
            results_data = json.load(f)
        return {'success': True, 'data': results_data}
    except Exception as e:
        logging.error(f"Error loading results: {str(e)}")
        return {'success': False, 'error': str(e)}

def get_results_list():
    """Get a list of available results files"""
    data_dir = get_data_dir()
    results_files = []
    
    try:
        for filename in os.listdir(data_dir):
            if filename.startswith('results_') and filename.endswith('.json'):
                filepath = os.path.join(data_dir, filename)
                results_files.append({
                    'filename': filename,
                    'created': datetime.fromtimestamp(os.path.getctime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return {'success': True, 'results': results_files}
    except Exception as e:
        logging.error(f"Error getting results list: {str(e)}")
        return {'success': False, 'error': str(e)}

def validate_config(config):
    """Validate a simulation configuration"""
    required_fields = ['name', 'game_type', 'rounds', 'strategies']
    
    # Check required fields
    for field in required_fields:
        if field not in config:
            return {'valid': False, 'error': f"Missing required field: {field}"}
    
    # Validate rounds
    try:
        rounds = int(config['rounds'])
        if rounds <= 0:
            return {'valid': False, 'error': "Rounds must be a positive integer"}
    except ValueError:
        return {'valid': False, 'error': "Rounds must be a number"}
    
    # Validate strategies
    if not isinstance(config['strategies'], dict):
        return {'valid': False, 'error': "Strategies must be an object mapping strategy names to counts"}
    
    from simulation import STRATEGY_MAP
    
    for strategy, count in config['strategies'].items():
        if strategy not in STRATEGY_MAP:
            return {'valid': False, 'error': f"Unknown strategy: {strategy}"}
        
        try:
            count = int(count)
            if count < 0:
                return {'valid': False, 'error': f"Strategy count must be non-negative: {strategy}"}
        except ValueError:
            return {'valid': False, 'error': f"Strategy count must be a number: {strategy}"}
    
    # Check if at least two agents are specified
    total_agents = sum(int(count) for count in config['strategies'].values())
    if total_agents < 2:
        return {'valid': False, 'error': "At least 2 agents are required for simulation"}
    
    return {'valid': True}
