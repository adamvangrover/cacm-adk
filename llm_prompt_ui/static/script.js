document.addEventListener('DOMContentLoaded', () => {
    const promptButtons = document.querySelectorAll('.prompt-button');
    const llmResponseElement = document.getElementById('llm-response');

    if (!llmResponseElement) {
        console.error('Error: Element with ID "llm-response" not found.');
        return;
    }

    promptButtons.forEach(button => {
        button.addEventListener('click', () => {
            const promptText = button.dataset.prompt;
            if (promptText) {
                // Simulate LLM interaction by displaying the prompt text.
                // In a real application, you would send this promptText to an LLM API
                // and display the actual response.
                llmResponseElement.textContent = promptText;
                console.log('Prompt selected:', promptText);
            } else {
                llmResponseElement.textContent = 'Error: No prompt associated with this button.';
                console.error('Error: Button does not have a data-prompt attribute or it is empty.');
            }
        });
    });

    // Initial message
    if (promptButtons.length > 0) {
        llmResponseElement.textContent = 'Click one of the buttons above to see its prompt here.';
    } else {
        llmResponseElement.textContent = 'No prompt buttons found on the page.';
        console.warn('No elements with class "prompt-button" found.');
    }
});
