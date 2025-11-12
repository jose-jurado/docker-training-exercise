// Configuration
const API_ENDPOINT = '/api/chat';
const MODEL_NAME = 'Mistral-7B-Instruct-v0.2';

// DOM Elements
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const messagesContainer = document.getElementById('messages');
const statusDiv = document.getElementById('status');

// Conversation history
let conversationHistory = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    addMessage('assistant', 'Hello! I\'m your RAG chatbot. Ask me anything about your documents.');
    userInput.focus();
});

// Handle form submission
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const message = userInput.value.trim();
    if (!message) return;
    
    // Add user message to UI
    addMessage('user', message);
    
    // Add to conversation history
    conversationHistory.push({
        role: 'user',
        content: message
    });
    
    // Clear input and disable form
    userInput.value = '';
    setLoading(true);
    
    try {
        // Show typing indicator
        const typingId = addTypingIndicator();
        
        // Call chatbot API
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: MODEL_NAME,
                messages: conversationHistory,
                temperature: 0.7,
                max_tokens: 512
            })
        });
        
        // Remove typing indicator
        removeTypingIndicator(typingId);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Extract assistant response
        const assistantMessage = data.choices[0].message.content;
        
        // Add assistant message to UI
        addMessage('assistant', assistantMessage);
        
        // Add to conversation history
        conversationHistory.push({
            role: 'assistant',
            content: assistantMessage
        });
        
    } catch (error) {
        console.error('Error:', error);
        removeTypingIndicator();
        addMessage('error', `Error: ${error.message}. Please try again.`);
    } finally {
        setLoading(false);
        userInput.focus();
    }
});

// Add message to chat
function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.textContent = content;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Add typing indicator
function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.id = 'typing-indicator';
    typingDiv.textContent = 'Thinking';
    messagesContainer.appendChild(typingDiv);
    scrollToBottom();
    return 'typing-indicator';
}

// Remove typing indicator
function removeTypingIndicator(id = 'typing-indicator') {
    const typingDiv = document.getElementById(id);
    if (typingDiv) {
        typingDiv.remove();
    }
}

// Set loading state
function setLoading(isLoading) {
    sendButton.disabled = isLoading;
    userInput.disabled = isLoading;
    sendButton.textContent = isLoading ? 'Sending...' : 'Send';
}

// Scroll to bottom of chat
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Handle Enter key (optional: shift+enter for new line)
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});
