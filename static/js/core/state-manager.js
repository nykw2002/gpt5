export class StateManager {
    constructor() {
        this.isSystemReady = false;
        this.currentQuery = null;
        this.queryHistoryData = [];
    }

    setSystemReady(ready) {
        this.isSystemReady = ready;
    }

    setCurrentQuery(query) {
        this.currentQuery = query;
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
    }

    updateHistoryStatus(query, status) {
        const item = this.queryHistoryData.find(h => h.fullQuery === query);
        if (item) {
            item.status = status;
        }
    }

    getHistory() {
        return this.queryHistoryData;
    }
}