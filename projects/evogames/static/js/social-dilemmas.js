// Social Dilemmas Simulation JavaScript
//
// @author: Theodore Mui
// @version: 1.0
// @since: 2025-05-03
//

// Make sure Bootstrap is loaded before initializing
function ensureBootstrap(callback) {
    if (typeof bootstrap !== 'undefined') {
        // Bootstrap is already loaded
        console.log("Bootstrap is loaded, initializing page...");
        callback();
    } else {
        // Wait a bit and try again
        console.log("Waiting for Bootstrap to load...");
        setTimeout(function() {
            ensureBootstrap(callback);
        }, 100);
    }
}

// This will run when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM content loaded, checking for Bootstrap...");
    // Wait for Bootstrap to be available
    ensureBootstrap(initializePage);
});

// Main initialization function that will run when Bootstrap is ready
function initializePage() {
    console.log("Initializing page with Bootstrap loaded...");
    // Get URL parameter for dilemma if present
    const urlParams = new URLSearchParams(window.location.search);
    const dilemmaParam = urlParams.get('dilemma');
    
    // Set initial dilemma type based on URL parameter if present
    if (dilemmaParam && ['tragedy_commons', 'free_rider', 'public_goods'].includes(dilemmaParam)) {
        const dilemmaTypeSelect = document.getElementById('dilemma-type');
        if (dilemmaTypeSelect) {
            dilemmaTypeSelect.value = dilemmaParam;
            // Trigger change event to update UI
            const event = new Event('change');
            dilemmaTypeSelect.dispatchEvent(event);
        }
    }
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            html: true,
            container: 'body',
            trigger: 'hover focus'
        });
    });
    
    // Initialize toast component with error handling
    const toastEl = document.getElementById('notification-toast');
    let toast;
    try {
        toast = new bootstrap.Toast(toastEl);
    } catch (e) {
        console.error("Toast initialization error:", e);
        // Create a fallback notification function if toast fails
        window.showNotificationFallback = function(title, message) {
            alert(title + ": " + message);
        }
    }
    
    // Configure dilemma type selector to show appropriate config panel
    const dilemmaType = document.getElementById('dilemma-type');
    const configs = document.querySelectorAll('.dilemma-config');
    
    // Function to show the appropriate configuration panel
    function showSelectedDilemmaConfig() {
        try {
            const selectedValue = dilemmaType.value;
            console.log(`Showing config for: ${selectedValue}`);
            
            // Hide all config panels first using class selector
            document.querySelectorAll('.dilemma-config').forEach(panel => {
                panel.style.display = 'none';
                console.log(`Hidden config panel: ${panel.id}`);
            });
            
            // Show selected panel - convert underscore to hyphen for HTML ID
            const configId = selectedValue.replace(/_/g, '-') + '-config';
            const selectedConfig = document.getElementById(configId);
            
            console.log(`Looking for config panel with ID: ${configId}`);
            
            if (selectedConfig) {
                selectedConfig.style.display = 'block';
                console.log(`Displayed config panel: ${selectedConfig.id}`);
            } else {
                console.error(`Config panel not found for ID: ${configId}`);
                
                // Debugging - list all available panels
                console.log("Available panels:");
                document.querySelectorAll('.dilemma-config').forEach(panel => {
                    console.log(`- ${panel.id}`);
                });
            }
            
            // Update agent counts based on visible panel
            updateDilemmaTotalAgents();
        } catch (e) {
            console.error("Error showing dilemma config:", e);
        }
    }
    
    // Initialize the correct panel on page load
    showSelectedDilemmaConfig();
    
    // Add change event listener
    dilemmaType.addEventListener('change', showSelectedDilemmaConfig);
    
    // Update total agents for each dilemma type
    function updateDilemmaTotalAgents() {
        console.log("Updating total agent counts for all dilemma types");
        
        // For Tragedy of Commons
        const tcInputs = document.querySelectorAll('#tragedy-commons-config .social-strategy-count');
        let tcTotal = 0;
        tcInputs.forEach(input => {
            tcTotal += parseInt(input.value) || 0;
        });
        console.log(`Tragedy Commons total agents: ${tcTotal}`);
        
        // Generic method to show total - may be shared between dilemmas
        let totalElement = document.getElementById('dilemma-total-agents');
        if (totalElement) totalElement.textContent = tcTotal;
        
        // Specific total element for this dilemma
        let specificTcTotal = document.getElementById('tc-total-agents');
        if (specificTcTotal) specificTcTotal.textContent = tcTotal;
        
        // For Free Rider
        const frInputs = document.querySelectorAll('#free-rider-config .social-strategy-count');
        let frTotal = 0;
        frInputs.forEach(input => {
            frTotal += parseInt(input.value) || 0;
        });
        console.log(`Free Rider total agents: ${frTotal}`);
        
        const frTotalElement = document.getElementById('fr-total-agents');
        if (frTotalElement) frTotalElement.textContent = frTotal;
        
        // For Public Goods
        const pgInputs = document.querySelectorAll('#public-goods-config .social-strategy-count');
        let pgTotal = 0;
        pgInputs.forEach(input => {
            pgTotal += parseInt(input.value) || 0;
        });
        console.log(`Public Goods total agents: ${pgTotal}`);
        
        const pgTotalElement = document.getElementById('pg-total-agents');
        if (pgTotalElement) pgTotalElement.textContent = pgTotal;
        
        // Update generic total based on current selection
        const currentDilemma = document.getElementById('dilemma-type').value;
        if (currentDilemma === 'tragedy_commons' && totalElement) {
            totalElement.textContent = tcTotal;
        } else if (currentDilemma === 'free_rider' && totalElement) {
            totalElement.textContent = frTotal;
        } else if (currentDilemma === 'public_goods' && totalElement) {
            totalElement.textContent = pgTotal;
        }
    }
    
    // Add event listeners to all agent count inputs
    const strategyInputs = document.querySelectorAll('.social-strategy-count');
    strategyInputs.forEach(input => {
        input.addEventListener('change', updateDilemmaTotalAgents);
    });
    
    // Save configuration button
    const saveBtn = document.getElementById('save-dilemma-btn');
    saveBtn.addEventListener('click', function() {
        if (!validateForm()) return;
        
        const configData = collectFormData();
        
        // Send to backend
        fetch('/api/social-dilemma/config', {
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
            } else {
                showNotification('Error', data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error', 'Failed to save configuration', 'danger');
        });
    });
    
    // Run simulation button with simpler direct implementation
    const runBtn = document.getElementById('run-dilemma-btn');
    if (runBtn) {
        runBtn.addEventListener('click', function(e) {
            console.log("Run simulation button clicked");
            e.preventDefault(); // Prevent default in case this is inside a form
            
            if (!validateForm()) {
                console.log("Form validation failed");
                return;
            }
            
            try {
                const configData = collectFormData();
                console.log("Config data collected:", configData);
                
                // Update UI for simulation start
                const statusElement = document.getElementById('dilemma-status');
                if (statusElement) {
                    statusElement.innerHTML = `
                        <div class="d-flex justify-content-center">
                            <div class="spinner-border text-primary me-2" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <span>Running simulation...</span>
                        </div>
                    `;
                }
                
                // Show simulation controls if they exist
                const controlsElement = document.getElementById('dilemma-controls');
                if (controlsElement) {
                    controlsElement.style.display = 'flex';
                }
                
                // Create a simple form submission instead of fetch
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = '/api/social-dilemma/simulate';
                form.style.display = 'none';
                
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'config';
                input.value = JSON.stringify(configData);
                form.appendChild(input);
                
                document.body.appendChild(form);
                
                // Submit the form
                console.log("Submitting form to /api/social-dilemma/simulate");
                form.submit();
            } catch (error) {
                console.error("Error in run simulation handler:", error);
                alert("Error running simulation: " + error.message);
            }
        });
    } else {
        console.error("Run button element not found");
    }
    
    // Helper functions
    function validateForm() {
        console.log("Running form validation...");
        
        // Check if name is provided
        const name = document.getElementById('dilemma-name').value.trim();
        if (!name) {
            showNotification('Error', 'Please provide a configuration name', 'danger');
            console.log("Validation failed: No name provided");
            return false;
        }
        
        // Check current dilemma type
        const dilemmaType = document.getElementById('dilemma-type').value;
        console.log("Dilemma type:", dilemmaType);
        
        // Check if at least 2 agents are specified for the current dilemma
        let totalAgents = 0;
        // Need to convert underscores to hyphens for the HTML ID
        const configId = dilemmaType.replace(/_/g, '-') + '-config';
        const strategyInputs = document.querySelectorAll(`#${configId} .social-strategy-count`);
        console.log(`Found strategy inputs in #${configId}:`, strategyInputs.length);
        
        strategyInputs.forEach(input => {
            const value = parseInt(input.value) || 0;
            console.log(`Strategy ${input.dataset.strategy}: ${value} agents`);
            totalAgents += value;
        });
        
        console.log("Total agents:", totalAgents);
        
        if (totalAgents < 2) {
            showNotification('Error', 'At least 2 agents are required for the simulation', 'danger');
            console.log("Validation failed: Less than 2 agents");
            return false;
        }
        
        console.log("Form validation passed");
        return true;
    }
    
    function collectFormData() {
        // Get basic info
        const dilemmaType = document.getElementById('dilemma-type').value;
        const rounds = parseInt(document.getElementById('dilemma-rounds').value);
        
        // Prepare config object
        const config = {
            name: document.getElementById('dilemma-name').value.trim(),
            description: document.getElementById('dilemma-description').value.trim(),
            dilemma_type: dilemmaType,
            rounds: rounds,
            strategies: {}
        };
        
        // Add strategies based on dilemma type
        // Convert underscores to hyphens for proper HTML ID
        const configId = dilemmaType.replace(/_/g, '-') + '-config';
        const strategyInputs = document.querySelectorAll(`#${configId} .social-strategy-count`);
        console.log(`Collecting strategies from #${configId}, found:`, strategyInputs.length);
        
        strategyInputs.forEach(input => {
            const count = parseInt(input.value) || 0;
            if (count > 0) {
                config.strategies[input.dataset.strategy] = count;
                console.log(`Added strategy: ${input.dataset.strategy} with ${count} agents`);
            }
        });
        
        // Add specific parameters for each dilemma type
        if (dilemmaType === 'tragedy_commons') {
            config.parameters = {
                resource_size: parseInt(document.getElementById('tc-resource-size').value),
                regeneration_rate: parseFloat(document.getElementById('tc-regen-rate').value),
                harvest_limit: parseInt(document.getElementById('tc-harvest-limit').value)
            };
        } else if (dilemmaType === 'free_rider') {
            config.parameters = {
                project_cost: parseInt(document.getElementById('fr-project-cost').value),
                benefit_multiplier: parseFloat(document.getElementById('fr-contribution-reward').value),
                threshold: parseInt(document.getElementById('fr-threshold').value)
            };
        } else if (dilemmaType === 'public_goods') {
            config.parameters = {
                endowment: parseInt(document.getElementById('pg-endowment').value),
                multiplier: parseFloat(document.getElementById('pg-multiplier').value),
                distribution: document.getElementById('pg-distribution').value
            };
        }
        
        return config;
    }
    
    function displayDilemmaResults(results, config) {
        // Show round info
        document.getElementById('dilemma-round-info').style.display = 'block';
        document.getElementById('dilemma-total-rounds').textContent = results.rounds.length;
        document.getElementById('dilemma-current-round').textContent = results.rounds.length;
        document.getElementById('dilemma-round-progress').style.width = '100%';
        document.getElementById('dilemma-round-progress').textContent = '100%';
        
        // Show charts container
        document.getElementById('dilemma-charts-container').style.display = 'flex';
        
        // Update chart titles based on dilemma type
        let chart1Title, chart2Title;
        switch(config.dilemma_type) {
            case 'tragedy_commons':
                chart1Title = 'Resource Level Over Rounds';
                chart2Title = 'Harvests by Strategy Type';
                break;
            case 'free_rider':
                chart1Title = 'Project Funding Progress';
                chart2Title = 'Individual Gains by Strategy';
                break;
            case 'public_goods':
                chart1Title = 'Public Goods Contributions';
                chart2Title = 'Individual Payoffs by Strategy';
                break;
            default:
                chart1Title = 'Resource Status Over Time';
                chart2Title = 'Agent Scores by Strategy';
        }
        
        document.getElementById('dilemma-chart1-title').textContent = chart1Title;
        document.getElementById('dilemma-chart2-title').textContent = chart2Title;
        
        // Initialize charts
        initializeDilemmaCharts(results, config);
        
        // Show detailed results
        document.getElementById('dilemma-detailed-results').style.display = 'block';
        populateDilemmaResultsTable(results);
        
        // Show insights
        document.getElementById('dilemma-insights').style.display = 'block';
        generateInsights(results, config);
    }
    
    function initializeDilemmaCharts(results, config) {
        // Chart 1 - Resource or Project Status
        const ctx1 = document.getElementById('dilemma-chart1').getContext('2d');
        let chart1Data, chart1Options;
        
        // Chart 2 - Strategy Performance
        const ctx2 = document.getElementById('dilemma-chart2').getContext('2d');
        let chart2Data, chart2Options;
        
        // Configure charts based on dilemma type
        switch(config.dilemma_type) {
            case 'tragedy_commons':
                // Resource level chart
                chart1Data = {
                    labels: results.rounds.map((_, i) => `Round ${i+1}`),
                    datasets: [{
                        label: 'Resource Level',
                        data: results.resource_levels,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1,
                        fill: true
                    }]
                };
                
                chart1Options = {
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Resource Units'
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `Resource Level: ${context.parsed.y} units`;
                                }
                            }
                        }
                    }
                };
                
                // Strategy harvests chart
                const strategyLabels = Object.keys(results.strategy_performance);
                const harvestData = strategyLabels.map(strategy => 
                    results.strategy_performance[strategy].total_harvest / results.strategy_performance[strategy].agent_count
                );
                
                chart2Data = {
                    labels: strategyLabels.map(s => s.replace('_', ' ').toUpperCase()),
                    datasets: [{
                        label: 'Average Harvest Per Agent',
                        data: harvestData,
                        backgroundColor: generateColors(strategyLabels.length),
                        borderWidth: 1
                    }]
                };
                
                chart2Options = {
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Average Harvest'
                            }
                        }
                    }
                };
                break;
                
            case 'free_rider':
                // Project funding progress
                chart1Data = {
                    labels: results.rounds.map((_, i) => `Round ${i+1}`),
                    datasets: [{
                        label: 'Funding Progress',
                        data: results.funding_progress,
                        borderColor: 'rgba(54, 162, 235, 1)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        tension: 0.1,
                        fill: true
                    }, {
                        label: 'Threshold',
                        data: Array(results.rounds.length).fill(results.threshold),
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderDash: [5, 5],
                        fill: false
                    }]
                };
                
                chart1Options = {
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Funding (%)'
                            }
                        }
                    }
                };
                
                // Individual gains
                const frStrategyLabels = Object.keys(results.strategy_performance);
                const gainsData = frStrategyLabels.map(strategy => 
                    results.strategy_performance[strategy].average_gain
                );
                
                chart2Data = {
                    labels: frStrategyLabels.map(s => s.replace('_', ' ').toUpperCase()),
                    datasets: [{
                        label: 'Average Gain',
                        data: gainsData,
                        backgroundColor: generateColors(frStrategyLabels.length),
                        borderWidth: 1
                    }]
                };
                
                chart2Options = {
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Average Gain'
                            }
                        }
                    }
                };
                break;
                
            case 'public_goods':
                // Contributions over time
                const strategyTypes = Object.keys(results.strategy_performance);
                const contributionDatasets = strategyTypes.map((strategy, index) => {
                    return {
                        label: strategy.replace('_', ' ').toUpperCase(),
                        data: results.contribution_history[strategy],
                        borderColor: generateColors(strategyTypes.length)[index],
                        tension: 0.1,
                        fill: false
                    };
                });
                
                chart1Data = {
                    labels: results.rounds.map((_, i) => `Round ${i+1}`),
                    datasets: contributionDatasets
                };
                
                chart1Options = {
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Average Contribution'
                            }
                        }
                    }
                };
                
                // Payoffs by strategy
                const pgStrategyLabels = Object.keys(results.strategy_performance);
                const payoffData = pgStrategyLabels.map(strategy => 
                    results.strategy_performance[strategy].average_payoff
                );
                
                chart2Data = {
                    labels: pgStrategyLabels.map(s => s.replace('_', ' ').toUpperCase()),
                    datasets: [{
                        label: 'Average Payoff',
                        data: payoffData,
                        backgroundColor: generateColors(pgStrategyLabels.length),
                        borderWidth: 1
                    }]
                };
                
                chart2Options = {
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Average Payoff'
                            }
                        }
                    }
                };
                break;
                
            default:
                // Default charts if type not recognized
                chart1Data = {
                    labels: results.rounds.map((_, i) => `Round ${i+1}`),
                    datasets: [{
                        label: 'Resource Level',
                        data: Array(results.rounds.length).fill(0),
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    }]
                };
                
                chart2Data = {
                    labels: ['No Data'],
                    datasets: [{
                        label: 'No Data',
                        data: [0],
                        backgroundColor: ['rgba(200, 200, 200, 0.5)'],
                        borderWidth: 1
                    }]
                };
        }
        
        // Create the charts
        if (window.chart1) window.chart1.destroy();
        if (window.chart2) window.chart2.destroy();
        
        window.chart1 = new Chart(ctx1, {
            type: 'line',
            data: chart1Data,
            options: chart1Options
        });
        
        window.chart2 = new Chart(ctx2, {
            type: 'bar',
            data: chart2Data,
            options: chart2Options
        });
    }
    
    function populateDilemmaResultsTable(results) {
        const tableBody = document.getElementById('dilemma-results-table-body');
        tableBody.innerHTML = '';
        
        // Get strategy performance data
        const strategies = Object.keys(results.strategy_performance);
        
        // Find max and min scores for highlighting
        let maxScore = -Infinity;
        let minScore = Infinity;
        strategies.forEach(strategy => {
            const score = results.strategy_performance[strategy].average_score || 0;
            maxScore = Math.max(maxScore, score);
            minScore = Math.min(minScore, score);
        });
        
        // Create table rows
        strategies.forEach(strategy => {
            const perf = results.strategy_performance[strategy];
            const row = document.createElement('tr');
            
            // Determine row class based on score
            if (perf.average_score === maxScore) {
                row.classList.add('table-success');
            } else if (perf.average_score === minScore) {
                row.classList.add('table-danger');
            }
            
            // Strategy name
            const nameCell = document.createElement('td');
            nameCell.textContent = strategy.replace('_', ' ').toUpperCase();
            row.appendChild(nameCell);
            
            // Average score
            const scoreCell = document.createElement('td');
            scoreCell.textContent = perf.average_score?.toFixed(2) || 'N/A';
            row.appendChild(scoreCell);
            
            // Sustainability impact
            const impactCell = document.createElement('td');
            if (perf.sustainability_impact) {
                // Add sustainability impact icon and value
                const impactValue = perf.sustainability_impact;
                let impactIcon, impactClass;
                
                if (impactValue > 0.3) {
                    impactIcon = 'fa-plus-circle';
                    impactClass = 'text-success';
                    impactCell.textContent = ' Positive';
                } else if (impactValue < -0.3) {
                    impactIcon = 'fa-minus-circle';
                    impactClass = 'text-danger';
                    impactCell.textContent = ' Negative';
                } else {
                    impactIcon = 'fa-equals';
                    impactClass = 'text-warning';
                    impactCell.textContent = ' Neutral';
                }
                
                const icon = document.createElement('i');
                icon.className = `fas ${impactIcon} ${impactClass} me-1`;
                impactCell.prepend(icon);
            } else {
                impactCell.textContent = 'N/A';
            }
            row.appendChild(impactCell);
            
            // Social welfare
            const welfareCell = document.createElement('td');
            if (perf.social_welfare) {
                // Add social welfare icon and value
                const welfareValue = perf.social_welfare;
                let welfareIcon, welfareClass;
                
                if (welfareValue > 0.3) {
                    welfareIcon = 'fa-thumbs-up';
                    welfareClass = 'text-success';
                    welfareCell.textContent = ' High';
                } else if (welfareValue < -0.3) {
                    welfareIcon = 'fa-thumbs-down';
                    welfareClass = 'text-danger';
                    welfareCell.textContent = ' Low';
                } else {
                    welfareIcon = 'fa-equals';
                    welfareClass = 'text-warning';
                    welfareCell.textContent = ' Medium';
                }
                
                const icon = document.createElement('i');
                icon.className = `fas ${welfareIcon} ${welfareClass} me-1`;
                welfareCell.prepend(icon);
            } else {
                welfareCell.textContent = 'N/A';
            }
            row.appendChild(welfareCell);
            
            tableBody.appendChild(row);
        });
    }
    
    function generateInsights(results, config) {
        const insightsContainer = document.getElementById('dilemma-insights-content');
        insightsContainer.innerHTML = '';
        
        let insights = [];
        
        // General insight based on dilemma type
        switch(config.dilemma_type) {
            case 'tragedy_commons':
                // Check if resource collapsed
                const finalResourceLevel = results.resource_levels[results.resource_levels.length - 1];
                const initialResourceLevel = results.resource_levels[0];
                const resourceDepleted = finalResourceLevel < initialResourceLevel * 0.1;
                
                if (resourceDepleted) {
                    insights.push({
                        title: 'Resource Collapse',
                        content: 'The shared resource was depleted to critical levels, demonstrating how individual short-term interests can lead to collective long-term harm.',
                        icon: 'fa-exclamation-triangle',
                        class: 'text-danger'
                    });
                } else {
                    insights.push({
                        title: 'Sustainable Management',
                        content: 'The resource was maintained at sustainable levels, showing that with the right balance of strategies, common resources can be preserved.',
                        icon: 'fa-check-circle',
                        class: 'text-success'
                    });
                }
                
                // Compare greedy vs. sustainable strategies
                if (results.strategy_performance.greedy && results.strategy_performance.sustainable) {
                    const greedyAvg = results.strategy_performance.greedy.average_score;
                    const sustainableAvg = results.strategy_performance.sustainable.average_score;
                    
                    if (greedyAvg > sustainableAvg && !resourceDepleted) {
                        insights.push({
                            title: 'Short-term Advantage',
                            content: 'Greedy harvesting strategies outperformed sustainable ones while still maintaining resource viability, highlighting the tension between individual gain and collective responsibility.',
                            icon: 'fa-balance-scale',
                            class: 'text-warning'
                        });
                    } else if (sustainableAvg > greedyAvg) {
                        insights.push({
                            title: 'Sustainability Wins',
                            content: 'Sustainable harvesting strategies achieved better outcomes than greedy ones, demonstrating that long-term thinking can be both individually and collectively beneficial.',
                            icon: 'fa-seedling',
                            class: 'text-success'
                        });
                    }
                }
                break;
                
            case 'free_rider':
                // Check if project was successfully funded
                const finalFunding = results.funding_progress[results.funding_progress.length - 1];
                const projectSucceeded = finalFunding >= results.threshold;
                
                if (projectSucceeded) {
                    insights.push({
                        title: 'Project Success Despite Free Riders',
                        content: 'The project was successfully funded despite the presence of free riders, showing that a critical mass of contributors can overcome the free rider problem.',
                        icon: 'fa-check-circle',
                        class: 'text-success'
                    });
                } else {
                    insights.push({
                        title: 'Project Failure Due to Free Riding',
                        content: 'The project failed to reach its funding threshold, demonstrating how free riding behavior can lead to the underprovision of public goods.',
                        icon: 'fa-times-circle',
                        class: 'text-danger'
                    });
                }
                
                // Compare contributor vs. free rider outcomes
                if (results.strategy_performance.contributor && results.strategy_performance.free_rider) {
                    const contributorAvg = results.strategy_performance.contributor.average_gain;
                    const freeRiderAvg = results.strategy_performance.free_rider.average_gain;
                    
                    if (freeRiderAvg > contributorAvg && projectSucceeded) {
                        insights.push({
                            title: 'Free Rider Advantage',
                            content: 'Free riders achieved higher individual gains than contributors, illustrating why free riding behavior persists in many social contexts.',
                            icon: 'fa-user-ninja',
                            class: 'text-warning'
                        });
                    } else if (contributorAvg > freeRiderAvg || !projectSucceeded) {
                        insights.push({
                            title: 'Contribution Rewarded',
                            content: 'Contributors achieved better outcomes than free riders, suggesting that mechanisms to reward contribution may help overcome the free rider problem.',
                            icon: 'fa-hand-holding-heart',
                            class: 'text-success'
                        });
                    }
                }
                break;
                
            case 'public_goods':
                // Check overall contribution trends
                const firstRoundAvg = results.average_contribution[0];
                const lastRoundAvg = results.average_contribution[results.average_contribution.length - 1];
                const contributionDeclined = lastRoundAvg < firstRoundAvg * 0.7;
                
                if (contributionDeclined) {
                    insights.push({
                        title: 'Declining Contributions',
                        content: 'Contributions to the public good declined over time, a common pattern seen in repeated public goods games as participants adjust their strategy based on others\' behavior.',
                        icon: 'fa-chart-line-down',
                        class: 'text-danger'
                    });
                } else {
                    insights.push({
                        title: 'Sustained Contributions',
                        content: 'Contributions to the public good remained stable or increased over time, contrary to the typical pattern seen in many public goods experiments.',
                        icon: 'fa-chart-line',
                        class: 'text-success'
                    });
                }
                
                // Compare zero vs. full contributors
                if (results.strategy_performance.zero && results.strategy_performance.full) {
                    const zeroAvg = results.strategy_performance.zero.average_payoff;
                    const fullAvg = results.strategy_performance.full.average_payoff;
                    
                    if (zeroAvg > fullAvg) {
                        insights.push({
                            title: 'Non-contribution Advantage',
                            content: 'Non-contributors achieved higher individual payoffs than full contributors, highlighting the inherent tension in public goods provision.',
                            icon: 'fa-user-slash',
                            class: 'text-warning'
                        });
                    } else if (fullAvg > zeroAvg) {
                        insights.push({
                            title: 'Contribution Pays Off',
                            content: 'Full contributors achieved better outcomes than non-contributors, suggesting that the multiplier effect was strong enough to make contribution individually rational.',
                            icon: 'fa-hands-helping',
                            class: 'text-success'
                        });
                    }
                }
                break;
                
            default:
                insights.push({
                    title: 'Simulation Complete',
                    content: 'Examine the charts and data to understand the dynamics of this social dilemma.',
                    icon: 'fa-search',
                    class: 'text-info'
                });
        }
        
        // Add general insight about emergence
        insights.push({
            title: 'Emergent Social Behavior',
            content: 'This simulation demonstrates how complex social dynamics can emerge from simple interaction rules and how individual decisions collectively shape outcomes that affect everyone.',
            icon: 'fa-brain',
            class: 'text-primary'
        });
        
        // Add real-world connection
        const realWorldConnections = {
            tragedy_commons: 'Real-world examples include climate change, overfishing, and deforestation, where individual actors have incentives to overuse shared resources.',
            free_rider: 'Similar dynamics occur in public transportation fare evasion, tax compliance, and voluntary contributions to public services.',
            public_goods: 'This mirrors scenarios like open-source software development, Wikipedia contributions, and community improvement projects.'
        };
        
        if (realWorldConnections[config.dilemma_type]) {
            insights.push({
                title: 'Real-World Connection',
                content: realWorldConnections[config.dilemma_type],
                icon: 'fa-globe',
                class: 'text-info'
            });
        }
        
        // Display insights
        insights.forEach(insight => {
            const card = document.createElement('div');
            card.className = 'card mb-3';
            
            const cardBody = document.createElement('div');
            cardBody.className = 'card-body';
            
            const title = document.createElement('h5');
            title.className = 'card-title';
            title.innerHTML = `<i class="fas ${insight.icon} ${insight.class} me-2"></i>${insight.title}`;
            
            const content = document.createElement('p');
            content.className = 'card-text';
            content.textContent = insight.content;
            
            cardBody.appendChild(title);
            cardBody.appendChild(content);
            card.appendChild(cardBody);
            
            insightsContainer.appendChild(card);
        });
    }
    
    function showNotification(title, message, type = 'primary') {
        console.log(`Showing notification: ${title} - ${message} (${type})`);
        
        // Check if we should use fallback notification
        if (window.showNotificationFallback) {
            window.showNotificationFallback(title, message);
            return;
        }
        
        try {
            // Get toast elements
            const toastEl = document.getElementById('notification-toast');
            const titleEl = document.getElementById('toast-title');
            const messageEl = document.getElementById('toast-message');
            
            // If elements don't exist, fall back to alert
            if (!toastEl || !titleEl || !messageEl) {
                throw new Error("Toast elements not found");
            }
            
            // Update toast content
            titleEl.textContent = title;
            messageEl.textContent = message;
            
            // Set toast color based on type
            toastEl.className = 'toast';
            toastEl.classList.add(`bg-${type === 'danger' ? 'danger' : 'dark'}`);
            toastEl.classList.add(type === 'danger' ? 'text-white' : 'text-light');
            
            // Try to use Bootstrap Toast if available
            if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
                const bsToast = new bootstrap.Toast(toastEl);
                bsToast.show();
            } else {
                // Manual toast display
                toastEl.style.display = 'block';
                toastEl.style.opacity = '1';
                
                // Auto-hide after 4 seconds
                setTimeout(() => {
                    toastEl.style.opacity = '0';
                    setTimeout(() => {
                        toastEl.style.display = 'none';
                    }, 300);
                }, 4000);
            }
        } catch (e) {
            console.error("Error showing toast:", e);
            alert(title + ": " + message);
        }
    }
    
    function generateColors(count) {
        const colors = [
            'rgba(255, 99, 132, 0.7)',   // Red
            'rgba(54, 162, 235, 0.7)',   // Blue
            'rgba(255, 206, 86, 0.7)',   // Yellow
            'rgba(75, 192, 192, 0.7)',   // Green
            'rgba(153, 102, 255, 0.7)',  // Purple
            'rgba(255, 159, 64, 0.7)',   // Orange
            'rgba(199, 199, 199, 0.7)',  // Gray
            'rgba(83, 102, 255, 0.7)',   // Indigo
            'rgba(255, 99, 255, 0.7)',   // Pink
            'rgba(99, 255, 132, 0.7)'    // Light green
        ];
        
        // If we need more colors than in our predefined array, generate random ones
        if (count > colors.length) {
            for (let i = colors.length; i < count; i++) {
                const r = Math.floor(Math.random() * 255);
                const g = Math.floor(Math.random() * 255);
                const b = Math.floor(Math.random() * 255);
                colors.push(`rgba(${r}, ${g}, ${b}, 0.7)`);
            }
        }
        
        return colors.slice(0, count);
    }
    
    // Initialize on page load
    updateDilemmaTotalAgents();
    
    // Add debugging to help identify issues
    console.log("Social dilemmas page initialization complete");
}

// Execute initialization when page loads
if (document.readyState === 'loading') {
    // Still loading, so wait for the DOMContentLoaded event
    console.log("Document still loading, waiting for DOMContentLoaded");
} else {
    // DOM has already loaded, initialize immediately
    console.log("Document already loaded, initializing now");
    ensureBootstrap(initializePage);
}