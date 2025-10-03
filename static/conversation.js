// Conversational UI JavaScript

let currentProjectId = null;
let projects = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadProjects();
    setupEventListeners();
});

function setupEventListeners() {
    // New project form
    document.getElementById('newProjectForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await createProject();
    });

    // Enter to send message (Shift+Enter for new line)
    const messageInput = document.querySelector('.message-input');
    if (messageInput) {
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
}

// Load all projects
async function loadProjects() {
    try {
        const response = await fetch('/api/v2/projects');
        projects = await response.json();

        const projectsList = document.getElementById('projectsList');

        if (projects.length === 0) {
            projectsList.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #a0aec0;">
                    <p>No projects yet</p>
                    <p style="font-size: 12px; margin-top: 8px;">Create your first project to get started</p>
                </div>
            `;
            return;
        }

        projectsList.innerHTML = projects.map(project => `
            <div class="project-item ${currentProjectId === project.id ? 'active' : ''}"
                 onclick="selectProject('${project.id}')">
                <div class="project-name">${escapeHtml(project.name)}</div>
                <div class="project-status">
                    <span class="status-badge ${project.status}">${project.status}</span>
                    ${project.deployment_url ? '<i class="fas fa-link" style="margin-left: 8px;"></i>' : ''}
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading projects:', error);
        document.getElementById('projectsList').innerHTML = `
            <div style="padding: 20px; text-align: center; color: #e53e3e;">
                <p>Failed to load projects</p>
            </div>
        `;
    }
}

// Select a project
async function selectProject(projectId) {
    currentProjectId = projectId;

    // Update sidebar
    document.querySelectorAll('.project-item').forEach(item => {
        item.classList.remove('active');
    });
    event.currentTarget?.classList.add('active');

    // Load project and conversation
    await loadProjectConversation(projectId);
}

// Load project conversation
async function loadProjectConversation(projectId) {
    try {
        // Get project details
        const projectResponse = await fetch(`/api/v2/projects/${projectId}`);
        const project = await projectResponse.json();

        // Get conversation history
        const conversationResponse = await fetch(`/api/v2/projects/${projectId}/conversation`);
        const conversation = await conversationResponse.json();

        // Render chat interface
        renderChatInterface(project, conversation.messages);

    } catch (error) {
        console.error('Error loading conversation:', error);
    }
}

// Render chat interface
function renderChatInterface(project, messages) {
    const chatContainer = document.getElementById('chatContainer');

    chatContainer.innerHTML = `
        <div class="chat-header">
            <h2>${escapeHtml(project.name)}</h2>
            <div class="project-meta">
                <span class="status-badge ${project.status}">${project.status}</span>
                ${project.deployment_url ?
                    `<a href="${project.deployment_url}" target="_blank" style="margin-left: 12px; color: #667eea;">
                        <i class="fas fa-external-link-alt"></i> View Deployment
                    </a>` : ''}
            </div>
        </div>
        <div class="messages-container" id="messagesContainer">
            ${messages.length === 0 ? `
                <div style="text-align: center; color: #a0aec0; padding: 40px;">
                    <p>Start a conversation by typing a message below</p>
                </div>
            ` : messages.map(msg => renderMessage(msg)).join('')}
        </div>
        <div class="input-container">
            <div class="input-wrapper">
                <textarea class="message-input"
                          placeholder="Type your message... (Shift+Enter for new line)"
                          rows="2"
                          id="messageInput"></textarea>
                <button class="send-btn" onclick="sendMessage()">
                    <i class="fas fa-paper-plane"></i> Send
                </button>
            </div>
        </div>
    `;

    // Scroll to bottom
    scrollToBottom();

    // Re-setup event listeners for message input
    const messageInput = document.getElementById('messageInput');
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    messageInput.focus();
}

// Render a single message
function renderMessage(message) {
    const time = new Date(message.created_at).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
    });

    const icon = message.role === 'user' ? 'fa-user' :
                 message.role === 'assistant' ? 'fa-robot' : 'fa-info-circle';

    const roleDisplay = message.role === 'assistant' && message.agent_name ?
                       message.agent_name :
                       message.role.charAt(0).toUpperCase() + message.role.slice(1);

    return `
        <div class="message ${message.role}">
            <div class="message-avatar">
                <i class="fas ${icon}"></i>
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-role">${roleDisplay}</span>
                    ${message.agent_name && message.role === 'assistant' ?
                        `<span class="message-agent">(${message.agent_name})</span>` : ''}
                    <span class="message-time">${time}</span>
                </div>
                <div class="message-text">${escapeHtml(message.content)}</div>
                ${Object.keys(message.metadata || {}).length > 0 ? `
                    <div class="message-metadata">
                        <strong>Metadata:</strong> ${JSON.stringify(message.metadata, null, 2)}
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

// Send message
async function sendMessage() {
    if (!currentProjectId) {
        alert('Please select a project first');
        return;
    }

    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (!message) return;

    // Disable input
    messageInput.disabled = true;
    document.querySelector('.send-btn').disabled = true;

    // Add user message to UI immediately
    const messagesContainer = document.getElementById('messagesContainer');
    messagesContainer.innerHTML += renderMessage({
        role: 'user',
        content: message,
        created_at: new Date().toISOString(),
        metadata: {}
    });
    scrollToBottom();

    // Clear input
    messageInput.value = '';

    try {
        // Send to API
        const response = await fetch(`/api/v2/projects/${currentProjectId}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });

        if (!response.ok) throw new Error('Failed to send message');

        const assistantMessage = await response.json();

        // Add assistant response to UI
        messagesContainer.innerHTML += renderMessage(assistantMessage);
        scrollToBottom();

        // Reload projects to update status
        loadProjects();

    } catch (error) {
        console.error('Error sending message:', error);
        alert('Failed to send message. Please try again.');
    } finally {
        // Re-enable input
        messageInput.disabled = false;
        document.querySelector('.send-btn').disabled = false;
        messageInput.focus();
    }
}

// Create new project
async function createProject() {
    const name = document.getElementById('projectName').value;
    const description = document.getElementById('projectDescription').value;

    try {
        const response = await fetch('/api/v2/projects', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, description })
        });

        if (!response.ok) throw new Error('Failed to create project');

        const project = await response.json();

        // Hide modal
        hideNewProjectModal();

        // Reload projects
        await loadProjects();

        // Select the new project
        await selectProject(project.id);

    } catch (error) {
        console.error('Error creating project:', error);
        alert('Failed to create project. Please try again.');
    }
}

// Modal functions
function showNewProjectModal() {
    document.getElementById('newProjectModal').classList.add('active');
    document.getElementById('projectName').focus();
}

function hideNewProjectModal() {
    document.getElementById('newProjectModal').classList.remove('active');
    document.getElementById('newProjectForm').reset();
}

// Utility functions
function scrollToBottom() {
    const messagesContainer = document.getElementById('messagesContainer');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
