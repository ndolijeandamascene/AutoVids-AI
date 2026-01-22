// AutoVids AI Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Theme Toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            // Theme toggle functionality (placeholder)
            console.log('Theme toggle clicked');
        });
    }
    
    // Notifications
    const notificationsBtn = document.getElementById('notifications-btn');
    if (notificationsBtn) {
        notificationsBtn.addEventListener('click', function() {
            console.log('Notifications clicked');
        });
    }
    
    // Add smooth scroll behavior
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Auto-refresh stats every 30 seconds (optional)
    // setInterval(function() {
    //     location.reload();
    // }, 30000);
});
