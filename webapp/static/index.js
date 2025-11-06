// Get DOM elements
const submitButton = document.getElementById('submit-button');
const promptInput = document.getElementById('prompt-input');
const statusMessage = document.getElementById('status-message');
const outputCode = document.getElementById('output-code');

// Add event listener to submit button
submitButton.addEventListener('click', async (event) => {
    // Prevent default form submission
    event.preventDefault();

    // Get the prompt text
    const promptText = promptInput.value.trim();

    // Get the selected mode
    const modeAVM = document.getElementById('mode-avm').checked;
    const bicepMode = modeAVM ? 'avm' : 'classic';

    // Validate input
    if (!promptText) {
        statusMessage.textContent = 'Please enter a prompt.';
        statusMessage.className = 'text-sm text-red-600 mb-4';
        return;
    }

    // Display initial status
    statusMessage.textContent = 'Starting...';
    statusMessage.className = 'text-sm text-blue-600 mb-4 font-semibold';

    // Disable button during request
    submitButton.disabled = true;
    submitButton.textContent = 'Generating...';
    submitButton.className = 'w-full bg-gray-400 text-white py-2 px-4 rounded-md cursor-not-allowed transition';

    try {
        // Make POST request to /generate endpoint and handle SSE stream
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: promptText,
                mode: bicepMode
            })
        });

        if (!response.ok) {
            // Handle non-200 response
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.error || `Error: ${response.status} ${response.statusText}`;

            statusMessage.textContent = errorMessage;
            statusMessage.className = 'text-sm text-red-600 mb-4 font-semibold';

            outputCode.textContent = '// Error occurred. Please try again.';
            Prism.highlightElement(outputCode);

            // Re-enable button
            submitButton.disabled = false;
            submitButton.textContent = 'Generate Bicep Template';
            submitButton.className = 'w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition';
            return;
        }

        // Read the SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let streamedCode = '';  // Accumulate streamed code

        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Process complete SSE messages
            const lines = buffer.split('\n\n');
            buffer = lines.pop(); // Keep incomplete message in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const jsonData = line.substring(6);
                    try {
                        const event = JSON.parse(jsonData);

                        if (event.status === 'progress') {
                            // Update status with progress message
                            statusMessage.textContent = event.message;
                            statusMessage.className = 'text-sm text-blue-600 mb-4 font-semibold';
                        } else if (event.status === 'streaming') {
                            // Code streaming started
                            statusMessage.textContent = event.message;
                            statusMessage.className = 'text-sm text-blue-600 mb-4 font-semibold';
                            streamedCode = '';  // Reset streamed code
                            outputCode.textContent = '';  // Clear output
                        } else if (event.status === 'chunk') {
                            // Append streaming chunk to output
                            streamedCode += event.content;
                            outputCode.textContent = streamedCode;
                            // Re-apply Prism syntax highlighting on each chunk
                            Prism.highlightElement(outputCode);
                        } else if (event.status === 'complete') {
                            // Extract and display final Bicep code
                            const bicepCode = event.bicep || streamedCode || '// No code generated';
                            outputCode.textContent = bicepCode;

                            // Re-apply Prism syntax highlighting
                            Prism.highlightElement(outputCode);

                            // Show success message
                            statusMessage.textContent = '✅ Template generated successfully!';
                            statusMessage.className = 'text-sm text-green-600 mb-4 font-semibold';

                            // Clear success message after 3 seconds
                            setTimeout(() => {
                                statusMessage.textContent = '';
                            }, 3000);
                        } else if (event.status === 'error') {
                            // Handle error
                            statusMessage.textContent = event.error;
                            statusMessage.className = 'text-sm text-red-600 mb-4 font-semibold';

                            outputCode.textContent = '// Error occurred. Please try again.';
                            Prism.highlightElement(outputCode);
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }

    } catch (error) {
        // Handle network errors
        console.error('Network error:', error);

        statusMessage.textContent = `Network error: ${error.message}. Please check your connection and try again.`;
        statusMessage.className = 'text-sm text-red-600 mb-4 font-semibold';

        // Clear output code block
        outputCode.textContent = '// Network error occurred.';
        Prism.highlightElement(outputCode);

    } finally {
        // Re-enable button
        submitButton.disabled = false;
        submitButton.textContent = 'Generate Template';
        submitButton.className = 'w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition';
    }
});

// Optional: Allow Enter key to submit (Ctrl+Enter for textarea)
promptInput.addEventListener('keydown', (event) => {
    if (event.ctrlKey && event.key === 'Enter') {
        submitButton.click();
    }
});

// Function to copy example prompt to textarea
function useExample(exampleText) {
    promptInput.value = exampleText;
    promptInput.focus();
    // Scroll to the textarea
    promptInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
}
