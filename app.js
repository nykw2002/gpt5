class RAGInterface {
    constructor() {
        this.isSystemReady = false;
        this.currentQuery = null;
        this.queryHistoryData = [];
        this.initializeElements();
        this.bindEvents();
        this.initializeSystem();
    }

    initializeElements() {
        // Input elements
        this.queryInput = document.getElementById('query-input');
        this.submitBtn = document.getElementById('submit-btn');
        this.clearBtn = document.getElementById('clear-btn');
        this.loadDocBtn = document.getElementById('load-doc-btn');
        this.currentDocInput = document.getElementById('current-doc');

        // Display elements
        this.statusElement = document.getElementById('status');
        this.statusText = document.getElementById('status-text');
        this.statusDetail = document.getElementById('status-detail');
        this.statusIcon = document.getElementById('status-icon');
        this.responseSection = document.getElementById('response-section');
        this.responseContent = document.getElementById('response-content');
        this.responseMeta = document.getElementById('response-meta');
        this.loadingModal = document.getElementById('loading-modal');
        this.loadingText = document.getElementById('loading-text');

        // Info elements
        this.charCount = document.getElementById('char-count');
        this.chunkCount = document.getElementById('chunk-count');
        this.docSize = document.getElementById('doc-size');
        this.sysStatus = document.getElementById('sys-status');
        this.sysChunks = document.getElementById('sys-chunks');
        this.queryHistoryElement = document.getElementById('query-history');
        this.queryTypeIndicator = document.getElementById('query-type-indicator');
        this.queryTypeText = document.getElementById('query-type-text');

        // Example queries
        this.exampleQueries = document.querySelectorAll('.example-query');
    }

    bindEvents() {
        // Query input events
        this.queryInput.addEventListener('input', () => this.handleQueryInput());
        this.queryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                this.submitQuery();
            }
        });

        // Button events
        this.submitBtn.addEventListener('click', () => this.submitQuery());
        this.clearBtn.addEventListener('click', () => this.clearQuery());
        this.loadDocBtn.addEventListener('click', () => this.loadDocument());

        // Example query events
        this.exampleQueries.forEach(btn => {
            btn.addEventListener('click', () => {
                this.queryInput.value = btn.textContent.trim();
                this.handleQueryInput();
            });
        });

        // Modal events
        this.loadingModal.addEventListener('click', (e) => {
            if (e.target === this.loadingModal) {
                // Don't allow closing modal during processing
            }
        });
    }

    handleQueryInput() {
        const query = this.queryInput.value;
        const charLength = query.length;

        // Update character count
        this.charCount.textContent = charLength;

        // Update submit button state
        this.submitBtn.disabled = !this.isSystemReady || charLength === 0 || charLength > 1000;

        // Update query type indicator
        if (query.length > 10) {
            this.updateQueryTypeIndicator(query);
        } else {
            this.queryTypeIndicator.classList.add('hidden');
        }
    }

    updateQueryTypeIndicator(query) {
        const queryLower = query.toLowerCase();
        let queryType = 'general';
        let color = 'bg-gray-100 text-gray-800';

        // Detect query type
        if (this.hasCountingPatterns(queryLower)) {
            queryType = 'counting';
            color = 'bg-blue-100 text-blue-800';
        } else if (this.hasAnalysisPatterns(queryLower)) {
            queryType = 'analysis';
            color = 'bg-green-100 text-green-800';
        } else if (this.hasSearchPatterns(queryLower)) {
            queryType = 'search';
            color = 'bg-purple-100 text-purple-800';
        }

        this.queryTypeText.textContent = `${queryType} query`;
        this.queryTypeIndicator.className = `mb-4 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${color}`;
        this.queryTypeIndicator.classList.remove('hidden');
    }

    hasCountingPatterns(query) {
        const patterns = ['how many', 'count', 'number of', 'total', 'list all', 'find all'];
        return patterns.some(pattern => query.includes(pattern));
    }

    hasAnalysisPatterns(query) {
        const patterns = ['analyze', 'compare', 'trend', 'summarize', 'evaluate', 'assess', 'review', 'report'];
        return patterns.some(pattern => query.includes(pattern));
    }

    hasSearchPatterns(query) {
        const patterns = ['find', 'search', 'look up', 'show where', 'what is', 'tell me about'];
        return patterns.some(pattern => query.includes(pattern));
    }

    async initializeSystem() {
        this.updateStatus('initializing', 'System initializing...', 'Loading RAG system and processing documents');

        try {
            // Simulate system initialization
            await this.delay(1000);

            // Check if system is ready
            const response = await this.makeRequest('/api/status');
            if (response.success) {
                this.isSystemReady = true;
                this.updateStatus('ready', 'System Ready', 'RAG system loaded and ready for queries');
                this.updateSystemInfo(response.data);
            } else {
                throw new Error(response.error || 'System initialization failed');
            }
        } catch (error) {
            console.error('Initialization error:', error);
            this.updateStatus('error', 'System Error', error.message);
        }
    }

    async loadDocument() {
        const docPath = this.currentDocInput.value.trim();
        if (!docPath) {
            alert('Please enter a document path');
            return;
        }

        this.loadDocBtn.disabled = true;
        this.loadDocBtn.textContent = 'Loading...';

        try {
            const response = await this.makeRequest('/api/load-document', {
                method: 'POST',
                body: JSON.stringify({ document_path: docPath })
            });

            if (response.success) {
                this.updateStatus('ready', 'Document Loaded', `Successfully loaded: ${docPath}`);
                this.updateSystemInfo(response.data);
            } else {
                throw new Error(response.error || 'Failed to load document');
            }
        } catch (error) {
            console.error('Document loading error:', error);
            this.updateStatus('error', 'Loading Failed', error.message);
        } finally {
            this.loadDocBtn.disabled = false;
            this.loadDocBtn.textContent = 'Load';
        }
    }

    async submitQuery() {
        if (!this.isSystemReady || !this.queryInput.value.trim()) {
            return;
        }

        const query = this.queryInput.value.trim();
        this.currentQuery = query;

        // Show loading modal
        this.showLoadingModal('Analyzing your request');

        try {
            // Add to history immediately
            this.addToHistory(query, 'pending');

            // Submit query
            const response = await this.makeRequest('/api/query', {
                method: 'POST',
                body: JSON.stringify({ question: query })
            });

            if (response.success) {
                this.displayResponse(response.data);
                this.updateHistoryStatus(query, 'completed');
            } else {
                throw new Error(response.error || 'Query processing failed');
            }
        } catch (error) {
            console.error('Query error:', error);
            this.displayError(error.message);
            this.updateHistoryStatus(query, 'failed');
        } finally {
            this.hideLoadingModal();
        }
    }

    displayResponse(data) {
        // Update response metadata
        const summarizedBadge = data.was_summarized ?
            '<span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">summarized</span>' : '';

        const qualityBadge = this.getQualityBadge(data.quality_metrics);

        this.responseMeta.innerHTML = `
            <div class="flex items-center space-x-4">
                <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-orange-100 text-orange-800">
                    ${data.query_classification?.primary_type || 'general'}
                </span>
                ${summarizedBadge}
                ${qualityBadge}
                <span class="text-gray-500">${data.chunks_analyzed || 0} chunks analyzed</span>
                <span class="text-gray-500">
                    ${data.query_classification?.confidence ?
                        `${Math.round(data.query_classification.confidence * 100)}% confidence` : ''}
                </span>
            </div>
        `;

        // Display answer
        this.responseContent.innerHTML = this.formatResponse(data.answer);

        // Add quality metrics section if available
        if (data.quality_metrics) {
            this.responseContent.innerHTML += this.createQualityMetricsSection(data.quality_metrics);
        }

        // Show response section
        this.responseSection.classList.remove('hidden');
        this.responseSection.classList.add('fade-in');

        // Scroll to response
        this.responseSection.scrollIntoView({ behavior: 'smooth' });
    }

    getQualityBadge(metrics) {
        if (!metrics || !metrics.overall_assessment) {
            return '<span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-600">metrics unavailable</span>';
        }

        const overall = metrics.overall_assessment;
        const score = overall.average_score;

        if (overall.acceptable) {
            return `<span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">quality: ${score}%</span>`;
        } else {
            return `<span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800">needs review: ${score}%</span>`;
        }
    }

    createQualityMetricsSection(metrics) {
        const overall = metrics.overall_assessment;
        const needsReview = overall.needs_review;

        return `
            <div class="mt-6 border-t pt-6">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold">Quality Metrics</h3>
                    <div class="flex items-center space-x-2">
                        <span class="text-sm font-medium">Overall: ${overall.average_score}%</span>
                        <div class="w-3 h-3 rounded-full ${needsReview ? 'bg-red-500' : 'bg-green-500'}"></div>
                        ${needsReview ? '<span class="text-xs text-red-600 font-medium">REVIEW REQUIRED</span>' : '<span class="text-xs text-green-600 font-medium">ACCEPTABLE</span>'}
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    ${this.createMetricCard('Groundedness', metrics.groundedness, 'How well the answer is supported by source data')}
                    ${this.createMetricCard('Accuracy', metrics.accuracy, 'Correctness of facts and information')}
                    ${this.createMetricCard('Relevance', metrics.relevance, 'How well the answer addresses the question')}
                </div>

                <div class="bg-gray-50 rounded-lg p-4">
                    <h4 class="font-medium text-gray-800 mb-2">Assessment Summary</h4>
                    <p class="text-sm text-gray-600">${overall.summary}</p>

                    <div class="mt-3">
                        <button onclick="ragInterface.toggleMetricsDetails()"
                                class="text-sm text-orange-600 hover:text-orange-700 font-medium">
                            View Detailed Breakdown →
                        </button>
                    </div>
                </div>

                <div id="metrics-details" class="hidden mt-4 space-y-3">
                    ${this.createDetailedMetricBreakdown('Groundedness', metrics.groundedness)}
                    ${this.createDetailedMetricBreakdown('Accuracy', metrics.accuracy)}
                    ${this.createDetailedMetricBreakdown('Relevance', metrics.relevance)}
                </div>
            </div>
        `;
    }

    createMetricCard(title, metric, description) {
        const score = metric.score;
        const isGood = score >= 80;
        const progressColor = isGood ? 'bg-green-500' : (score >= 60 ? 'bg-yellow-500' : 'bg-red-500');
        const textColor = isGood ? 'text-green-700' : (score >= 60 ? 'text-yellow-700' : 'text-red-700');
        const bgColor = isGood ? 'bg-green-50' : (score >= 60 ? 'bg-yellow-50' : 'bg-red-50');

        return `
            <div class="border rounded-lg p-4 ${bgColor}">
                <div class="flex items-center justify-between mb-2">
                    <h4 class="font-medium text-gray-800">${title}</h4>
                    <span class="text-lg font-bold ${textColor}">${score}%</span>
                </div>

                <div class="w-full bg-gray-200 rounded-full h-2 mb-2">
                    <div class="${progressColor} h-2 rounded-full transition-all duration-300"
                         style="width: ${score}%"></div>
                </div>

                <p class="text-xs text-gray-600">${description}</p>
                ${score < 80 ? '<div class="mt-2 text-xs text-red-600 font-medium">⚠ Requires Review</div>' : ''}
            </div>
        `;
    }

    createDetailedMetricBreakdown(title, metric) {
        const score = metric.score;
        const isGood = score >= 80;

        let detailContent = '';
        if (title === 'Groundedness' && metric.evidence && metric.evidence.length > 0) {
            detailContent = `
                <div class="mt-2">
                    <p class="text-sm font-medium text-gray-700">Supporting Evidence:</p>
                    <ul class="list-disc list-inside text-sm text-gray-600 mt-1">
                        ${metric.evidence.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
            `;
        } else if (title === 'Accuracy' && metric.issues && metric.issues.length > 0) {
            detailContent = `
                <div class="mt-2">
                    <p class="text-sm font-medium text-gray-700">Issues Found:</p>
                    <ul class="list-disc list-inside text-sm text-red-600 mt-1">
                        ${metric.issues.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
            `;
        } else if (title === 'Relevance' && metric.alignment) {
            detailContent = `
                <div class="mt-2">
                    <p class="text-sm font-medium text-gray-700">Alignment Assessment:</p>
                    <p class="text-sm text-gray-600 mt-1">${metric.alignment}</p>
                </div>
            `;
        }

        return `
            <div class="border rounded-lg p-4 ${isGood ? 'bg-green-50' : 'bg-red-50'}">
                <div class="flex items-center justify-between">
                    <h5 class="font-medium text-gray-800">${title}</h5>
                    <span class="text-sm font-bold ${isGood ? 'text-green-700' : 'text-red-700'}">${score}%</span>
                </div>

                <p class="text-sm text-gray-600 mt-2">${metric.reasoning}</p>
                ${detailContent}
            </div>
        `;
    }

    toggleMetricsDetails() {
        const detailsElement = document.getElementById('metrics-details');
        if (detailsElement) {
            detailsElement.classList.toggle('hidden');
        }
    }

    displayError(errorMessage) {
        this.responseMeta.innerHTML = `
            <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800">
                Error
            </span>
        `;

        this.responseContent.innerHTML = `
            <div class="text-red-600 p-4 bg-red-50 rounded-lg">
                <h4 class="font-medium mb-2">Error Processing Query</h4>
                <p>${errorMessage}</p>
            </div>
        `;

        this.responseSection.classList.remove('hidden');
        this.responseSection.classList.add('fade-in');
    }

    formatResponse(answer) {
        if (!answer) return '<p class="text-gray-500">No response generated</p>';

        // Convert line breaks to HTML
        let formatted = answer.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
        formatted = `<p>${formatted}</p>`;

        // Format numbered lists
        formatted = formatted.replace(/(\d+\.\s)/g, '<br><strong>$1</strong>');

        // Format headers (lines that end with colon)
        formatted = formatted.replace(/([A-Z][^<\n]*:)/g, '<strong>$1</strong>');

        // Highlight important numbers
        formatted = formatted.replace(/\b(\d+)\b/g, '<span class="font-semibold text-orange-600">$1</span>');

        return formatted;
    }

    clearQuery() {
        this.queryInput.value = '';
        this.handleQueryInput();
        this.responseSection.classList.add('hidden');
        this.queryTypeIndicator.classList.add('hidden');
    }

    addToHistory(query, status) {
        const historyItem = {
            query: query.length > 50 ? query.substring(0, 50) + '...' : query,
            fullQuery: query,
            status: status,
            timestamp: new Date()
        };

        this.queryHistoryData.unshift(historyItem);
        if (this.queryHistoryData.length > 5) {
            this.queryHistoryData = this.queryHistoryData.slice(0, 5);
        }

        this.updateHistoryDisplay();
    }

    updateHistoryStatus(query, status) {
        const item = this.queryHistoryData.find(h => h.fullQuery === query);
        if (item) {
            item.status = status;
            this.updateHistoryDisplay();
        }
    }

    updateHistoryDisplay() {
        if (this.queryHistoryData.length === 0) {
            this.queryHistoryElement.innerHTML = '<p class="text-gray-500 text-center py-4">No queries yet</p>';
            return;
        }

        this.queryHistoryElement.innerHTML = this.queryHistoryData.map(item => {
            const statusClass = {
                'pending': 'bg-yellow-100 text-yellow-800',
                'completed': 'bg-green-100 text-green-800',
                'failed': 'bg-red-100 text-red-800'
            }[item.status] || 'bg-gray-100 text-gray-800';

            return `
                <div class="p-2 bg-gray-50 rounded cursor-pointer hover:bg-gray-100"
                     onclick="ragInterface.queryInput.value = '${item.fullQuery.replace(/'/g, "\\'")}'; ragInterface.handleQueryInput();">
                    <div class="flex items-center justify-between mb-1">
                        <span class="text-xs px-2 py-0.5 rounded ${statusClass}">${item.status}</span>
                        <span class="text-xs text-gray-400">${this.formatTime(item.timestamp)}</span>
                    </div>
                    <p class="text-sm">${item.query}</p>
                </div>
            `;
        }).join('');
    }

    updateStatus(type, title, detail) {
        const statusClasses = {
            'initializing': 'border-yellow-400 bg-yellow-50',
            'ready': 'border-green-400 bg-green-50',
            'error': 'border-red-400 bg-red-50',
            'processing': 'border-blue-400 bg-blue-50'
        };

        const iconClasses = {
            'initializing': 'text-yellow-400',
            'ready': 'text-green-400',
            'error': 'text-red-400',
            'processing': 'text-blue-400'
        };

        this.statusElement.className = `mb-6 ${statusClasses[type]} border-l-4 p-4 rounded-r-lg`;
        this.statusIcon.className = `mr-3 ${iconClasses[type]}`;
        this.statusText.textContent = title;
        this.statusDetail.textContent = detail;
        this.sysStatus.textContent = title;
    }

    updateSystemInfo(data) {
        if (data.chunks_count !== undefined) {
            this.chunkCount.textContent = data.chunks_count;
            this.sysChunks.textContent = data.chunks_count;
        }
        if (data.document_size !== undefined) {
            this.docSize.textContent = this.formatFileSize(data.document_size);
        }
    }

    showLoadingModal(message) {
        this.loadingText.textContent = message;
        this.loadingModal.classList.remove('hidden');
    }

    hideLoadingModal() {
        this.loadingModal.classList.add('hidden');
    }

    async makeRequest(url, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        };

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Request failed:', error);
            // Simulate response for development
            return this.simulateResponse(url, options);
        }
    }

    simulateResponse(url, options) {
        // Simulate API responses for development
        if (url === '/api/status') {
            return {
                success: true,
                data: {
                    chunks_count: 247,
                    document_size: 1024 * 500, // 500KB
                    system_ready: true
                }
            };
        }

        if (url === '/api/query') {
            const body = JSON.parse(options.body);
            return {
                success: true,
                data: {
                    question: body.question,
                    answer: `This is a simulated response to your query: "${body.question}".\n\nThe system would analyze the document and provide relevant information based on the query type and content. In a real implementation, this would connect to the RAG backend and return actual processed results.`,
                    query_classification: {
                        primary_type: this.detectQueryType(body.question),
                        confidence: 0.85
                    },
                    chunks_analyzed: Math.floor(Math.random() * 20) + 5
                }
            };
        }

        return { success: false, error: 'API endpoint not available in demo mode' };
    }

    detectQueryType(query) {
        const queryLower = query.toLowerCase();
        if (this.hasCountingPatterns(queryLower)) return 'counting';
        if (this.hasAnalysisPatterns(queryLower)) return 'analysis';
        if (this.hasSearchPatterns(queryLower)) return 'search';
        return 'general';
    }

    formatTime(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize the interface when the page loads
let ragInterface;
document.addEventListener('DOMContentLoaded', () => {
    ragInterface = new RAGInterface();
});