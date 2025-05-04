// Chart configuration and utilities for EvoGames - Mui Lab

// Function to generate random colors for chart datasets
function generateColors(count) {
    const colors = [
        '#4dc9f6', '#f67019', '#f53794', '#537bc4',
        '#acc236', '#166a8f', '#00a950', '#58595b',
        '#8549ba', '#e6194b', '#3cb44b', '#ffe119',
        '#4363d8', '#f58231', '#911eb4', '#46f0f0',
        '#f032e6', '#bcf60c', '#fabebe', '#008080'
    ];
    
    // If we need more colors than in our predefined list, generate random ones
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

// Initialize charts with empty data
let scoreChart = null;
let strategyPerformanceChart = null;
let cooperationChart = null;
let interactionChart = null;

function initializeCharts() {
    // Destroy existing charts if they exist
    if (scoreChart) scoreChart.destroy();
    if (strategyPerformanceChart) strategyPerformanceChart.destroy();
    if (cooperationChart) cooperationChart.destroy();
    if (interactionChart) interactionChart.destroy();
    
    // Score Chart - Line chart showing agent scores over rounds
    const scoreCtx = document.getElementById('score-chart').getContext('2d');
    scoreChart = new Chart(scoreCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Agent Scores Over Rounds',
                    color: '#fff'
                },
                legend: {
                    position: 'top',
                    labels: {
                        color: '#fff'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Round',
                        color: '#fff'
                    },
                    ticks: {
                        color: '#fff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Cumulative Score',
                        color: '#fff'
                    },
                    ticks: {
                        color: '#fff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
    
    // Strategy Performance Chart - Bar chart showing average scores by strategy
    const strategyCtx = document.getElementById('strategy-performance-chart').getContext('2d');
    strategyPerformanceChart = new Chart(strategyCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Average Score',
                data: [],
                backgroundColor: []
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Average Score by Strategy',
                    color: '#fff'
                },
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    display: true,
                    ticks: {
                        color: '#fff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Average Score',
                        color: '#fff'
                    },
                    ticks: {
                        color: '#fff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
    
    // Cooperation Chart - Doughnut chart showing overall cooperation vs defection
    const cooperationCtx = document.getElementById('cooperation-chart').getContext('2d');
    cooperationChart = new Chart(cooperationCtx, {
        type: 'doughnut',
        data: {
            labels: ['Cooperation', 'Defection'],
            datasets: [{
                data: [0, 0],
                backgroundColor: ['rgba(75, 192, 192, 0.7)', 'rgba(255, 99, 132, 0.7)'],
                borderColor: ['rgb(75, 192, 192)', 'rgb(255, 99, 132)'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Overall Cooperation vs Defection',
                    color: '#fff'
                },
                legend: {
                    position: 'top',
                    labels: {
                        color: '#fff'
                    }
                }
            }
        }
    });
    
    // Interaction Chart - Radar chart showing cooperation rates between strategies
    const interactionCtx = document.getElementById('interaction-chart').getContext('2d');
    interactionChart = new Chart(interactionCtx, {
        type: 'radar',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Strategy Cooperation Rates',
                    color: '#fff'
                },
                legend: {
                    position: 'top',
                    labels: {
                        color: '#fff'
                    }
                }
            },
            scales: {
                r: {
                    angleLines: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    pointLabels: {
                        color: '#fff'
                    },
                    ticks: {
                        color: '#fff',
                        backdropColor: 'rgba(0, 0, 0, 0)'
                    }
                }
            }
        }
    });
}

// Update charts with simulation results
function updateCharts(results, config) {
    // Clear and initialize charts
    initializeCharts();
    
    // Generate round labels
    const rounds = results.rounds.length;
    const roundLabels = Array.from({length: rounds}, (_, i) => i + 1);
    
    // Update Score Chart
    const agentIds = Object.keys(results.scores);
    const colors = generateColors(agentIds.length);
    
    const scoreDatasets = agentIds.map((agentId, index) => {
        // Extract agent type from ID (e.g., "tit_for_tat_1" -> "tit_for_tat")
        const agentType = agentId.substring(0, agentId.lastIndexOf('_'));
        return {
            label: formatStrategyName(agentType),
            data: results.scores[agentId],
            borderColor: colors[index],
            backgroundColor: colors[index] + '33', // Add transparency
            fill: false,
            tension: 0.1
        };
    });
    
    scoreChart.data.labels = roundLabels;
    scoreChart.data.datasets = scoreDatasets;
    scoreChart.update();
    
    // Update Strategy Performance Chart
    const strategies = Object.keys(results.strategy_performance);
    const avgScores = strategies.map(s => results.strategy_performance[s].avg_score);
    strategyPerformanceChart.data.labels = strategies.map(formatStrategyName);
    strategyPerformanceChart.data.datasets[0].data = avgScores;
    strategyPerformanceChart.data.datasets[0].backgroundColor = generateColors(strategies.length);
    strategyPerformanceChart.update();
    
    // Update Cooperation Chart
    cooperationChart.data.datasets[0].data = [
        results.overall_cooperation,
        results.overall_defection
    ];
    cooperationChart.update();
    
    // Update Interaction Chart - Showing cooperation rates for each strategy
    const strategyLabels = strategies.map(formatStrategyName);
    const cooperationRates = strategies.map(s => 
        results.strategy_performance[s].cooperation_rate * 100
    );
    
    interactionChart.data.labels = strategyLabels;
    interactionChart.data.datasets = [{
        label: 'Cooperation Rate (%)',
        data: cooperationRates,
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        borderColor: 'rgb(75, 192, 192)',
        pointBackgroundColor: 'rgb(75, 192, 192)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgb(75, 192, 192)'
    }];
    interactionChart.update();
}

// Helper function to format strategy names for display
function formatStrategyName(name) {
    return name.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}
