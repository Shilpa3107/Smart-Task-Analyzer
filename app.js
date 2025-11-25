// DOM Elements
const taskForm = document.getElementById('task-form');
const taskList = document.getElementById('task-list');
const analyzeBtn = document.getElementById('analyze-btn');
const clearTasksBtn = document.getElementById('clear-tasks');
const exportJsonBtn = document.getElementById('export-json');
const importJsonBtn = document.getElementById('import-json');
const jsonInput = document.getElementById('json-input');
const sortStrategy = document.getElementById('sort-strategy');
const taskCount = document.getElementById('task-count');
const loadingOverlay = document.getElementById('loading-overlay');
const tabButtons = document.querySelectorAll('.tab-button');
const tabContents = document.querySelectorAll('.tab-content');

// State
let tasks = JSON.parse(localStorage.getItem('tasks')) || [];
let analyzedTasks = [];

// Initialize the app
function init() {
    renderTaskList();
    setupEventListeners();
    updateTaskCount();
}

// Set up event listeners
function setupEventListeners() {
    // Form submission
    taskForm.addEventListener('submit', handleAddTask);
    
    // Button clicks
    analyzeBtn.addEventListener('click', analyzeTasks);
    clearTasksBtn.addEventListener('click', clearTasks);
    exportJsonBtn.addEventListener('click', exportTasks);
    importJsonBtn.addEventListener('click', importTasks);
    
    // Tab switching
    tabButtons.forEach(button => {
        button.addEventListener('click', () => switchTab(button.dataset.tab));
    });
}

// Switch between tabs
function switchTab(tabId) {
    // Update active tab button
    tabButtons.forEach(button => {
        button.classList.toggle('active', button.dataset.tab === tabId);
    });
    
    // Show active tab content
    tabContents.forEach(content => {
        content.classList.toggle('active', content.id === `${tabId}-form` || 
            (tabId === 'single' && content.id === 'single-task-form'));
    });
}

// Handle adding a new task
function handleAddTask(e) {
    e.preventDefault();
    
    const title = document.getElementById('title').value.trim();
    const dueDate = document.getElementById('due-date').value;
    const effort = parseInt(document.getElementById('effort').value);
    const importance = parseInt(document.getElementById('importance').value);
    const description = document.getElementById('description').value.trim();
    
    if (!title || !dueDate || isNaN(effort) || isNaN(importance)) {
        showAlert('Please fill in all required fields', 'error');
        return;
    }
    
    const task = {
        id: Date.now().toString(),
        title,
        dueDate,
        effort,
        importance,
        description,
        createdAt: new Date().toISOString()
    };
    
    tasks.push(task);
    saveTasks();
    renderTaskList();
    updateTaskCount();
    
    // Reset form
    taskForm.reset();
    
    showAlert('Task added successfully!', 'success');
}

// Import tasks from JSON
function importTasks() {
    try {
        const importedTasks = JSON.parse(jsonInput.value);
        
        if (!Array.isArray(importedTasks)) {
            throw new Error('Invalid format. Please provide a valid JSON array of tasks.');
        }
        
        // Validate each task
        const validTasks = importedTasks.filter(task => {
            return task.title && task.dueDate && task.effort && task.importance;
        });
        
        if (validTasks.length === 0) {
            throw new Error('No valid tasks found in the provided JSON.');
        }
        
        // Add imported tasks
        tasks = [...tasks, ...validTasks.map(task => ({
            ...task,
            id: task.id || Date.now().toString() + Math.random().toString(36).substr(2, 9),
            createdAt: task.createdAt || new Date().toISOString()
        }))];
        
        saveTasks();
        renderTaskList();
        updateTaskCount();
        
        // Clear the input
        jsonInput.value = '';
        
        showAlert(`Successfully imported ${validTasks.length} tasks!`, 'success');
    } catch (error) {
        console.error('Error importing tasks:', error);
        showAlert(error.message || 'Failed to import tasks. Please check the JSON format.', 'error');
    }
}

// Export tasks as JSON
function exportTasks() {
    if (tasks.length === 0) {
        showAlert('No tasks to export.', 'warning');
        return;
    }
    
    const dataStr = JSON.stringify(tasks, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `tasks-${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    showAlert('Tasks exported successfully!', 'success');
}

// Clear all tasks
function clearTasks() {
    if (tasks.length === 0) return;
    
    if (confirm('Are you sure you want to clear all tasks? This cannot be undone.')) {
        tasks = [];
        analyzedTasks = [];
        saveTasks();
        renderTaskList();
        updateTaskCount();
        showAlert('All tasks have been cleared.', 'info');
    }
}

// Analyze tasks using the selected strategy
async function analyzeTasks() {
    if (tasks.length === 0) {
        showAlert('Please add at least one task to analyze.', 'warning');
        return;
    }
    
    const strategy = sortStrategy.value;
    
    try {
        showLoading(true);
        
        // In a real app, you would call your API here
        // For now, we'll simulate an API call with a timeout
        analyzedTasks = await simulateApiCall(tasks, strategy);
        
        // Sort tasks based on the selected strategy
        sortTasks(analyzedTasks, strategy);
        
        // Render the analyzed tasks
        renderTaskList(analyzedTasks);
        
        showAlert(`Tasks analyzed using ${getStrategyName(strategy)} strategy.`, 'success');
    } catch (error) {
        console.error('Error analyzing tasks:', error);
        showAlert('Failed to analyze tasks. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

// Simulate API call (replace with actual API call)
function simulateApiCall(tasks, strategy) {
    return new Promise((resolve) => {
        // Simulate network delay
        setTimeout(() => {
            // Calculate priority score for each task based on the strategy
            const processedTasks = tasks.map(task => {
                let score = 0;
                let explanation = '';
                
                const today = new Date();
                const dueDate = new Date(task.dueDate);
                const daysUntilDue = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));
                
                switch (strategy) {
                    case 'fastest':
                        // Lower effort = higher priority
                        score = (1 / task.effort) * 100;
                        explanation = `This task was prioritized because it has a low effort level (${task.effort}/5).`;
                        break;
                        
                    case 'impact':
                        // Higher importance = higher priority
                        score = task.importance * 20;
                        explanation = `This task was prioritized because it has high importance (${task.importance}/5).`;
                        break;
                        
                    case 'deadline':
                        // Sooner due date = higher priority
                        score = 100 / (daysUntilDue + 1); // +1 to avoid division by zero
                        explanation = `This task is due in ${daysUntilDue} days.`;
                        break;
                        
                    default: // 'smart' - balanced approach
                        // Weighted combination of factors
                        const effortWeight = 0.3;
                        const importanceWeight = 0.4;
                        const urgencyWeight = 0.3;
                        
                        // Normalize values (higher is better)
                        const normalizedEffort = (6 - task.effort) / 5; // Invert effort (1-5 to 5-1)
                        const normalizedImportance = task.importance / 5;
                        const normalizedUrgency = 1 / (daysUntilDue + 1);
                        
                        // Calculate weighted score (0-100)
                        score = (
                            (normalizedEffort * effortWeight) +
                            (normalizedImportance * importanceWeight) +
                            (normalizedUrgency * urgencyWeight)
                        ) * 100;
                        
                        explanation = `This task was prioritized based on a balanced consideration of effort (${task.effort}/5), ` +
                                    `importance (${task.importance}/5), and time until deadline (${daysUntilDue} days).`;
                }
                
                // Round to 2 decimal places
                score = Math.round(score * 100) / 100;
                
                return {
                    ...task,
                    score,
                    explanation
                };
            });
            
            resolve(processedTasks);
        }, 1000); // Simulate 1 second delay
    });
}

// Sort tasks based on the selected strategy
function sortTasks(tasks, strategy) {
    tasks.sort((a, b) => {
        // For deadline strategy, we want tasks due sooner to appear first
        if (strategy === 'deadline') {
            return new Date(a.dueDate) - new Date(b.dueDate);
        }
        
        // For other strategies, sort by score (descending)
        return b.score - a.score;
    });
}

// Get display name for strategy
function getStrategyName(strategy) {
    const strategies = {
        'smart': 'Smart Balance',
        'fastest': 'Fastest Wins',
        'impact': 'High Impact',
        'deadline': 'Deadline Driven'
    };
    return strategies[strategy] || strategy;
}

// Render the task list
function renderTaskList(tasksToRender = null) {
    const displayTasks = tasksToRender || tasks;
    
    if (displayTasks.length === 0) {
        taskList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>${tasksToRender ? 'No tasks to display. Try analyzing your tasks first.' : 'Add tasks to get started'}</p>
            </div>
        `;
        return;
    }
    
    taskList.innerHTML = displayTasks.map(task => {
        const dueDate = new Date(task.dueDate).toLocaleDateString();
        const priority = getPriorityLevel(task.score || 0);
        const priorityClass = task.score ? `${priority}-priority` : '';
        const scoreDisplay = task.score !== undefined ? 
            `<div class="task-score" title="Priority Score: ${task.score.toFixed(2)}">${Math.round(task.score)}</div>` : '';
        
        const explanation = task.explanation ? 
            `<div class="task-explanation">${task.explanation}</div>` : '';
        
        return `
            <div class="task-item ${priorityClass}">
                ${scoreDisplay}
                <div class="task-header">
                    <h3 class="task-title">${task.title}</h3>
                    ${task.score ? 
                        `<span class="priority-badge priority-${priority}">
                            ${priority.charAt(0).toUpperCase() + priority.slice(1)} Priority
                        </span>` : ''
                    }
                </div>
                <div class="task-meta">
                    <span title="Due Date"><i class="far fa-calendar-alt"></i> ${dueDate}</span>
                    <span title="Effort"><i class="fas fa-bolt"></i> ${task.effort}/5</span>
                    <span title="Importance"><i class="fas fa-star"></i> ${task.importance}/5</span>
                </div>
                ${task.description ? `<p>${task.description}</p>` : ''}
                ${explanation}
            </div>
        `;
    }).join('');
}

// Get priority level based on score
function getPriorityLevel(score) {
    if (score >= 70) return 'high';
    if (score >= 30) return 'medium';
    return 'low';
}

// Update task count display
function updateTaskCount() {
    const count = tasks.length;
    taskCount.textContent = `${count} task${count !== 1 ? 's' : ''}`;
}

// Save tasks to localStorage
function saveTasks() {
    localStorage.setItem('tasks', JSON.stringify(tasks));
}

// Show loading overlay
function showLoading(show) {
    if (show) {
        loadingOverlay.classList.add('active');
    } else {
        loadingOverlay.classList.remove('active');
    }
}

// Show alert message
function showAlert(message, type = 'info') {
    // Remove any existing alerts
    const existingAlert = document.querySelector('.alert');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <span>${message}</span>
        <button class="alert-close">&times;</button>
    `;
    
    document.body.appendChild(alert);
    
    // Add close button functionality
    const closeBtn = alert.querySelector('.alert-close');
    closeBtn.addEventListener('click', () => {
        alert.remove();
    });
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (document.body.contains(alert)) {
            alert.remove();
        }
    }, 5000);
}

// Add some CSS for the alert
const alertStyles = document.createElement('style');
alertStyles.textContent = `
    .alert {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 4px;
        color: white;
        display: flex;
        align-items: center;
        justify-content: space-between;
        min-width: 250px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    }
    
    .alert-success {
        background-color: #4bb543;
    }
    
    .alert-error {
        background-color: #ef476f;
    }
    
    .alert-warning {
        background-color: #f9c74f;
        color: #212529;
    }
    
    .alert-info {
        background-color: #4361ee;
    }
    
    .alert-close {
        background: none;
        border: none;
        color: inherit;
        font-size: 1.2rem;
        cursor: pointer;
        margin-left: 15px;
        opacity: 0.8;
    }
    
    .alert-close:hover {
        opacity: 1;
    }
    
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
`;

document.head.appendChild(alertStyles);

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', init);
