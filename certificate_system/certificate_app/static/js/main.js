// Global utility functions
function showLoading(element) {
    element.innerHTML = '<div class="loading">Loading...</div>';
}

function showError(element, message) {
    element.innerHTML = `<div class="error">${message}</div>`;
}

function showSuccess(element, message) {
    element.innerHTML = `<div class="success">${message}</div>`;
}

// API utility functions
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}