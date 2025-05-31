document.addEventListener('DOMContentLoaded', () => {
    const chatOutput = document.getElementById('chat-output');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
        messageDiv.textContent = text;
        chatOutput.appendChild(messageDiv);
        chatOutput.scrollTop = chatOutput.scrollHeight; // Scroll to the bottom
    }

    async function sendMessageToServer(messageText) {
        addMessage(messageText, 'user');
        chatInput.value = ''; // Clear input field

        try {
            // This is where you send the message to your backend server
            // The backend server will then invoke your C control program
            const response = await fetch('/api/chatbot', { // Example API endpoint
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command: messageText }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown server error' }));
                throw new Error(`Server error: ${response.status} - ${errorData.detail || response.statusText}`);
            }

            const data = await response.json();
            addMessage(data.reply, 'bot');

        } catch (error) {
            console.error('Error sending message:', error);
            addMessage(`Error: ${error.message}`, 'bot');
        }
    }

    sendButton.addEventListener('click', () => {
        const messageText = chatInput.value.trim();
        if (messageText) {
            sendMessageToServer(messageText);
        }
    });

    chatInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            const messageText = chatInput.value.trim();
            if (messageText) {
                sendMessageToServer(messageText);
            }
        }
    });
});
