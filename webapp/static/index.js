// Get DOM elements
const submitButton = document.getElementById('submit-button');
const promptInput = document.getElementById('prompt-input');
const statusMessage = document.getElementById('status-message');
const outputCode = document.getElementById('output-code');

submitButton.addEventListener('click', async (event) => {
    event.preventDefault();

    const promptText = promptInput.value.trim();
    const modeAVM = document.getElementById('mode-avm').checked;
    const bicepMode = modeAVM ? 'avm' : 'classic';

    if (!promptText) {
        statusMessage.textContent = 'Please enter a prompt.';
        statusMessage.className = 'text-sm text-red-600 mb-4';
        return;
    }

    statusMessage.textContent = 'Starting...';
    statusMessage.className = 'text-sm text-blue-600 mb-4 font-semibold';

    // Hide the code output during generation
    const codePre = document.getElementById('code-pre');
    codePre.style.visibility = 'hidden';

    submitButton.disabled = true;
    submitButton.textContent = 'Generating...';
    submitButton.className = 'w-full bg-gray-400 text-white py-2 px-4 rounded-md cursor-not-allowed transition';

    try {
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
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.error || `Error: ${response.status} ${response.statusText}`;

            statusMessage.textContent = errorMessage;
            statusMessage.className = 'text-sm text-red-600 mb-4 font-semibold';

            outputCode.textContent = '// Error occurred. Please try again.';
            hljs.highlightElement(outputCode);
            codePre.style.visibility = 'visible';

            submitButton.disabled = false;
            submitButton.textContent = 'Generate Bicep Template';
            submitButton.className = 'w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition';
            return;
        }

        // Process Server-Sent Events for progress updates
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            const lines = buffer.split('\n\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const jsonData = line.substring(6);
                    try {
                        const event = JSON.parse(jsonData);

                        if (event.status === 'progress') {
                            // Update status message for progress updates
                            statusMessage.textContent = event.message;
                            statusMessage.className = 'text-sm text-blue-600 mb-4 font-semibold';
                        } else if (event.status === 'complete') {
                            // Set the final Bicep code (no streaming of content)
                            const bicepCode = event.bicep || '// No code generated';
                            outputCode.textContent = bicepCode;

                            // Apply syntax highlighting first, then show the code
                            hljs.highlightElement(outputCode);
                            codePre.style.visibility = 'visible';

                            statusMessage.textContent = '✅ Template generated successfully!';
                            statusMessage.className = 'text-sm text-green-600 mb-4 font-semibold';

                            setTimeout(() => {
                                statusMessage.textContent = '';
                            }, 3000);
                        } else if (event.status === 'error') {
                            statusMessage.textContent = event.error;
                            statusMessage.className = 'text-sm text-red-600 mb-4 font-semibold';

                            outputCode.textContent = '// Error occurred. Please try again.';
                            hljs.highlightElement(outputCode);
                            codePre.style.visibility = 'visible';
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }

    } catch (error) {
        console.error('Network error:', error);

        statusMessage.textContent = `Network error: ${error.message}. Please check your connection and try again.`;
        statusMessage.className = 'text-sm text-red-600 mb-4 font-semibold';

        outputCode.textContent = '// Network error occurred.';
        hljs.highlightElement(outputCode);
        codePre.style.visibility = 'visible';

    } finally {
        submitButton.disabled = false;
        submitButton.textContent = 'Generate Template';
        submitButton.className = 'w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition';
    }
});

// Allow Enter key to submit (Ctrl+Enter for textarea)
promptInput.addEventListener('keydown', (event) => {
    if (event.ctrlKey && event.key === 'Enter') {
        submitButton.click();
    }
});

function useExample(exampleText) {
    promptInput.value = exampleText;
    promptInput.focus();
    promptInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function toggleVisualizations() {
    const content = document.getElementById('visualizations-content');
    const arrow = document.getElementById('visualizations-arrow');
    if (content.style.display === 'none') {
        content.style.display = 'block';
        arrow.style.transform = 'rotate(0deg)';
    } else {
        content.style.display = 'none';
        arrow.style.transform = 'rotate(-90deg)';
    }
}

function toggleInstructions() {
    const content = document.getElementById('instructions-content');
    const arrow = document.getElementById('instructions-arrow');
    if (content.style.display === 'none') {
        content.style.display = 'block';
        arrow.style.transform = 'rotate(0deg)';
    } else {
        content.style.display = 'none';
        arrow.style.transform = 'rotate(-90deg)';
    }
}

let isWrapped = true;
function toggleWordWrap() {
    const codePre = document.getElementById('code-pre');
    const outputCode = document.getElementById('output-code');
    const wrapToggle = document.getElementById('wrap-toggle');
    const container = codePre.parentElement;

    isWrapped = !isWrapped;

    if (isWrapped) {
        codePre.style.whiteSpace = 'pre-wrap';
        codePre.style.wordWrap = 'break-word';
        codePre.style.overflowWrap = 'break-word';
        codePre.style.maxWidth = '100%';
        outputCode.style.whiteSpace = 'pre-wrap';
        container.style.overflowX = 'hidden';
        wrapToggle.textContent = 'Wrap: On';
    } else {
        codePre.style.whiteSpace = 'pre';
        codePre.style.wordWrap = 'normal';
        codePre.style.overflowWrap = 'normal';
        codePre.style.maxWidth = 'none';
        outputCode.style.whiteSpace = 'pre';
        container.style.overflowX = 'auto';
        wrapToggle.textContent = 'Wrap: Off';
    }
}

function copyCode() {
    const outputCode = document.getElementById('output-code');
    const copyButton = document.getElementById('copy-button');
    const codeText = outputCode.textContent;

    navigator.clipboard.writeText(codeText).then(() => {
        const originalText = copyButton.textContent;
        copyButton.textContent = '✓ Copied!';
        copyButton.className = 'text-xs bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded transition';

        setTimeout(() => {
            copyButton.textContent = originalText;
            copyButton.className = 'text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded transition';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        copyButton.textContent = '✗ Failed';
        setTimeout(() => {
            copyButton.textContent = '📋 Copy';
        }, 2000);
    });
}

function downloadCode() {
    const outputCode = document.getElementById('output-code');
    const downloadButton = document.getElementById('download-button');
    const codeText = outputCode.textContent;

    const blob = new Blob([codeText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = 'template.bicep';

    document.body.appendChild(link);
    link.click();

    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    const originalText = downloadButton.textContent;
    downloadButton.textContent = '✓ Downloaded!';
    downloadButton.className = 'text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded transition';

    setTimeout(() => {
        downloadButton.textContent = originalText;
        downloadButton.className = 'text-xs bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded transition';
    }, 2000);
}
