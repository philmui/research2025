// Main JavaScript for EvoGames - Mui Lab

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            html: true,
            container: 'body',
            trigger: 'hover focus'
        });
    });
    
    // Initialize toast component
    const toastEl = document.getElementById('notification-toast');
    const toast = new bootstrap.Toast(toastEl);
    
    // Strategy count inputs
    const strategyInputs = document.querySelectorAll('.strategy-count');
    const totalAgentsElement = document.getElementById('total-agents');
    
    // Configuration form
    const configForm = document.getElementById('config-form');
    const saveConfigBtn = document.getElementById('save-config-btn');
    const runSimulationBtn = document.getElementById('run-simulation-btn');
    
    // Saved configurations
    const savedConfigsList = document.getElementById('saved-configs');
    
    // Update total agents count when strategy counts change
    strategyInputs.forEach(input => {
        input.addEventListener('change', updateTotalAgents);
    });
    
    function updateTotalAgents() {
        let total = 0;
        strategyInputs.forEach(input => {
            total += parseInt(input.value) || 0;
        });
        totalAgentsElement.textContent = total;
    }
    
    // Save configuration button
    saveConfigBtn.addEventListener('click', function() {
        if (!validateForm()) return;
        
        const configData = collectFormData();
        
        // Send to backend
        fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(configData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Success', 'Configuration saved successfully!', 'success');
                // Refresh saved configs list
                fetchSavedConfigs();
            } else {
                showNotification('Error', data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error', 'Failed to save configuration', 'danger');
        });
    });
    
    // Run simulation button
    runSimulationBtn.addEventListener('click', function() {
        if (!validateForm()) return;
        
        const configData = collectFormData();
        
        // Update UI for simulation start
        document.getElementById('simulation-status').innerHTML = `
            <div class="d-flex justify-content-center">
                <div class="spinner-border text-primary me-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span>Running simulation...</span>
            </div>
        `;
        
        // Show simulation controls
        document.getElementById('simulation-controls').style.display = 'flex';
        
        // Run simulation
        fetch('/api/simulate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ config: configData })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Success', 'Simulation completed successfully!', 'success');
                // Process and display results
                displayResults(data.results, configData);
            } else {
                document.getElementById('simulation-status').innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Error: ${data.error}
                    </div>
                `;
                showNotification('Error', data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('simulation-status').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Error: Failed to run simulation
                </div>
            `;
            showNotification('Error', 'Failed to run simulation', 'danger');
        });
    });
    
    // Load configuration when clicked
    if (savedConfigsList) {
        savedConfigsList.addEventListener('click', function(e) {
            const configBtn = e.target.closest('[data-config-id]');
            if (configBtn) {
                const configId = configBtn.getAttribute('data-config-id');
                loadConfiguration(configId);
            }
        });
    }
    
    // Load saved configurations on page load
    fetchSavedConfigs();
    
    // Helper functions
    function validateForm() {
        // Check if name is provided
        const name = document.getElementById('config-name').value.trim();
        if (!name) {
            showNotification('Error', 'Please provide a configuration name', 'danger');
            return false;
        }
        
        // Check if at least 2 agents are specified
        let totalAgents = 0;
        strategyInputs.forEach(input => {
            totalAgents += parseInt(input.value) || 0;
        });
        
        if (totalAgents < 2) {
            showNotification('Error', 'At least 2 agents are required for the simulation', 'danger');
            return false;
        }
        
        return true;
    }
    
    function collectFormData() {
        const strategies = {};
        strategyInputs.forEach(input => {
            const count = parseInt(input.value) || 0;
            if (count > 0) {
                strategies[input.dataset.strategy] = count;
            }
        });
        
        // Get payoff values
        const payoffT = parseFloat(document.getElementById('payoff-t').value);
        const payoffR = parseFloat(document.getElementById('payoff-r').value);
        const payoffP = parseFloat(document.getElementById('payoff-p').value);
        const payoffS = parseFloat(document.getElementById('payoff-s').value);
        
        return {
            name: document.getElementById('config-name').value.trim(),
            description: document.getElementById('config-description').value.trim(),
            game_type: document.getElementById('game-type').value,
            rounds: parseInt(document.getElementById('rounds').value),
            strategies: strategies,
            payoffs: {
                T: payoffT,
                R: payoffR,
                P: payoffP,
                S: payoffS
            }
        };
    }
    
    function showNotification(title, message, type = 'primary') {
        document.getElementById('toast-title').textContent = title;
        document.getElementById('toast-message').textContent = message;
        
        // Set toast color based on type
        toastEl.className = 'toast';
        toastEl.classList.add(`bg-${type === 'danger' ? 'danger' : 'dark'}`);
        toastEl.classList.add(type === 'danger' ? 'text-white' : 'text-light');
        
        toast.show();
    }
    
    function fetchSavedConfigs() {
        fetch('/api/configs')
        .then(response => response.json())
        .then(data => {
            if (data.success && savedConfigsList) {
                if (data.configs.length === 0) {
                    savedConfigsList.innerHTML = `
                        <div class="text-center py-3">
                            <i class="fas fa-info-circle mb-2" style="font-size: 2rem;"></i>
                            <p class="mb-0">No saved configurations yet.</p>
                        </div>
                    `;
                } else {
                    savedConfigsList.innerHTML = data.configs.map(config => `
                        <button type="button" class="list-group-item list-group-item-action" 
                                data-config-id="${config.id}">
                            <div class="d-flex w-100 justify-content-between">
                                <h5 class="mb-1">${config.name}</h5>
                                <small>${config.game_type}</small>
                            </div>
                            <small class="text-muted">Created: ${new Date(config.created_at).toLocaleString()}</small>
                        </button>
                    `).join('');
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
    
    function loadConfiguration(configId) {
        fetch(`/api/config/${configId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const config = data.config;
                
                // Populate form with config data
                document.getElementById('config-name').value = config.name;
                document.getElementById('config-description').value = config.description || '';
                document.getElementById('game-type').value = config.game_type;
                document.getElementById('rounds').value = config.data.rounds;
                
                // Set payoff values if they exist in the config
                if (config.data.payoffs) {
                    document.getElementById('payoff-t').value = config.data.payoffs.T;
                    document.getElementById('payoff-r').value = config.data.payoffs.R;
                    document.getElementById('payoff-p').value = config.data.payoffs.P;
                    document.getElementById('payoff-s').value = config.data.payoffs.S;
                    updatePayoffMatrix();
                }
                
                // Reset all strategy counts
                strategyInputs.forEach(input => {
                    input.value = 0;
                });
                
                // Set strategy counts from config
                for (const [strategy, count] of Object.entries(config.data.strategies)) {
                    const input = document.querySelector(`.strategy-count[data-strategy="${strategy}"]`);
                    if (input) {
                        input.value = count;
                    }
                }
                
                // Update total agents
                updateTotalAgents();
                
                showNotification('Success', 'Configuration loaded successfully!', 'success');
            } else {
                showNotification('Error', data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error', 'Failed to load configuration', 'danger');
        });
    }
    
    // Update payoff matrix visualization when values change
    const payoffInputs = document.querySelectorAll('.payoff-value');
    payoffInputs.forEach(input => {
        input.addEventListener('change', updatePayoffMatrix);
    });
    
    function updatePayoffMatrix() {
        const T = document.getElementById('payoff-t').value;
        const R = document.getElementById('payoff-r').value;
        const P = document.getElementById('payoff-p').value;
        const S = document.getElementById('payoff-s').value;
        
        // Update the payoff matrix display
        document.getElementById('payoff-rr').innerHTML = `R,R (${R},${R})`;
        document.getElementById('payoff-st').innerHTML = `S,T (${S},${T})`;
        document.getElementById('payoff-ts').innerHTML = `T,S (${T},${S})`;
        document.getElementById('payoff-pp').innerHTML = `P,P (${P},${P})`;
        
        // Validate the payoff values (T > R > P > S)
        const errorEl = document.getElementById('payoff-error');
        if (!(parseFloat(T) > parseFloat(R) && parseFloat(R) > parseFloat(P) && parseFloat(P) > parseFloat(S))) {
            errorEl.style.display = 'block';
            errorEl.innerHTML = 'Warning: For a standard Prisoner\'s Dilemma, payoffs should satisfy: T > R > P > S';
        } else if (!(2 * parseFloat(R) > parseFloat(T) + parseFloat(S))) {
            errorEl.style.display = 'block';
            errorEl.innerHTML = 'Warning: For a standard Prisoner\'s Dilemma, payoffs should satisfy: 2R > T+S';
        } else {
            errorEl.style.display = 'none';
        }
    }
    
    // Initialize on page load
    updateTotalAgents();
    updatePayoffMatrix();
});
