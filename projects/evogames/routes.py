from flask import render_template, request, jsonify, redirect, url_for, flash, session
import json
import os
import time
from app import app, db
from models import Configuration, SimulationResult
from simulation import SimulationFactory, STRATEGY_MAP
from social_dilemmas import SocialDilemmaFactory
from utils import (
    save_config, load_config, get_config_list, 
    save_results, load_results, get_results_list,
    validate_config
)

@app.route('/')
def index():
    """Render the main page"""
    # Get a list of available strategies
    strategies = list(STRATEGY_MAP.keys())
    
    # Get a list of saved configurations
    configs_response = get_config_list()
    configs = configs_response.get('configs', []) if configs_response.get('success', False) else []
    
    # Define detailed strategy descriptions for tooltips
    strategy_descriptions = {
        'all_cooperate': """
            <strong>Always Cooperate</strong><br>
            This strategy always chooses to cooperate regardless of what the opponent does.<br><br>
            <strong>Behavior:</strong> Always plays C (cooperate).<br>
            <strong>Strengths:</strong> Works well in environments with many cooperative agents.<br>
            <strong>Weaknesses:</strong> Very vulnerable to exploitation by defectors.
        """,
        'all_defect': """
            <strong>Always Defect</strong><br>
            This strategy always chooses to defect regardless of what the opponent does.<br><br>
            <strong>Behavior:</strong> Always plays D (defect).<br>
            <strong>Strengths:</strong> Cannot be exploited, and maximizes gain against cooperators.<br>
            <strong>Weaknesses:</strong> Performs poorly against other defectors and strategies that retaliate.
        """,
        'tit_for_tat': """
            <strong>Tit for Tat</strong><br>
            Cooperates on first move, then copies opponent's previous move. This strategy won Axelrod's famous tournament.<br><br>
            <strong>Behavior:</strong> Starts with C, then mirrors what opponent did in previous round.<br>
            <strong>Strengths:</strong> Simple, robust, and forgiving. Rewards cooperation while punishing defection.<br>
            <strong>Weaknesses:</strong> Can get stuck in bad cycles after noise/mistakes.
        """,
        'tit_for_2_tat': """
            <strong>Tit for 2 Tat</strong><br>
            More forgiving version of Tit for Tat. Only defects if opponent defects twice in a row.<br><br>
            <strong>Behavior:</strong> Starts with C, defects only after two consecutive defections from opponent.<br>
            <strong>Strengths:</strong> Very forgiving, robust against occasional defection.<br>
            <strong>Weaknesses:</strong> Can be exploited by strategies that alternate cooperation and defection.
        """,
        '2_tit_for_tat': """
            <strong>2 Tit for Tat</strong><br>
            More punishing version of Tit for Tat. Defects twice after opponent defects once.<br><br>
            <strong>Behavior:</strong> Starts with C, retaliates with two Ds after opponent defects.<br>
            <strong>Strengths:</strong> Strongly discourages defection with double punishment.<br>
            <strong>Weaknesses:</strong> Not forgiving, can trigger long defection cycles.
        """,
        'random': """
            <strong>Random</strong><br>
            Randomly chooses to cooperate or defect with equal probability.<br><br>
            <strong>Behavior:</strong> 50% chance to play C or D each round.<br>
            <strong>Strengths:</strong> Unpredictable, cannot be exploited by pattern recognition.<br>
            <strong>Weaknesses:</strong> Sub-optimal performance since it has no strategy.
        """,
        'pavlov': """
            <strong>Pavlov (Win-Stay, Lose-Shift)</strong><br>
            Changes move if previous outcome was poor, repeats move if previous outcome was good.<br><br>
            <strong>Behavior:</strong> Starts with C. If it got a good outcome (CC or DC), repeats last move. If it got bad outcome (CD or DD), switches.<br> 
            <strong>Strengths:</strong> Performs well in evolving populations, can establish cooperation after mutual defection.<br>
            <strong>Weaknesses:</strong> Can be exploited by consistent defectors.
        """,
        'grudger': """
            <strong>Grudger (Grim Trigger)</strong><br>
            Cooperates until opponent defects, then always defects forever.<br><br>
            <strong>Behavior:</strong> Starts with C, switches to all D permanently after first defection by opponent.<br>
            <strong>Strengths:</strong> Cannot be exploited more than once.<br>
            <strong>Weaknesses:</strong> Extremely unforgiving, never recovers cooperation after a single defection.
        """
    }
    
    return render_template('index.html', 
                          strategies=strategies, 
                          configs=configs,
                          strategy_descriptions=strategy_descriptions,
                          game_types=['prisoners_dilemma', 'ultimatum_game', 'game_of_chicken'])

@app.route('/about')
def about():
    """Render the about page with information about game theory"""
    return render_template('about.html')

@app.route('/social-dilemmas')
def social_dilemmas():
    """Render the social dilemmas simulation page"""
    # Check if a specific dilemma was requested
    dilemma_type = request.args.get('dilemma', None)
    return render_template('social_dilemmas.html', dilemma_type=dilemma_type)

@app.route('/real-world-examples')
def real_world_examples():
    """Render the real-world examples page with visualizations"""
    return render_template('real_world_examples.html')

@app.route('/api/config', methods=['POST'])
def create_config():
    """Create a new configuration"""
    data = request.json
    
    # Validate configuration
    validation = validate_config(data)
    if not validation['valid']:
        return jsonify({'success': False, 'error': validation['error']}), 400
    
    # Save to database
    config = Configuration(
        name=data['name'],
        description=data.get('description', ''),
        game_type=data['game_type'],
        config_data=json.dumps(data)
    )
    
    try:
        db.session.add(config)
        db.session.commit()
        
        # Also save to file
        result = save_config(data, f"config_{config.id}.json")
        if not result['success']:
            return jsonify({'success': False, 'error': result['error']}), 500
        
        return jsonify({'success': True, 'config_id': config.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config/<int:config_id>', methods=['GET'])
def get_config(config_id):
    """Get a configuration by ID"""
    config = Configuration.query.get(config_id)
    
    if not config:
        return jsonify({'success': False, 'error': 'Configuration not found'}), 404
    
    return jsonify({
        'success': True,
        'config': {
            'id': config.id,
            'name': config.name,
            'description': config.description,
            'game_type': config.game_type,
            'data': json.loads(config.config_data),
            'created_at': config.created_at.isoformat()
        }
    })

@app.route('/api/config/<int:config_id>', methods=['PUT'])
def update_config(config_id):
    """Update an existing configuration"""
    config = Configuration.query.get(config_id)
    
    if not config:
        return jsonify({'success': False, 'error': 'Configuration not found'}), 404
    
    data = request.json
    
    # Validate configuration
    validation = validate_config(data)
    if not validation['valid']:
        return jsonify({'success': False, 'error': validation['error']}), 400
    
    try:
        config.name = data['name']
        config.description = data.get('description', '')
        config.game_type = data['game_type']
        config.config_data = json.dumps(data)
        
        db.session.commit()
        
        # Also update file
        result = save_config(data, f"config_{config.id}.json")
        if not result['success']:
            return jsonify({'success': False, 'error': result['error']}), 500
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/configs', methods=['GET'])
def list_configs():
    """List all saved configurations"""
    configs = Configuration.query.all()
    
    return jsonify({
        'success': True,
        'configs': [{
            'id': config.id,
            'name': config.name,
            'game_type': config.game_type,
            'created_at': config.created_at.isoformat()
        } for config in configs]
    })

@app.route('/api/simulate', methods=['POST'])
def run_simulation():
    """Run a simulation with the provided configuration"""
    data = request.json
    
    # Check if using saved config or new config
    if 'config_id' in data:
        config = Configuration.query.get(data['config_id'])
        if not config:
            return jsonify({'success': False, 'error': 'Configuration not found'}), 404
        
        config_data = json.loads(config.config_data)
    else:
        config_data = data.get('config')
        
        # Validate configuration
        validation = validate_config(config_data)
        if not validation['valid']:
            return jsonify({'success': False, 'error': validation['error']}), 400
    
    # Get number of rounds
    rounds = data.get('rounds', config_data.get('rounds', 100))
    
    try:
        # Create and run simulation
        simulation = SimulationFactory.create_simulation(config_data)
        results = simulation.run_simulation(rounds=rounds)
        
        # Save results
        if 'config_id' in data:
            result_obj = SimulationResult(
                configuration_id=data['config_id'],
                result_data=json.dumps(results),
                stats_summary=json.dumps(results['strategy_performance'])
            )
            db.session.add(result_obj)
            db.session.commit()
            
            # Also save to file
            save_results(results, config_id=data['config_id'])
        else:
            save_results(results)
        
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/results/<int:config_id>', methods=['GET'])
def get_results(config_id):
    """Get results for a specific configuration"""
    results = SimulationResult.query.filter_by(configuration_id=config_id).all()
    
    if not results:
        return jsonify({'success': False, 'error': 'No results found for this configuration'}), 404
    
    return jsonify({
        'success': True,
        'results': [{
            'id': result.id,
            'created_at': result.created_at.isoformat(),
            'data': json.loads(result.result_data),
            'summary': json.loads(result.stats_summary)
        } for result in results]
    })

@app.route('/api/social-dilemma/config', methods=['POST'])
def create_social_dilemma_config():
    """Create a new social dilemma configuration"""
    data = request.json
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({'success': False, 'error': 'Configuration name is required'}), 400
    
    if not data.get('dilemma_type'):
        return jsonify({'success': False, 'error': 'Dilemma type is required'}), 400
    
    if not data.get('strategies') or not isinstance(data['strategies'], dict):
        return jsonify({'success': False, 'error': 'At least one strategy must be specified'}), 400
    
    # Save to file
    filename = f"social_dilemma_{data['dilemma_type']}_{int(time.time())}.json"
    try:
        # Ensure directory exists
        os.makedirs('data', exist_ok=True)
        
        # Save to file
        with open(os.path.join('data', filename), 'w') as f:
            json.dump(data, f, indent=2)
        
        return jsonify({'success': True, 'filename': filename}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/social-dilemma/simulate', methods=['POST'])
def run_social_dilemma_simulation():
    """Run a social dilemma simulation with the provided configuration"""
    # Support both JSON and form data
    if request.is_json:
        data = request.json
        if not data.get('config'):
            return jsonify({'success': False, 'error': 'Configuration is required'}), 400
        config_data = data['config']
    else:
        # Handle form data
        config_json = request.form.get('config')
        if not config_json:
            return jsonify({'success': False, 'error': 'Configuration is required'}), 400
        try:
            config_data = json.loads(config_json)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Invalid JSON in config: {str(e)}'}), 400
    
    # Get number of rounds
    rounds = config_data.get('rounds', 50)
    
    try:
        # Create and run simulation
        simulation = SocialDilemmaFactory.create_simulation(config_data)
        results = simulation.run_simulation(rounds=rounds)
        
        # Save results to file
        filename = f"social_dilemma_results_{config_data['dilemma_type']}_{int(time.time())}.json"
        os.makedirs('data', exist_ok=True)
        with open(os.path.join('data', filename), 'w') as f:
            json.dump(results, f, indent=2)
        
        # Check if request wants JSON or redirect
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'results': results, 'filename': filename})
        else:
            # For form submissions, redirect to a results page with the data in session
            session['simulation_results'] = results
            session['simulation_config'] = config_data
            # Flash a success message
            flash('Simulation completed successfully!', 'success')
            return redirect(url_for('social_dilemmas', _anchor='results'))
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': error_msg}), 500
        else:
            # For form submissions, redirect back with an error
            flash(f'Error running simulation: {error_msg}', 'danger')
            return redirect(url_for('social_dilemmas'))
