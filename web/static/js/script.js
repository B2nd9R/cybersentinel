// CyberSentinel Website JavaScript
// Professional and Modern Implementation

class CyberSentinelWebsite {
    constructor() {
        this.init();
        this.bindEvents();
        this.setupAnimations();
        this.setupParticles();
        this.setupStats();
    }

    init() {
        // Initialize variables
        this.navbar = document.getElementById('navbar');
        this.mobileMenuBtn = document.getElementById('mobile-menu-btn');
        this.navMenu = document.getElementById('nav-menu');
        this.scrollIndicator = document.querySelector('.scroll-indicator');
        this.particlesBg = document.getElementById('particles-bg');
        
        // Animation observers
        this.observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        this.setupIntersectionObserver();
    }

    bindEvents() {
        // Scroll events
        window.addEventListener('scroll', this.handleScroll.bind(this));
        
        // Mobile menu
        this.mobileMenuBtn?.addEventListener('click', this.toggleMobileMenu.bind(this));
        
        // Smooth scroll for navigation links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', this.handleNavClick.bind(this));
        });
        
        // Tab functionality for commands section
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', this.handleTabClick.bind(this));
        });
        
        // Button hover effects
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('mouseenter', this.handleButtonHover.bind(this));
            btn.addEventListener('mouseleave', this.handleButtonLeave.bind(this));
        });
        
        // Magnetic effect for interactive elements
        document.querySelectorAll('.magnetic').forEach(el => {
            el.addEventListener('mousemove', this.handleMagneticMove.bind(this));
            el.addEventListener('mouseleave', this.handleMagneticLeave.bind(this));
        });
        
        // Resize events
        window.addEventListener('resize', this.handleResize.bind(this));
        
        // Page load
        window.addEventListener('load', this.handlePageLoad.bind(this));
    }

    handleScroll() {
        const scrollY = window.scrollY;
        
        // Navbar scroll effect
        if (scrollY > 50) {
            this.navbar?.classList.add('scrolled');
        } else {
            this.navbar?.classList.remove('scrolled');
        }
        
        // Hide scroll indicator
        if (scrollY > 100) {
            this.scrollIndicator?.style.setProperty('opacity', '0');
        } else {
            this.scrollIndicator?.style.setProperty('opacity', '1');
        }
        
        // Update active nav link
        this.updateActiveNavLink();
    }

    toggleMobileMenu() {
        this.navMenu?.classList.toggle('active');
        this.mobileMenuBtn?.classList.toggle('active');
        
        // Prevent body scroll when menu is open
        if (this.navMenu?.classList.contains('active')) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
    }

    handleNavClick(e) {
        e.preventDefault();
        
        const targetId = e.target.getAttribute('href');
        if (targetId && targetId.startsWith('#')) {
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                const offsetTop = targetElement.offsetTop - 70;
                
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
                
                // Close mobile menu if open
                this.navMenu?.classList.remove('active');
                this.mobileMenuBtn?.classList.remove('active');
                document.body.style.overflow = '';
            }
        }
    }

    updateActiveNavLink() {
        const sections = document.querySelectorAll('section[id]');
        const navLinks = document.querySelectorAll('.nav-link');
        
        let currentSection = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop - 100;
            const sectionHeight = section.offsetHeight;
            
            if (window.scrollY >= sectionTop && window.scrollY < sectionTop + sectionHeight) {
                currentSection = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${currentSection}`) {
                link.classList.add('active');
            }
        });
    }

    handleTabClick(e) {
        const tabId = e.target.getAttribute('data-tab');
        
        // Remove active from all tabs and contents
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        // Add active to clicked tab and corresponding content
        e.target.classList.add('active');
        const targetContent = document.getElementById(tabId);
        if (targetContent) {
            targetContent.classList.add('active');
            
            // Animate content appearance
            const cards = targetContent.querySelectorAll('.command-card');
            cards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    card.style.transition = 'all 0.3s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 100);
            });
        }
    }

    handleButtonHover(e) {
        const btn = e.target;
        const rect = btn.getBoundingClientRect();
        const ripple = document.createElement('span');
        
        ripple.classList.add('ripple');
        ripple.style.position = 'absolute';
        ripple.style.borderRadius = '50%';
        ripple.style.background = 'rgba(255, 255, 255, 0.3)';
        ripple.style.transform = 'scale(0)';
        ripple.style.animation = 'ripple 0.6s linear';
        ripple.style.left = '50%';
        ripple.style.top = '50%';
        ripple.style.width = '20px';
        ripple.style.height = '20px';
        ripple.style.marginLeft = '-10px';
        ripple.style.marginTop = '-10px';
        
        btn.style.position = 'relative';
        btn.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    handleButtonLeave(e) {
        // Button leave animation
        e.target.style.transform = '';
    }

    handleMagneticMove(e) {
        const element = e.target;
        const rect = element.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        
        const moveX = x * 0.1;
        const moveY = y * 0.1;
        
        element.style.transform = `translate(${moveX}px, ${moveY}px)`;
    }

    handleMagneticLeave(e) {
        e.target.style.transform = '';
    }

    handleResize() {
        // Recalculate particles on resize
        this.setupParticles();
        
        // Close mobile menu on resize to desktop
        if (window.innerWidth > 768) {
            this.navMenu?.classList.remove('active');
            this.mobileMenuBtn?.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    handlePageLoad() {
        // Hide loading animations
        document.body.classList.add('loaded');
        
        // Start typewriter effect
        this.startTypewriterEffect();
        
        // Initialize all animations
        this.triggerAnimations();
    }

    setupIntersectionObserver() {
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    if (entry.target.classList.contains('fade-in')) {
                        entry.target.classList.add('visible');
                    }
                    if (entry.target.classList.contains('slide-in-left')) {
                        entry.target.classList.add('visible');
                    }
                    if (entry.target.classList.contains('slide-in-right')) {
                        entry.target.classList.add('visible');
                    }
                    
                    // Trigger counter animation for stats
                    if (entry.target.classList.contains('stat-number')) {
                        this.animateCounter(entry.target);
                    }
                }
            });
        }, this.observerOptions);
        
        // Observe elements
        document.querySelectorAll('.fade-in, .slide-in-left, .slide-in-right, .stat-number').forEach(el => {
            this.observer.observe(el);
        });
    }

    setupAnimations() {
        // Add animation classes to elements
        document.querySelectorAll('.feature-card').forEach((card, index) => {
            card.classList.add('fade-in');
            card.style.transitionDelay = `${index * 0.1}s`;
        });
        
        document.querySelectorAll('.step-item').forEach((step, index) => {
            step.classList.add('fade-in');
            step.style.transitionDelay = `${index * 0.2}s`;
        });
        
        document.querySelectorAll('.command-card').forEach((card, index) => {
            card.classList.add('fade-in');
            card.style.transitionDelay = `${index * 0.05}s`;
        });
    }

    setupParticles() {
        if (!this.particlesBg) return;
        
        // Create floating particles
        const particleCount = Math.min(50, Math.floor(window.innerWidth / 30));
        
        // Clear existing particles
        this.particlesBg.innerHTML = '';
        
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.position = 'absolute';
            particle.style.width = Math.random() * 4 + 2 + 'px';
            particle.style.height = particle.style.width;
            particle.style.background = Math.random() > 0.5 ? '#00e4ff' : '#8c67ff';
            particle.style.borderRadius = '50%';
            particle.style.opacity = Math.random() * 0.5 + 0.2;
            particle.style.left = Math.random() * 100 + '%';
            particle.style.top = Math.random() * 100 + '%';
            particle.style.animation = `floatParticle ${Math.random() * 20 + 10}s linear infinite`;
            particle.style.animationDelay = Math.random() * 5 + 's';
            
            this.particlesBg.appendChild(particle);
        }
        
        // Add CSS for particle animation if not exists
        if (!document.getElementById('particle-styles')) {
            const style = document.createElement('style');
            style.id = 'particle-styles';
            style.textContent = `
                @keyframes floatParticle {
                    0% { transform: translateY(100vh) rotate(0deg); }
                    100% { transform: translateY(-100px) rotate(360deg); }
                }
                .particle {
                    will-change: transform;
                    filter: blur(0.5px);
                }
            `;
            document.head.appendChild(style);
        }
    }

    setupStats() {
        // Initialize counter values
        document.querySelectorAll('.stat-number').forEach(stat => {
            stat.setAttribute('data-current', '0');
        });
    }

    animateCounter(element) {
        if (element.hasAttribute('data-animated')) return;
        
        const target = parseInt(element.getAttribute('data-target'));
        const duration = 2000;
        const increment = target / (duration / 16);
        let current = 0;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = Math.floor(current);
        }, 16);
        
        element.setAttribute('data-animated', 'true');
    }

    startTypewriterEffect() {
        const typewriterElements = document.querySelectorAll('.typewriter');
        
        typewriterElements.forEach((element, index) => {
            setTimeout(() => {
                element.style.animation = 'typewriter 4s steps(40, end), blink-caret 0.75s step-end infinite';
            }, index * 1000);
        });
    }

    triggerAnimations() {
        // Security dashboard animations
        const dashboard = document.querySelector('.security-dashboard');
        if (dashboard) {
            setTimeout(() => {
                dashboard.style.transform = 'scale(1)';
                dashboard.style.opacity = '1';
            }, 500);
        }
        
        // Meter animation
        const meterFill = document.querySelector('.meter-fill');
        if (meterFill) {
            setTimeout(() => {
                meterFill.style.background = 'conic-gradient(var(--cyan-glow) 0deg, var(--cyan-glow) 270deg, rgba(0, 228, 255, 0.2) 270deg)';
            }, 1000);
        }
        
        // Pulse ring animation
        const pulseRing = document.querySelector('.pulse-ring');
        if (pulseRing) {
            pulseRing.style.animation = 'pulse-ring 2s ease-out infinite';
        }
    }

    // Utility methods
    throttle(func, wait) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, wait);
            }
        };
    }

    debounce(func, wait, immediate) {
        let timeout;
        return function() {
            const context = this;
            const args = arguments;
            const later = function() {
                timeout = null;
                if (!immediate) func.apply(context, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(context, args);
        };
    }

    // Advanced features
    setupAdvancedFeatures() {
        // Page visibility API for performance
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Pause animations when page is not visible
                document.querySelectorAll('.particle').forEach(particle => {
                    particle.style.animationPlayState = 'paused';
                });
            } else {
                // Resume animations when page is visible
                document.querySelectorAll('.particle').forEach(particle => {
                    particle.style.animationPlayState = 'running';
                });
            }
        });
        
        // Preload critical resources
        this.preloadResources();
        
        // Setup service worker for caching (if needed)
        if ('serviceWorker' in navigator) {
            this.setupServiceWorker();
        }
    }

    preloadResources() {
        // Preload critical images and fonts
        const preloadLinks = [
            { rel: 'preload', href: 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css', as: 'style' }
        ];
        
        preloadLinks.forEach(link => {
            const linkElement = document.createElement('link');
            Object.keys(link).forEach(key => {
                linkElement[key] = link[key];
            });
            document.head.appendChild(linkElement);
        });
    }

    setupServiceWorker() {
        // Basic service worker setup for caching
        navigator.serviceWorker.register('/sw.js').then(() => {
            console.log('Service Worker registered successfully');
        }).catch(error => {
            console.log('Service Worker registration failed:', error);
        });
    }

    // Analytics and tracking
    trackUserInteraction(action, element) {
        // Basic analytics tracking
        if (typeof gtag !== 'undefined') {
            gtag('event', action, {
                event_category: 'interaction',
                event_label: element
            });
        }
        
        console.log(`User interaction: ${action} on ${element}`);
    }

    // Performance monitoring
    measurePerformance() {
        if ('performance' in window) {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const perfData = performance.timing;
                    const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
                    console.log(`Page load time: ${pageLoadTime}ms`);
                }, 0);
            });
        }
    }

    // Error handling
    setupErrorHandling() {
        window.addEventListener('error', (e) => {
            console.error('JavaScript error:', e.error);
            // Could send to error tracking service
        });
        
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Unhandled promise rejection:', e.reason);
            // Could send to error tracking service
        });
    }

    // Accessibility improvements
    setupAccessibility() {
        // Focus management
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-nav');
            }
        });
        
        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-nav');
        });
        
        // Skip to content link
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Skip to main content';
        skipLink.className = 'sr-only';
        skipLink.addEventListener('focus', () => {
            skipLink.classList.remove('sr-only');
        });
        skipLink.addEventListener('blur', () => {
            skipLink.classList.add('sr-only');
        });
        
        document.body.insertBefore(skipLink, document.body.firstChild);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const website = new CyberSentinelWebsite();
    
    // Add additional setup
    website.setupAdvancedFeatures();
    website.measurePerformance();
    website.setupErrorHandling();
    website.setupAccessibility();
    
    // Make available globally for debugging
    window.cyberSentinel = website;
});

// Add ripple effect CSS
const rippleStyles = document.createElement('style');
rippleStyles.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .keyboard-nav *:focus {
        outline: 2px solid var(--cyan-glow) !important;
        outline-offset: 2px;
    }
    
    .sr-only:focus {
        position: absolute;
        width: auto;
        height: auto;
        padding: 0.5rem 1rem;
        margin: 0;
        overflow: visible;
        clip: auto;
        white-space: normal;
        background: var(--primary-dark);
        color: var(--cyan-glow);
        border: 2px solid var(--cyan-glow);
        border-radius: var(--border-radius);
        top: 1rem;
        left: 1rem;
        z-index: 9999;
    }
`;

document.head.appendChild(rippleStyles);