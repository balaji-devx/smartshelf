function updateDashboardStats() {
    fetch('/api/dashboard-stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const stats = data.stats;
                
                // Update the dashboard numbers with animation
                updateNumberWithAnimation('.total-books', stats.total_books);
                updateNumberWithAnimation('.available-books', stats.available_books);
                updateNumberWithAnimation('.returned-books', stats.returned_books);
                updateNumberWithAnimation('.issued-books', stats.issued_books);
            } else {
                console.error('Error fetching stats:', data.error);
                if (data.error === 'Unauthorized access') {
                    window.location.href = '/';
                }
            }
        })
        .catch(error => {
            console.error('Error updating dashboard:', error);
        });
}

function updateNumberWithAnimation(selector, newValue) {
    const element = document.querySelector(selector);
    const oldValue = parseInt(element.textContent) || 0;
    
    if (oldValue !== newValue) {
        element.classList.add('number-updated');
        element.textContent = newValue;
        setTimeout(() => element.classList.remove('number-updated'), 1000);
    }
}

// Update stats every 30 seconds
setInterval(updateDashboardStats, 30000);

// Initial update when page loads
document.addEventListener('DOMContentLoaded', updateDashboardStats);