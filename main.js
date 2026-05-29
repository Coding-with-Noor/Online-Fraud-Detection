// ============================================================
// FraudGuard - Main JavaScript
// Handles: navbar scroll, metric bar animation, general UI
// ============================================================

// --- Navbar shadow on scroll ---
window.addEventListener('scroll', function () {
    const navbar = document.getElementById('mainNavbar');
    if (!navbar) return;
    if (window.scrollY > 20) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// --- Animate metric bars when they scroll into view ---
// Using IntersectionObserver (works in all modern browsers)
function animateMetricBars() {
    const fills = document.querySelectorAll('.metric-fill');
    if (!fills.length) return;

    const observer = new IntersectionObserver(function (entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const target = el.getAttribute('data-target');
                if (target) {
                    // Slight delay before animating
                    setTimeout(() => {
                        el.style.width = target + '%';
                    }, 200);
                }
                observer.unobserve(el);  // Only animate once
            }
        });
    }, { threshold: 0.3 });

    fills.forEach(fill => observer.observe(fill));
}

// --- Flash messages auto-dismiss ---
function autoDismissAlerts() {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) closeBtn.click();
        }, 4000);
    });
}

// --- Run on DOM ready ---
document.addEventListener('DOMContentLoaded', function () {
    animateMetricBars();
    autoDismissAlerts();

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    console.log('%cFraudGuard Loaded ✓', 'color: #00d4aa; font-weight: bold; font-size: 14px;');
});
