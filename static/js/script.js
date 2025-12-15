// Save as: static/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const messagesContainer = document.getElementById('messages-container');
    const messageCount = document.getElementById('message-count');
    const clearChatBtn = document.getElementById('clear-chat');
    const quickButtons = document.querySelectorAll('.quick-btn');
    const emojiBtn = document.getElementById('emoji-btn');
    const emojiContainer = document.getElementById('emoji-container');
    const setNameBtn = document.getElementById('set-name-btn');
    const nameModal = document.getElementById('name-modal');
    const closeModalBtns = document.querySelectorAll('.close-modal');
    const saveNameBtn = document.getElementById('save-name');
    const nameInput = document.getElementById('name-input');
    const usernameDisplay = document.getElementById('username-display');
    const currentTimeElement = document.getElementById('current-time');

    // Emoji list
    const emojis = ["😊", "😂", "🤣", "😍", "🥰", "😎", "🤔", "😴", "👍", "👋", 
                   "❤️", "🎉", "🔥", "⭐", "🌈", "🐱", "🐶", "🦄", "🍕", "☕",
                   "🎯", "✨", "💡", "🚀", "📚", "🎨", "🎵", "🏆", "💪", "🙏"];

    // Initialize
    let messageCounter = 0;
    updateCurrentTime();
    loadChatHistory();
    populateEmojis();

    // Update time every minute
    setInterval(updateCurrentTime, 60000);

    // Event Listeners
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);
    
    clearChatBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to clear all chat messages?')) {
            clearChat();
        }
    });

    quickButtons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.dataset.action;
            sendQuickAction(action);
        });
    });

    emojiBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        emojiContainer.classList.toggle('show');
    });

    document.addEventListener('click', function() {
        emojiContainer.classList.remove('show');
    });

    if (setNameBtn) {
        setNameBtn.addEventListener('click', function() {
            nameModal.classList.add('show');
        });
    }

    closeModalBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            nameModal.classList.remove('show');
        });
    });

    saveNameBtn.addEventListener('click', saveUserName);

    nameInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            saveUserName();
        }
    });

    // Functions
    function updateCurrentTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        if (currentTimeElement) {
            currentTimeElement.textContent = timeString;
        }
    }

    function populateEmojis() {
        emojis.forEach(emoji => {
            const span = document.createElement('span');
            span.textContent = emoji;
            span.addEventListener('click', function() {
                userInput.value += emoji;
                userInput.focus();
            });
            emojiContainer.appendChild(span);
        });
    }

    function addMessage(message, sender, isBot = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isBot ? 'bot-message' : 'user-message'}`;
        
        const now = new Date();
        const timeString = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas ${isBot ? 'fa-robot' : 'fa-user'}"></i>
            </div>
            <div class="message-content">
                <div class="message-sender">${sender}</div>
                <div class="message-text">${formatMessage(message)}</div>
                <div class="message-time">${timeString}</div>
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        if (!isBot) {
            messageCounter++;
            messageCount.textContent = messageCounter;
        }
    }

    function formatMessage(text) {
        // Convert markdown-like formatting
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>')
            .replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>');
    }

    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // Add user message to UI
        addMessage(message, 'You', false);
        userInput.value = '';

        // Show typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'message bot-message';
        typingIndicator.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-sender">AI Assistant</div>
                <div class="message-text typing">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                </div>
            </div>
        `;
        messagesContainer.appendChild(typingIndicator);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
            // Send message to server
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();

            // Remove typing indicator
            typingIndicator.remove();

            if (data.error) {
                addMessage('Sorry, I encountered an error. Please try again.', 'AI Assistant', true);
                return;
            }

            // Add bot response
            addMessage(data.response, 'AI Assistant', true);

            // Update username display if name was detected
            if (data.username && !document.querySelector('.welcome')) {
                updateUsernameDisplay(data.username);
            }

        } catch (error) {
            console.error('Error:', error);
            typingIndicator.remove();
            addMessage('Sorry, I encountered an error. Please try again.', 'AI Assistant', true);
        }
    }

    async function sendQuickAction(action) {
        try {
            const response = await fetch('/quick_actions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ action: action })
            });

            const data = await response.json();
            addMessage(data.response, 'AI Assistant', true);
        } catch (error) {
            console.error('Error:', error);
        }
    }

    async function loadChatHistory() {
        try {
            const response = await fetch('/history');
            const data = await response.json();
            
            if (data.history && data.history.length > 0) {
                // Clear welcome message
                messagesContainer.innerHTML = '';
                
                data.history.forEach(msg => {
                    addMessage(msg.user, 'You', false);
                    addMessage(msg.bot, 'AI Assistant', true);
                    messageCounter++;
                });
                
                messageCount.textContent = messageCounter;
            }
        } catch (error) {
            console.error('Error loading history:', error);
        }
    }

    async function clearChat() {
        try {
            const response = await fetch('/clear', {
                method: 'POST'
            });

            if (response.ok) {
                // Clear UI
                messagesContainer.innerHTML = '';
                messageCounter = 0;
                messageCount.textContent = '0';
                
                // Add welcome message
                const welcomeMessage = `🎉 Welcome to AI ChatBot! 🎉\n\nI'm your intelligent AI assistant ready to help you with:\n• Time and date information ⏰📅\n• Funny jokes and humor 😂\n• General conversation and questions 💬\n\nYou can type your message below or use the quick action buttons! 😊\n\nWhat would you like to do today?`;
                addMessage(welcomeMessage, 'AI Assistant', true);
            }
        } catch (error) {
            console.error('Error clearing chat:', error);
        }
    }

    async function saveUserName() {
        const name = nameInput.value.trim();
        if (!name) {
            alert('Please enter a name');
            return;
        }

        try {
            const response = await fetch('/update_username', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username: name })
            });

            const data = await response.json();

            if (data.success) {
                nameModal.classList.remove('show');
                nameInput.value = '';
                updateUsernameDisplay(name);
                addMessage(data.response, 'AI Assistant', true);
            } else {
                alert(data.error || 'Failed to save name');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to save name');
        }
    }

    function updateUsernameDisplay(name) {
        usernameDisplay.innerHTML = `<span class="welcome">Welcome, <strong>${name}</strong>!</span>`;
    }
});