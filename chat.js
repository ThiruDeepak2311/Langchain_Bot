// This file contains additional JavaScript for the chat application
// It can be imported in chat.html if needed for more complex functionality

/**
 * Initialize text-to-speech functionality
 */
function initTextToSpeech() {
    // Check if the browser supports the Web Speech API
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel(); // Cancel any ongoing speech
        return true;
    }
    return false;
}

/**
 * Speak text using the Web Speech API
 * @param {string} text - The text to speak
 */
function speakText(text) {
    if (!('speechSynthesis' in window)) {
        console.error('Text-to-speech not supported in this browser');
        return;
    }
    
    // Create a new utterance
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Configure the utterance
    utterance.lang = 'en-US';
    utterance.volume = 1; // 0 to 1
    utterance.rate = 1; // 0.1 to 10
    utterance.pitch = 1; // 0 to 2
    
    // Speak
    window.speechSynthesis.speak(utterance);
}

/**
 * Initialize speech recognition
 * @param {Function} callback - Function to call with recognized text
 */
function initSpeechRecognition(callback) {
    // Check if the browser supports the Web Speech API
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.error('Speech recognition not supported in this browser');
        return null;
    }
    
    // Create a new speech recognition instance
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    // Configure recognition
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    
    // Add event listeners
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        callback(transcript);
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
    };
    
    return recognition;
}

/**
 * Format code blocks in messages
 * @param {HTMLElement} element - The element containing code blocks
 */
function formatCodeBlocks(element) {
    // Find all code blocks
    const codeBlocks = element.querySelectorAll('pre code');
    
    // Add copy button to each code block
    codeBlocks.forEach((codeBlock) => {
        // Create copy button
        const copyButton = document.createElement('button');
        copyButton.innerHTML = '<i class="fas fa-copy"></i>';
        copyButton.className = 'absolute top-2 right-2 bg-gray-700 text-white rounded p-1 text-xs';
        copyButton.title = 'Copy to clipboard';
        
        // Add click event to copy button
        copyButton.addEventListener('click', () => {
            const code = codeBlock.textContent;
            navigator.clipboard.writeText(code).then(() => {
                copyButton.innerHTML = '<i class="fas fa-check"></i>';
                setTimeout(() => {
                    copyButton.innerHTML = '<i class="fas fa-copy"></i>';
                }, 2000);
            });
        });
        
        // Add button to code block container
        codeBlock.parentElement.style.position = 'relative';
        codeBlock.parentElement.appendChild(copyButton);
    });
}

/**
 * Export chat history as text
 * @param {Array} messages - Array of chat messages
 * @returns {string} - Formatted text of the chat history
 */
function exportChatHistory(messages) {
    let text = "# Chat History\n\n";
    
    messages.forEach((message) => {
        const role = message.role === 'user' ? 'You' : 'Chatbot';
        const content = message.content.replace(/<[^>]*>/g, ''); // Remove HTML tags
        
        text += `## ${role}\n${content}\n\n`;
    });
    
    return text;
}

// Export functions
if (typeof module !== 'undefined') {
    module.exports = {
        initTextToSpeech,
        speakText,
        initSpeechRecognition,
        formatCodeBlocks,
        exportChatHistory
    };
}