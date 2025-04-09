// Global variables
let currentSessionId = null;
let currentStage = null;
const stages = [
    'STAGE_REQUIREMENT_GATHERING',
    'STAGE_CONSTRAINT_GENERATION',
    'STAGE_CONSTRAINT_VISUALIZATION',
    'STAGE_CONSTRAINT_REFINEMENT',
    'STAGE_SOLUTION_GENERATION',
    'STAGE_SOLUTION_REFINEMENT'
];

// Stage display names for readability
const stageDisplayNames = {
    'STAGE_REQUIREMENT_GATHERING': 'Requirement Gathering',
    'STAGE_CONSTRAINT_GENERATION': 'Constraint Generation',
    'STAGE_CONSTRAINT_VISUALIZATION': 'Constraint Visualization',
    'STAGE_CONSTRAINT_REFINEMENT': 'Constraint Refinement',
    'STAGE_SOLUTION_GENERATION': 'Solution Generation',
    'STAGE_SOLUTION_REFINEMENT': 'Solution Refinement'
};

// Set up the event listeners when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Button event listeners
    document.getElementById('newSessionBtn').addEventListener('click', startNewSession);
    document.getElementById('resumeSessionBtn').addEventListener('click', showResumeModal);
    document.getElementById('confirmResumeBtn').addEventListener('click', resumeSession);
    document.getElementById('sendBtn').addEventListener('click', sendMessage);
    document.getElementById('skipBtn').addEventListener('click', skipStage);
    
    // Enter key in input field
    document.getElementById('userInput').addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });

    // Disable UI until session is started
    updateUIState(false);
});

// Update UI based on session state
function updateUIState(sessionActive) {
    const elements = [
        document.getElementById('userInput'),
        document.getElementById('sendBtn'),
        document.getElementById('skipBtn')
    ];
    
    elements.forEach(el => {
        if (el) el.disabled = !sessionActive;
    });
    
    // Update progress bar based on current stage
    updateProgressBar();
}

// Update the progress bar to reflect the current stage
function updateProgressBar() {
    const progressBar = document.getElementById('stageProgress');
    if (!currentStage) {
        progressBar.style.width = '0%';
        progressBar.setAttribute('data-label', '');
        return;
    }
    
    const stageIndex = stages.indexOf(currentStage);
    if (stageIndex >= 0) {
        const progressPercent = (stageIndex + 1) / stages.length * 100;
        progressBar.style.width = `${progressPercent}%`;
        progressBar.setAttribute('data-label', `${stageDisplayNames[currentStage]} (${stageIndex + 1}/${stages.length})`);
        
        // Update progress bar color based on stage
        progressBar.className = 'progress-bar';
        
        // Different colors for different stages
        if (currentStage === 'STAGE_REQUIREMENT_GATHERING') {
            progressBar.classList.add('bg-primary'); // Blue
        } else if (currentStage === 'STAGE_CONSTRAINT_GENERATION') {
            progressBar.classList.add('bg-info'); // Light blue
        } else if (currentStage === 'STAGE_CONSTRAINT_VISUALIZATION') {
            progressBar.classList.add('bg-success'); // Green
        } else if (currentStage === 'STAGE_CONSTRAINT_REFINEMENT') {
            progressBar.classList.add('bg-warning'); // Yellow
        } else if (currentStage === 'STAGE_SOLUTION_GENERATION') {
            progressBar.classList.add('bg-danger'); // Red
        } else if (currentStage === 'STAGE_SOLUTION_REFINEMENT') {
            progressBar.classList.add('bg-info'); // Light blue
        }
        
        // Add stage indicators below progress bar if they don't exist
        const stageIndicatorsContainer = document.querySelector('.stage-indicators');
        if (!stageIndicatorsContainer) {
            const container = document.createElement('div');
            container.className = 'stage-indicators d-flex justify-content-between mt-2';
            
            // Add an indicator for each stage
            stages.forEach((stage, index) => {
                const indicator = document.createElement('span');
                indicator.className = 'stage-indicator-dot';
                indicator.setAttribute('data-stage', stage);
                indicator.setAttribute('title', stageDisplayNames[stage]);
                
                // Add tooltip using Bootstrap
                new bootstrap.Tooltip(indicator);
                
                container.appendChild(indicator);
            });
            
            // Add the indicators after the progress bar
            const progressContainer = document.querySelector('.progress');
            progressContainer.parentNode.insertBefore(container, progressContainer.nextSibling);
        }
        
        // Update the active stage indicator
        document.querySelectorAll('.stage-indicator-dot').forEach((dot, index) => {
            if (index <= stageIndex) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }
}

// Start a new session
function startNewSession() {
    addSystemMessage("Starting new session...");
    
    fetch('/api/start', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            addSystemMessage('Error: ' + data.error);
            return;
        }
        
        currentSessionId = data.session_id;
        addSystemMessage('Welcome to the Architecture AI Design System! Please describe your building project and requirements.');
        updateUIState(true);
        refreshState();
    })
    .catch(error => {
        console.error('Error starting new session:', error);
        addSystemMessage('Error starting new session. Please try again.');
    });
}

// Show the resume session modal
function showResumeModal() {
    // Show loading spinner
    document.getElementById('sessionLoadingSpinner').classList.remove('d-none');
    
    // Load available sessions from the backend
    fetch('/api/list_sessions')
        .then(response => response.json())
        .then(data => {
            const selectElement = document.getElementById('sessionPathSelect');
            
            // Clear existing options
            selectElement.innerHTML = '';
            
            if (data.sessions && data.sessions.length > 0) {
                // Add a default/prompt option
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Select a session...';
                selectElement.appendChild(defaultOption);
                
                // Add options for each session
                data.sessions.forEach(session => {
                    const option = document.createElement('option');
                    option.value = session;
                    option.textContent = session;
                    selectElement.appendChild(option);
                });
            } else {
                // No sessions found
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No sessions found';
                selectElement.appendChild(option);
            }
            
            // Hide loading spinner
            document.getElementById('sessionLoadingSpinner').classList.add('d-none');
        })
        .catch(error => {
            console.error('Error loading sessions:', error);
            
            // Update dropdown with error message
            const selectElement = document.getElementById('sessionPathSelect');
            selectElement.innerHTML = '<option value="">Error loading sessions</option>';
            
            // Hide loading spinner
            document.getElementById('sessionLoadingSpinner').classList.add('d-none');
        });
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('resumeSessionModal'));
    modal.show();
    
    // Set up session path select dropdown to update text input
    document.getElementById('sessionPathSelect').addEventListener('change', function() {
        const selectedValue = this.value;
        if (selectedValue) {
            document.getElementById('sessionPath').value = selectedValue;
        }
    });
}

// Resume an existing session
function resumeSession() {
    // Try dropdown first, then fall back to text input
    let sessionPath = document.getElementById('sessionPathSelect').value;
    if (!sessionPath) {
        sessionPath = document.getElementById('sessionPath').value;
    }
    
    if (!sessionPath) {
        alert('Please select or enter a session path');
        return;
    }
    
    // Close the modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('resumeSessionModal'));
    modal.hide();
    
    addSystemMessage("Resuming session...");
    
    fetch('/api/resume', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_path: sessionPath })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            addSystemMessage('Error: ' + data.error);
            return;
        }
        
        currentSessionId = data.session_id;
        addSystemMessage('Session resumed. You can continue from where you left off.');
        updateUIState(true);
        refreshState();
    })
    .catch(error => {
        console.error('Error resuming session:', error);
        addSystemMessage('Error resuming session. Please check the path and try again.');
    });
}

// Send a message to the backend
function sendMessage() {
    if (!currentSessionId) {
        alert('Please start or resume a session first.');
        return;
    }
    
    const userInput = document.getElementById('userInput');
    const message = userInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addUserMessage(message);
    userInput.value = '';
    
    // Disable input while processing
    updateUIState(false);
    addSystemMessage("Processing...", true); // temporary message with loading indicator
    
    // Send message to backend
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_id: currentSessionId,
            message: message
        })
    })
    .then(response => response.json())
    .then(data => {
        // Remove temporary loading message
        removeLoadingMessage();
        
        if (data.error) {
            addSystemMessage('Error: ' + data.error);
            updateUIState(true);
            return;
        }
        
        // Handle response based on current stage
        if (typeof data.response === 'string') {
            addSystemMessage(data.response);
        } else if (data.response && typeof data.response === 'object') {
            if (data.response.question) {
                addSystemMessage(data.response.question);
            } else {
                addSystemMessage(JSON.stringify(data.response));
            }
        }
        
        // Check for stage change
        if (data.stage_change) {
            currentStage = data.next_stage;
            document.getElementById('stageDescription').textContent = data.stage_description;
            updateProgressBar();
            
            // If moving to constraint generation, we don't need to do anything special
            // as the backend is already handling that process
        }
        
        // Re-enable input
        updateUIState(true);
        
        // Refresh state and visualizations
        refreshState();
    })
    .catch(error => {
        removeLoadingMessage();
        console.error('Error sending message:', error);
        addSystemMessage('Error processing your message. Please try again.');
        updateUIState(true);
    });
}

// Skip the current stage
function skipStage() {
    if (!currentSessionId) {
        alert('Please start or resume a session first.');
        return;
    }
    
    // Disable UI during skip
    updateUIState(false);
    addSystemMessage("Skipping current stage...");
    
    // Send skip command
    fetch('/api/skip_stage', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_id: currentSessionId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            addSystemMessage('Error: ' + data.error);
            updateUIState(true);
            return;
        }
        
        // Update current stage
        currentStage = data.current_stage;
        document.getElementById('stageDescription').textContent = data.stage_description;
        updateProgressBar();
        
        // Re-enable UI
        updateUIState(true);
        
        // Refresh state
        refreshState();
    })
    .catch(error => {
        console.error('Error skipping stage:', error);
        addSystemMessage('Error skipping stage. Please try again.');
        updateUIState(true);
    });
}

// Refresh the system state
function refreshState() {
    if (!currentSessionId) return;
    
    fetch(`/api/state?session_id=${currentSessionId}`)
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error fetching state:', data.error);
            return;
        }
        
        // Check if stage changed
        const previousStage = currentStage;
        currentStage = data.current_stage;
        const stageChanged = previousStage !== currentStage;
        
        // Update stage description and progress bar
        document.getElementById('stageDescription').textContent = data.stage_description;
        updateProgressBar();
        
        // If stage changed, show a notification
        if (stageChanged && previousStage) {
            addSystemMessage(`Stage changed from ${stageDisplayNames[previousStage]} to ${stageDisplayNames[currentStage]}`);
            
            // If we just entered constraint generation stage
            if (currentStage === 'STAGE_CONSTRAINT_GENERATION') {
                updateConstraintGenerationProgress({ progress: 10, message: "Starting constraint generation..." });
            } 
            // If we just moved past constraint generation
            else if (previousStage === 'STAGE_CONSTRAINT_GENERATION' && 
                     stages.indexOf(currentStage) > stages.indexOf('STAGE_CONSTRAINT_GENERATION')) {
                // Update the progress to 100% complete
                const progressElement = updateConstraintGenerationProgress({ 
                    progress: 100, 
                    message: "Constraint generation complete!" 
                });
                
                // After a delay, refresh visualizations
                setTimeout(() => {
                    refreshVisualizations();
                }, 1000);
            }
        }
        
        // Handle constraint generation progress
        if (currentStage === 'STAGE_CONSTRAINT_GENERATION') {
            if (data.constraint_progress) {
                updateConstraintGenerationProgress(data.constraint_progress);
            } else {
                // If no specific progress data, just update with a simulated value
                updateConstraintGenerationProgress({ 
                    progress: Math.floor(Math.random() * 40) + 30, // Between 30% and 70%
                    message: "Generating constraints..."
                });
            }
        }
        
        // Update user requirement guess
        document.getElementById('userRequirementText').innerHTML = 
            data.user_requirement_guess ? formatTextWithLineBreaks(data.user_requirement_guess) : 'No requirements gathered yet.';
        
        // Update spatial understanding
        document.getElementById('spatialUnderstandingText').innerHTML = 
            data.spatial_understanding_record ? formatTextWithLineBreaks(data.spatial_understanding_record) : 'No spatial information gathered yet.';
        
        // Update key questions table
        const keyQuestionsTable = document.getElementById('keyQuestionsTable');
        keyQuestionsTable.innerHTML = '';
        
        // Count known questions to check if all are known
        let knownQuestions = 0;
        let totalQuestions = 0;
        
        if (data.key_questions && data.key_questions.length > 0) {
            totalQuestions = data.key_questions.length;
            
            data.key_questions.forEach(question => {
                const row = document.createElement('tr');
                
                const categoryCell = document.createElement('td');
                categoryCell.textContent = question.category;
                row.appendChild(categoryCell);
                
                const statusCell = document.createElement('td');
                statusCell.textContent = question.status;
                statusCell.className = question.status === '已知' ? 'status-known' : 'status-unknown';
                if (question.status === '已知') {
                    knownQuestions++;
                }
                row.appendChild(statusCell);
                
                const detailsCell = document.createElement('td');
                detailsCell.textContent = question.details || '';
                row.appendChild(detailsCell);
                
                keyQuestionsTable.appendChild(row);
            });
        }
        
        // Check if all questions are known (using either our count or the backend flag)
        const allQuestionsKnown = data.all_key_questions_known || 
                                (totalQuestions > 0 && knownQuestions === totalQuestions);
        
        // If all questions are known and we're still in requirement gathering stage
        if (allQuestionsKnown && currentStage === 'STAGE_REQUIREMENT_GATHERING') {
            // Add message to indicate we're moving to next stage
            addSystemMessage("All key questions have been answered! Moving to constraint generation stage...");
            
            // Automatically skip to next stage
            skipStage();
        }
        
        // Refresh visualizations if we're past the constraint generation stage
        if (stages.indexOf(currentStage) >= stages.indexOf('STAGE_CONSTRAINT_VISUALIZATION')) {
            refreshVisualizations();
        }
    })
    .catch(error => {
        console.error('Error refreshing state:', error);
    });
}

// Refresh visualizations
function refreshVisualizations() {
    fetch(`/api/visualize?session_id=${currentSessionId}`)
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error fetching visualizations:', data.error);
            return;
        }
        
        if (data.visualizations && data.visualizations.length > 0) {
            // Find and display the room graph
            const roomGraphImg = data.visualizations.find(path => 
                path.includes('constraints_visualization') && !path.includes('table'));
                
            if (roomGraphImg) {
                document.getElementById('roomGraphImg').src = roomGraphImg;
                document.getElementById('roomGraphImg').classList.remove('d-none');
                document.getElementById('roomGraphPlaceholder').classList.add('d-none');
            }
            
            // Find and display the constraints table
            const constraintsTableImg = data.visualizations.find(path => 
                path.includes('table') || path.includes('_table'));
                
            if (constraintsTableImg) {
                document.getElementById('constraintsTableImg').src = constraintsTableImg;
                document.getElementById('constraintsTableImg').classList.remove('d-none');
                document.getElementById('constraintsTablePlaceholder').classList.add('d-none');
            }
            
            // Find and display layout solution if available
            const layoutImg = data.visualizations.find(path => 
                path.includes('solution') || path.includes('layout'));
                
            if (layoutImg) {
                document.getElementById('layoutImg').src = layoutImg;
                document.getElementById('layoutImg').classList.remove('d-none');
                document.getElementById('layoutPlaceholder').classList.add('d-none');
            }
        }
    })
    .catch(error => {
        console.error('Error refreshing visualizations:', error);
    });
}

// Add a user message to the chat history
function addUserMessage(message) {
    const chatHistory = document.getElementById('chatHistory');
    const messageElement = document.createElement('div');
    messageElement.className = 'user-message';
    messageElement.innerHTML = formatTextWithLineBreaks(message);
    messageElement.classList.add('fade-in');
    chatHistory.appendChild(messageElement);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Add a system message to the chat history
function addSystemMessage(message, isLoading = false) {
    const chatHistory = document.getElementById('chatHistory');
    const messageElement = document.createElement('div');
    messageElement.className = 'system-message';
    
    if (isLoading) {
        messageElement.classList.add('loading-message');
        messageElement.innerHTML = `
            <div class="spinner-border spinner-border-sm text-light me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            ${message}
        `;
    } else {
        // Check if message is an object with a question property
        if (typeof message === 'object' && message.question) {
            messageElement.innerHTML = formatTextWithLineBreaks(message.question);
        } else {
            messageElement.innerHTML = formatTextWithLineBreaks(message);
        }
    }
    
    messageElement.classList.add('fade-in');
    chatHistory.appendChild(messageElement);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Remove the loading message
function removeLoadingMessage() {
    const chatHistory = document.getElementById('chatHistory');
    const loadingMessage = chatHistory.querySelector('.loading-message');
    if (loadingMessage) {
        chatHistory.removeChild(loadingMessage);
    }
}

// Format text with line breaks
function formatTextWithLineBreaks(text) {
    if (!text) return '';
    return text.replace(/\n/g, '<br>');
}

// Add a constraint generation progress indicator to the chat
function updateConstraintGenerationProgress(progress) {
    // Check if progress indicator already exists
    let progressElement = document.querySelector('.constraint-generation-progress');
    
    if (!progressElement) {
        // Create new progress indicator
        progressElement = document.createElement('div');
        progressElement.className = 'constraint-generation-progress system-message';
        progressElement.innerHTML = `
            <strong>Generating constraints...</strong>
            <div class="progress">
                <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" 
                     style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
            <div class="constraint-generation-status">Initializing...</div>
        `;
        
        // Add to chat history
        const chatHistory = document.getElementById('chatHistory');
        chatHistory.appendChild(progressElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    // Update progress percentage
    const progressBar = progressElement.querySelector('.progress-bar');
    let percentComplete = 0;
    
    if (progress) {
        if (typeof progress === 'number') {
            percentComplete = progress;
        } else if (progress.progress) {
            percentComplete = progress.progress;
        }
        
        // Update status message if provided
        if (progress.message) {
            progressElement.querySelector('.constraint-generation-status').textContent = progress.message;
        }
    }
    
    // Ensure we're showing at least some progress in constraint generation stage
    if (percentComplete === 0 && currentStage === 'STAGE_CONSTRAINT_GENERATION') {
        // Simulate progress if none provided
        const fakeProgress = Math.floor(Math.random() * 30) + 10; // Between 10 and 40%
        progressBar.style.width = `${fakeProgress}%`;
        progressBar.setAttribute('aria-valuenow', fakeProgress);
    } else {
        progressBar.style.width = `${percentComplete}%`;
        progressBar.setAttribute('aria-valuenow', percentComplete);
    }
    
    return progressElement;
}

// Poll for state changes when in certain stages
function pollForStateChanges() {
    if (!currentSessionId) return;
    
    // Only poll when in processing-heavy stages
    const pollingStages = [
        'STAGE_CONSTRAINT_GENERATION',
        'STAGE_SOLUTION_GENERATION'
    ];
    
    if (pollingStages.includes(currentStage)) {
        refreshState();
        
        // Add or update constraint generation progress
        if (currentStage === 'STAGE_CONSTRAINT_GENERATION') {
            updateConstraintGenerationProgress();
        }
        
        // Continue polling every 2 seconds
        setTimeout(pollForStateChanges, 2000);
    }
}

// Initialize periodic state refresh with varied frequencies
setInterval(() => {
    if (currentSessionId) {
        refreshState();
        
        // If in constraint generation or solution generation, poll more frequently
        if (currentStage === 'STAGE_CONSTRAINT_GENERATION' || 
            currentStage === 'STAGE_SOLUTION_GENERATION') {
            pollForStateChanges();
        }
    }
}, 5000); // Regular refresh every 5 seconds