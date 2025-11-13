const submitButton = document.getElementById('submit-button');
const promptInput = document.getElementById('prompt-input');
const statusMessage = document.getElementById('status-message');
const outputCode = document.getElementById('output-code');

let abortController = null;
let isGenerating = false;

submitButton.addEventListener('click', async (event) => {
    event.preventDefault();

    if (isGenerating) {
        return;
    }

    isGenerating = true;

    const promptText = promptInput.value.trim();
    const modeAVM = document.getElementById('mode-avm').checked;
    const bicepMode = modeAVM ? 'avm' : 'classic';

    if (!promptText) {
        statusMessage.textContent = 'Please enter a prompt.';
        statusMessage.className = 'text-sm text-red-600 mb-4';
        isGenerating = false;
        return;
    }

    statusMessage.textContent = 'Starting...';
    statusMessage.className = 'text-sm text-blue-600 mb-4 font-semibold';

    document.getElementById('debug-total-time').textContent = '-';
    document.getElementById('debug-search-time').textContent = '-';
    document.getElementById('debug-ai-time').textContent = '-';
    document.getElementById('debug-search-results').textContent = '-';
    document.getElementById('debug-context-size').textContent = '-';
    document.getElementById('debug-mode').textContent = '-';

    document.getElementById('search-content-code').textContent = 'No search content available';
    const searchContentContainer = document.getElementById('search-content-container');
    const toggleSearchBtn = document.getElementById('toggle-search-content-btn');
    searchContentContainer.classList.add('hidden');
    toggleSearchBtn.textContent = 'Show Content';

    const codePre = document.getElementById('code-pre');
    codePre.style.visibility = 'hidden';

    submitButton.disabled = true;
    submitButton.textContent = 'Generating...';
    submitButton.className = 'w-full bg-gray-400 text-white py-2 px-4 rounded-md cursor-not-allowed transition';

    try {
        if (abortController) {
            abortController.abort();
        }

        abortController = new AbortController();

        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: promptText,
                mode: bicepMode
            }),
            signal: abortController.signal
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.error || `Error: ${response.status} ${response.statusText}`;

            statusMessage.textContent = errorMessage;
            statusMessage.className = 'text-sm text-red-600 mb-4 font-semibold';

            outputCode.textContent = '// Error occurred. Please try again.';
            Prism.highlightElement(outputCode);
            codePre.style.visibility = 'visible';

            submitButton.disabled = false;
            submitButton.textContent = 'Generate Bicep Template';
            submitButton.className = 'w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition';
            isGenerating = false;
            return;
        }

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
                            statusMessage.textContent = event.message;
                            statusMessage.className = 'text-sm text-blue-600 mb-4 font-semibold';
                        } else if (event.status === 'debug') {
                            const debug = event.debug;
                            const modeAVM = document.getElementById('mode-avm').checked;
                            const bicepMode = modeAVM ? 'AVM' : 'Classic';

                            document.getElementById('debug-total-time').textContent = debug.total_time;
                            document.getElementById('debug-search-time').textContent = debug.search_time;
                            document.getElementById('debug-ai-time').textContent = debug.ai_time;
                            document.getElementById('debug-search-results').textContent = debug.result_count + ' documents';
                            document.getElementById('debug-context-size').textContent = debug.context_size;
                            document.getElementById('debug-mode').textContent = bicepMode;

                            const searchContentCode = document.getElementById('search-content-code');
                            if (debug.search_content && debug.search_content !== 'N/A') {
                                searchContentCode.textContent = debug.search_content;
                            } else {
                                searchContentCode.textContent = debug.search_content || 'No search content available';
                            }
                        } else if (event.status === 'complete') {
                            const bicepCode = event.bicep || '// No code generated';
                            outputCode.textContent = bicepCode;

                            Prism.highlightElement(outputCode);
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
                            Prism.highlightElement(outputCode);
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
        Prism.highlightElement(outputCode);
        codePre.style.visibility = 'visible';

    } finally {
        isGenerating = false;
        submitButton.disabled = false;
        submitButton.textContent = 'Generate Template';
        submitButton.className = 'w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition';
    }
});

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

function toggleDebug() {
    const content = document.getElementById('debug-content');
    const arrow = document.getElementById('debug-arrow');
    if (content.classList.contains('hidden')) {
        content.classList.remove('hidden');
        arrow.style.transform = 'rotate(0deg)';
    } else {
        content.classList.add('hidden');
        arrow.style.transform = 'rotate(-90deg)';
    }
}

function toggleSearchContent() {
    const container = document.getElementById('search-content-container');
    const button = document.getElementById('toggle-search-content-btn');

    if (container.classList.contains('hidden')) {
        container.classList.remove('hidden');
        button.textContent = 'Hide Content';
    } else {
        container.classList.add('hidden');
        button.textContent = 'Show Content';
    }
}

let isWrapped = false;
function toggleWordWrap() {
    const codePre = document.getElementById('code-pre');
    const outputCode = document.getElementById('output-code');
    const wrapToggle = document.getElementById('wrap-toggle');

    isWrapped = !isWrapped;

    if (isWrapped) {
        codePre.style.whiteSpace = 'pre-wrap';
        codePre.style.overflow = 'break-word';
        codePre.style.overflowWrap = 'break-word';
        outputCode.style.whiteSpace = 'pre-wrap';
        wrapToggle.textContent = 'Wrap: On';
    } else {
        codePre.style.whiteSpace = 'pre';
        codePre.style.overflow = 'normal';
        codePre.style.overflowWrap = 'normal';
        outputCode.style.whiteSpace = 'pre';
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

function openImageModal(imgElement) {
    const modal = document.getElementById('image-modal');
    const modalImage = document.getElementById('modal-image');

    modalImage.src = imgElement.src;
    modalImage.alt = imgElement.alt;
    modal.classList.remove('hidden');

    document.body.style.overflow = 'hidden';
}

function closeImageModal() {
    const modal = document.getElementById('image-modal');
    modal.classList.add('hidden');

    document.body.style.overflow = 'auto';
}

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeImageModal();
    }
});
