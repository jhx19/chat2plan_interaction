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
        
        // 处理响应（根据当前阶段）
        if (typeof data.response === 'string') {
            // 只有在response不为空时才添加到聊天窗口
            if (data.response.trim()) {
                addSystemMessage(data.response);
            } else {
                console.log("收到空响应，检查系统状态...");
                // 立即刷新状态以检查关键问题列表
                refreshState();
            }
        } else if (data.response && typeof data.response === 'object') {
            if (data.response.question) {
                addSystemMessage(data.response.question);
            } else {
                addSystemMessage(JSON.stringify(data.response));
            }}
        
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

// 刷新系统状态
function refreshState() {
    if (!currentSessionId) return;
    
    fetch(`/api/state?session_id=${currentSessionId}`)
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('获取状态时出错:', data.error);
            return;
        }
        
        // 检查阶段变化
        const previousStage = currentStage;
        currentStage = data.current_stage;
        const stageChanged = previousStage !== currentStage;
        
        // 更新阶段描述和进度条
        document.getElementById('stageDescription').textContent = data.stage_description;
        updateProgressBar();
        
        // 如果阶段发生变化，显示通知
        if (stageChanged && previousStage) {
            addSystemMessage(`阶段已从 ${stageDisplayNames[previousStage]} 变更至 ${stageDisplayNames[currentStage]}`);
            
            // 如果刚进入约束条件生成阶段
            if (currentStage === 'STAGE_CONSTRAINT_GENERATION') {
                updateConstraintGenerationProgress({ progress: 10, message: "开始生成约束条件..." });
            }
        }
        
        // 约束条件生成阶段的进度更新
        if (currentStage === 'STAGE_CONSTRAINT_GENERATION') {
            if (data.constraint_progress) {
                updateConstraintGenerationProgress(data.constraint_progress);
            } else {
                // 如果没有特定的进度数据，使用模拟的进度值
                updateConstraintGenerationProgress({ 
                    progress: Math.floor(Math.random() * 40) + 30, // 进度在30%到70%之间
                    message: "正在生成约束条件..."
                });
            }
        }
        
        // 更新用户需求猜测
        document.getElementById('userRequirementText').innerHTML = 
            data.user_requirement_guess ? formatTextWithLineBreaks(data.user_requirement_guess) : '尚未收集需求。';
        
        // 更新空间理解
        document.getElementById('spatialUnderstandingText').innerHTML = 
            data.spatial_understanding_record ? formatTextWithLineBreaks(data.spatial_understanding_record) : '尚未收集空间信息。';
        
        // 更新关键问题表格并检查是否全部已知
        const keyQuestionsTable = document.getElementById('keyQuestionsTable');
        keyQuestionsTable.innerHTML = '';

        // 计算已知问题数量
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
            
            // 详细日志记录（调试用）
            console.log(`关键问题详情:`, data.key_questions);
            console.log(`已知问题数量: ${knownQuestions}, 总问题数量: ${totalQuestions}`);
            console.log(`当前阶段: ${currentStage}`);
            console.log(`条件检查: ${currentStage === 'STAGE_REQUIREMENT_GATHERING'} && ${knownQuestions === totalQuestions} && ${totalQuestions > 0}`);
            
            // 如果所有问题都已知且当前处于需求收集阶段，则自动进入下一阶段
            if (currentStage === 'STAGE_REQUIREMENT_GATHERING' && 
                knownQuestions === totalQuestions && 
                totalQuestions > 0) {
                console.log("所有关键问题已知！自动进入下一阶段...");
                
                // 显示提示消息
                addSystemMessage("所有关键问题都已回答！正在进入约束条件生成阶段...");
                
                // 延迟一秒后，直接调用API进入下一阶段
                setTimeout(() => {
                    console.log("执行自动跳转...");
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
                    .then(stageData => {
                        if (stageData.error) {
                            console.error('跳转阶段失败:', stageData.error);
                            return;
                        }
                        console.log('成功跳转至:', stageData.current_stage);
                        currentStage = stageData.current_stage;
                        document.getElementById('stageDescription').textContent = stageData.stage_description;
                        updateProgressBar();
                    })
                    .catch(error => {
                        console.error('跳转阶段时出错:', error);
                    });
                }, 1000);
            }
        }
        
        // 状态变化检查和可视化刷新
        // 如果阶段发生变化
        if (stageChanged) {
            // 如果是从约束生成阶段到可视化阶段
            if (previousStage === 'STAGE_CONSTRAINT_GENERATION' && 
                currentStage === 'STAGE_CONSTRAINT_VISUALIZATION') {
                
                console.log("检测到已进入可视化阶段，立即刷新可视化...");
                
                // 立即刷新一次
                refreshVisualizations();
                
                // 然后每秒刷新一次，持续10秒钟，以确保图片加载
                let refreshCount = 0;
                const refreshInterval = setInterval(() => {
                    refreshCount++;
                    console.log(`第 ${refreshCount} 次刷新可视化...`);
                    refreshVisualizations();
                    
                    if (refreshCount >= 10) {
                        clearInterval(refreshInterval);
                    }
                }, 1000);
            }
            
            // 如果是从约束生成阶段到后面任何阶段
            if (previousStage === 'STAGE_CONSTRAINT_GENERATION' && 
                stages.indexOf(currentStage) > stages.indexOf('STAGE_CONSTRAINT_GENERATION')) {
                
                // 更新约束生成进度为100%
                updateConstraintGenerationProgress({ 
                    progress: 100, 
                    message: "约束条件生成完成！" 
                });
            }
        }
        
        // 在约束可视化阶段或之后，刷新可视化
        if (stages.indexOf(currentStage) >= stages.indexOf('STAGE_CONSTRAINT_VISUALIZATION')) {
            console.log("在可视化阶段或之后，刷新可视化...");
            refreshVisualizations();
        }
    })
    .catch(error => {
        console.error('刷新状态时出错:', error);
    });
}

// 刷新可视化图片
function refreshVisualizations() {
    if (!currentSessionId) return;
    
    console.log("正在刷新可视化图片...");
    
    // 首先检查是否存在具体的文件名
    fetch(`/api/check_visualization_files?session_id=${currentSessionId}`)
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('检查可视化文件失败:', data.error);
            return;
        }
        
        console.log("可视化文件检查结果:", data);
        
        // 如果找到图片文件，直接使用它们
        if (data.files) {
            if (data.files.room_graph) {
                console.log("找到房间图:", data.files.room_graph);
                const imgElement = document.getElementById('roomGraphImg');
                imgElement.src = data.files.room_graph + "?t=" + new Date().getTime(); // 添加时间戳防止缓存
                imgElement.onload = function() {
                    console.log("房间图加载成功");
                    imgElement.classList.remove('d-none');
                    document.getElementById('roomGraphPlaceholder').classList.add('d-none');
                };
                imgElement.onerror = function() {
                    console.error("房间图加载失败:", data.files.room_graph);
                };
            }
            
            if (data.files.constraints_table) {
                console.log("找到约束表格:", data.files.constraints_table);
                const imgElement = document.getElementById('constraintsTableImg');
                imgElement.src = data.files.constraints_table + "?t=" + new Date().getTime(); // 添加时间戳防止缓存
                imgElement.onload = function() {
                    console.log("约束表格加载成功");
                    imgElement.classList.remove('d-none');
                    document.getElementById('constraintsTablePlaceholder').classList.add('d-none');
                };
                imgElement.onerror = function() {
                    console.error("约束表格加载失败:", data.files.constraints_table);
                };
            }
            
            if (data.files.layout) {
                console.log("找到布局方案:", data.files.layout);
                const imgElement = document.getElementById('layoutImg');
                imgElement.src = data.files.layout + "?t=" + new Date().getTime(); // 添加时间戳防止缓存
                imgElement.onload = function() {
                    console.log("布局方案加载成功");
                    imgElement.classList.remove('d-none');
                    document.getElementById('layoutPlaceholder').classList.add('d-none');
                };
                imgElement.onerror = function() {
                    console.error("布局方案加载失败:", data.files.layout);
                };
            }
            
            return; // 如果已经找到具体文件，不需要执行下面的通用搜索
        }
        
        // 如果没有通过具体文件名找到，则使用通用搜索
        fetch(`/api/visualize?session_id=${currentSessionId}`)
        .then(response => response.json())
        .then(visualizeData => {
            if (visualizeData.error) {
                console.error('获取可视化图片失败:', visualizeData.error);
                return;
            }
            
            console.log("获取到的可视化图片:", visualizeData.visualizations);
            
            if (visualizeData.visualizations && visualizeData.visualizations.length > 0) {
                // 之前的查找逻辑保持不变
                // 找到并显示房间图
                const roomGraphImg = visualizeData.visualizations.find(path => 
                    path.includes('constraints_visualization') && !path.includes('table'));
                    
                if (roomGraphImg) {
                    console.log("找到房间图:", roomGraphImg);
                    const imgElement = document.getElementById('roomGraphImg');
                    imgElement.src = roomGraphImg + "?t=" + new Date().getTime(); // 添加时间戳防止缓存
                    imgElement.onload = function() {
                        console.log("房间图加载成功");
                        imgElement.classList.remove('d-none');
                        document.getElementById('roomGraphPlaceholder').classList.add('d-none');
                    };
                    imgElement.onerror = function() {
                        console.error("房间图加载失败:", roomGraphImg);
                    };
                }
                
                // 找到并显示约束表格
                const constraintsTableImg = visualizeData.visualizations.find(path => 
                    path.includes('table') || path.includes('_table'));
                    
                if (constraintsTableImg) {
                    console.log("找到约束表格:", constraintsTableImg);
                    const imgElement = document.getElementById('constraintsTableImg');
                    imgElement.src = constraintsTableImg + "?t=" + new Date().getTime(); // 添加时间戳防止缓存
                    imgElement.onload = function() {
                        console.log("约束表格加载成功");
                        imgElement.classList.remove('d-none');
                        document.getElementById('constraintsTablePlaceholder').classList.add('d-none');
                    };
                    imgElement.onerror = function() {
                        console.error("约束表格加载失败:", constraintsTableImg);
                    };
                }
                
                // 找到并显示布局方案
                const layoutImg = visualizeData.visualizations.find(path => 
                    path.includes('solution') || path.includes('layout'));
                    
                if (layoutImg) {
                    console.log("找到布局方案:", layoutImg);
                    const imgElement = document.getElementById('layoutImg');
                    imgElement.src = layoutImg + "?t=" + new Date().getTime(); // 添加时间戳防止缓存
                    imgElement.onload = function() {
                        console.log("布局方案加载成功");
                        imgElement.classList.remove('d-none');
                        document.getElementById('layoutPlaceholder').classList.add('d-none');
                    };
                    imgElement.onerror = function() {
                        console.error("布局方案加载失败:", layoutImg);
                    };
                }
            } else {
                console.log("没有找到可视化图片");
            }
        })
        .catch(error => {
            console.error('刷新可视化错误:', error);
        });
    })
    .catch(error => {
        console.error('检查可视化文件错误:', error);
        
        // 如果检查文件API失败，仍尝试通用搜索
        fetch(`/api/visualize?session_id=${currentSessionId}`)
        .then(response => response.json())
        .then(visualizeData => {
            // 处理通用搜索结果，与上面相同的逻辑
            // ...
        })
        .catch(error => {
            console.error('刷新可视化错误:', error);
        });
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