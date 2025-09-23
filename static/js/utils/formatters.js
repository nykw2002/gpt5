export function formatTime(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export function formatResponse(answer) {
    if (!answer) return '<p class="text-gray-500">No response generated</p>';

    let formatted = answer.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
    formatted = `<p>${formatted}</p>`;

    formatted = formatted.replace(/(\d+\.\s)/g, '<br><strong>$1</strong>');
    formatted = formatted.replace(/([A-Z][^<\n]*:)/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\b(\d+)\b/g, '<span class="font-semibold text-orange-600">$1</span>');

    return formatted;
}