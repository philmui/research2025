// Simulation Controller for EvoGames - Mui Lab

let currentSimulation = null;
let simulationInterval = null;
let currentRound = 0;
let totalRounds = 0;
let simulationConfig = null;
let simulationResults = null;
let simulationSpeed = 500; // ms between rounds

// Initialize simulation controller
function initializeSimulationController() {
    // Simulation control buttons
    const pauseBtn = document.getElementById('pause-btn');
    const stopBtn = document.getElementById('stop-btn');
    const stepBtn = document.getElementById('step-btn');
    
    // Hide simulation controls initially
    document.getElementById('simulation-controls').style.display = 'none';
    
    // Add event listeners to control buttons
    if (pauseBtn) {
        pauseBtn.addEventListener('click', togglePause);
    }
    
    if (stopBtn) {
        stopBtn.addEventListener('click', stopSimulation);
    }
    
    if (stepBtn) {
        stepBtn.addEventListener('click', stepSimulation);
    }
}

// Display simulation results
function displayResults(results, config) {
    // Store results and config
    simulationResults = results;
    simulationConfig = config;
    totalRounds = results.rounds.length;
    currentRound = totalRounds; // Start with all rounds completed
    
    // Update charts with results
    updateCharts(results, config);
    
    // Show round information
    const roundInfo = document.getElementById('round-info');
    if (roundInfo) {
        roundInfo.style.display = 'block';
        document.getElementById('current-round').textContent = totalRounds;
        document.getElementById('total-rounds').textContent = totalRounds;
        
        // Update progress bar
        const progress = (currentRound / totalRounds) * 100;
        const progressBar = document.getElementById('round-progress');
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        progressBar.textContent = `${Math.round(progress)}%`;
    }
    
    // Show interactions
    updateInteractionsTable(results.rounds[totalRounds - 1]);
    document.getElementById('interactions-card').style.display = 'block';
    
    // Show detailed results
    updateDetailedResults();
    document.getElementById('detailed-results').style.display = 'block';
    
    // Update simulation status
    document.getElementById('simulation-status').innerHTML = `
        <div class="alert alert-success">
            <i class="fas fa-check-circle me-2"></i>
            Simulation completed successfully with ${totalRounds} rounds!
        </div>
    `;
    
    // Hide simulation controls
    document.getElementById('simulation-controls').style.display = 'none';
}

// Update the interactions table
function updateInteractionsTable(roundData) {
    const tableBody = document.getElementById('interactions-table-body');
    if (!tableBody || !roundData || !roundData.interactions) return;
    
    tableBody.innerHTML = '';
    
    // Add interactions to the table
    roundData.interactions.forEach(interaction => {
        const row = document.createElement('tr');
        
        // Format agent IDs to show only strategy type and number
        const agent1Parts = interaction.agent1.split('_');
        const agent2Parts = interaction.agent2.split('_');
        const agent1Display = `${formatStrategyName(agent1Parts.slice(0, -1).join('_'))} ${agent1Parts.slice(-1)}`;
        const agent2Display = `${formatStrategyName(agent2Parts.slice(0, -1).join('_'))} ${agent2Parts.slice(-1)}`;
        
        row.innerHTML = `
            <td>${agent1Display}</td>
            <td class="move-cell ${interaction.move1 === 'C' ? 'cooperate' : 'defect'}">
                ${interaction.move1 === 'C' ? 'C' : 'D'}
            </td>
            <td>${agent2Display}</td>
            <td class="move-cell ${interaction.move2 === 'C' ? 'cooperate' : 'defect'}">
                ${interaction.move2 === 'C' ? 'C' : 'D'}
            </td>
            <td>${interaction.score1} / ${interaction.score2}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Update detailed results table
function updateDetailedResults() {
    const tableBody = document.getElementById('results-table-body');
    if (!tableBody || !simulationResults) return;
    
    tableBody.innerHTML = '';
    
    // Get strategy performance data
    const strategies = Object.keys(simulationResults.strategy_performance);
    
    // Sort strategies by average score (descending)
    strategies.sort((a, b) => {
        return simulationResults.strategy_performance[b].avg_score - 
               simulationResults.strategy_performance[a].avg_score;
    });
    
    // Add rows for each strategy
    strategies.forEach((strategy, index) => {
        const perfData = simulationResults.strategy_performance[strategy];
        const row = document.createElement('tr');
        
        // Highlight top and bottom performers
        if (index === 0) row.classList.add('top-score');
        if (index === strategies.length - 1) row.classList.add('bottom-score');
        
        const totalMoves = perfData.total_cooperation + perfData.total_defection;
        const cooperationRate = totalMoves > 0 ? 
            (perfData.total_cooperation / totalMoves * 100).toFixed(1) + '%' : 'N/A';
        
        row.innerHTML = `
            <td>${formatStrategyName(strategy)}</td>
            <td>${perfData.avg_score.toFixed(2)}</td>
            <td>${cooperationRate}</td>
            <td>${totalMoves}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Toggle pause/resume simulation
function togglePause() {
    const pauseBtn = document.getElementById('pause-btn');
    
    if (simulationInterval) {
        // Currently running, pause it
        clearInterval(simulationInterval);
        simulationInterval = null;
        pauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        pauseBtn.classList.replace('btn-primary', 'btn-success');
    } else {
        // Currently paused, resume it
        runSimulationAnimation();
        pauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
        pauseBtn.classList.replace('btn-success', 'btn-primary');
    }
}

// Stop simulation
function stopSimulation() {
    if (simulationInterval) {
        clearInterval(simulationInterval);
        simulationInterval = null;
    }
    
    // Reset to final state
    currentRound = totalRounds;
    
    // Update UI
    document.getElementById('current-round').textContent = totalRounds;
    
    // Update progress bar
    const progress = 100;
    const progressBar = document.getElementById('round-progress');
    progressBar.style.width = `${progress}%`;
    progressBar.setAttribute('aria-valuenow', progress);
    progressBar.textContent = `${Math.round(progress)}%`;
    
    // Update charts with complete results
    updateCharts(simulationResults, simulationConfig);
    
    // Show final round interactions
    updateInteractionsTable(simulationResults.rounds[totalRounds - 1]);
    
    // Reset pause button
    const pauseBtn = document.getElementById('pause-btn');
    pauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
    pauseBtn.classList.replace('btn-success', 'btn-primary');
}

// Step through simulation one round at a time
function stepSimulation() {
    if (currentRound < totalRounds) {
        currentRound++;
        updateSimulationUI();
    }
}

// Run simulation animation
function runSimulationAnimation() {
    // Reset to beginning
    currentRound = 0;
    
    // Start interval
    simulationInterval = setInterval(() => {
        currentRound++;
        
        // Update UI
        updateSimulationUI();
        
        // Check if simulation is complete
        if (currentRound >= totalRounds) {
            clearInterval(simulationInterval);
            simulationInterval = null;
            
            // Reset pause button
            const pauseBtn = document.getElementById('pause-btn');
            pauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
            pauseBtn.classList.replace('btn-success', 'btn-primary');
        }
    }, simulationSpeed);
}

// Update simulation UI based on current round
function updateSimulationUI() {
    // Update round counter
    document.getElementById('current-round').textContent = currentRound;
    
    // Update progress bar
    const progress = (currentRound / totalRounds) * 100;
    const progressBar = document.getElementById('round-progress');
    progressBar.style.width = `${progress}%`;
    progressBar.setAttribute('aria-valuenow', progress);
    progressBar.textContent = `${Math.round(progress)}%`;
    
    // Update interactions table for current round
    updateInteractionsTable(simulationResults.rounds[currentRound - 1]);
    
    // Create partial results for chart animation
    const partialResults = {
        rounds: simulationResults.rounds.slice(0, currentRound),
        scores: {},
        strategy_performance: simulationResults.strategy_performance,
        overall_cooperation: 0,
        overall_defection: 0
    };
    
    // Partial scores
    for (const agentId in simulationResults.scores) {
        partialResults.scores[agentId] = simulationResults.scores[agentId].slice(0, currentRound);
    }
    
    // Calculate partial cooperation/defection totals
    for (let i = 0; i < currentRound; i++) {
        const round = simulationResults.rounds[i];
        round.interactions.forEach(interaction => {
            if (interaction.move1 === 'C') partialResults.overall_cooperation++;
            else partialResults.overall_defection++;
            
            if (interaction.move2 === 'C') partialResults.overall_cooperation++;
            else partialResults.overall_defection++;
        });
    }
    
    // Update charts with partial results
    updateCharts(partialResults, simulationConfig);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initializeSimulationController);
