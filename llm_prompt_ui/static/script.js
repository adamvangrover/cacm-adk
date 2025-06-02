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

    function loadDoorDashReport() {
        const reportTabContent = document.getElementById('doordashReportTab');
        if (!reportTabContent) {
            console.error('Error: DoorDash report tab content area (doordashReportTab) not found.');
            return;
        }

        // Path relative to the root of the website, assuming 'static' is served at '/static/'
        // The Flask app.py will need to serve files from 'llm_prompt_ui/static' as '/static'
        // And the actual file is at 'llm_prompt_ui/static/content_scenarios/doordash_ma_balanced/synthesized_report_example.html'
        // So the path for fetch should be 'static/content_scenarios/doordash_ma_balanced/synthesized_report_example.html'
        // If index.html is at '/something', then relative path 'static/...' would be '/something/static/...'
        // Using absolute path from site root: '/static/content_scenarios/doordash_ma_balanced/synthesized_report_example.html'
        // For now, let's assume the index.html is served from a path where 'static/' is a direct child from the perspective of the browser.
        // Flask's url_for('static', filename='...') handles this by generating root-relative paths.
        // For direct fetch, if index.html is at root, then 'static/...' is fine.
        // If index.html is at e.g. /ui/, then 'static/...' would resolve to '/ui/static/...'.
        // The prompt uses `static/...` which implies it's relative to where index.html is served,
        // or the base URL is configured such that this path resolves correctly.
        // Given `url_for('static', ...)` is used elsewhere, this path should be `/static/...` if served by Flask at root.
        // Let's use the exact path from the prompt.
        const reportPath = '/static/content_scenarios/doordash_ma_balanced/synthesized_report_example.html';

        fetch(reportPath)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status} while fetching ${reportPath}`);
                }
                return response.text();
            })
            .then(html => {
                reportTabContent.innerHTML = html;
            })
            .catch(error => {
                console.error('Error loading DoorDash report:', error);
                if (reportTabContent) {
                    reportTabContent.innerHTML = '<p>Error loading DoorDash report. See console for details.</p>';
                }
            });
    }

    // Load the DoorDash report content
    loadDoorDashReport();

    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Deactivate all tabs and buttons
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Activate the clicked button and its corresponding tab content
            button.classList.add('active');
            const targetTabId = button.dataset.tab;
            const targetTabContent = document.getElementById(targetTabId);
            if (targetTabContent) {
                targetTabContent.classList.add('active');
            } else {
                console.error('Error: Tab content with ID ' + targetTabId + ' not found.');
            }
        });
    });
});
