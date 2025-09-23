import { APIClient } from './core/api-client.js';
import { StateManager } from './core/state-manager.js';
import { formatTime, formatFileSize, formatResponse } from './utils/formatters.js';

class RAGInterface {
    constructor() {
        this.apiClient = new APIClient();
        this.stateManager = new StateManager();
        this.initializeElements();
        this.bindEvents();
        this.initializeSystem();
    }

    initializeElements() {
        this.queryInput = document.getElementById('query-input');
        this.submitBtn = document.getElementById('submit-btn');
        this.clearBtn = document.getElementById('clear-btn');
        this.responseSection = document.getElementById('response-section');
        this.responseContent = document.getElementById('response-content');
        this.processingModal = document.getElementById('processing-modal');
        this.processingSteps = document.getElementById('processing-steps');
    }

    bindEvents() {
        this.submitBtn.addEventListener('click', () => this.submitQuery());
        this.clearBtn.addEventListener('click', () => this.clearQuery());
    }

    async initializeSystem() {
        console.log('System initializing...');
        this.stateManager.setSystemReady(true);
    }

    async submitQuery() {
        const query = this.queryInput.value.trim();
        if (!query) return;

        this.stateManager.setCurrentQuery(query);
        this.stateManager.addToHistory(query, 'pending');
        this.showProcessingModal();

        await this.apiClient.streamQuery(
            query,
            (progress) => this.handleProgress(progress),
            (result) => this.displayResponse(result),
            (error) => this.displayError(error)
        );

        this.hideProcessingModal();
        this.stateManager.updateHistoryStatus(query, 'completed');
    }

    handleProgress(data) {
        console.log('Progress:', data);
    }

    displayResponse(data) {
        this.responseContent.innerHTML = formatResponse(data.answer);
        this.responseSection.classList.remove('hidden');
    }

    displayError(error) {
        this.responseContent.innerHTML = `<div class="text-red-600">${error}</div>`;
        this.responseSection.classList.remove('hidden');
    }

    clearQuery() {
        this.queryInput.value = '';
        this.responseSection.classList.add('hidden');
    }

    showProcessingModal() {
        this.processingModal.classList.remove('hidden');
    }

    hideProcessingModal() {
        this.processingModal.classList.add('hidden');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.ragInterface = new RAGInterface();
});