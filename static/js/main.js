/**
 * Life Care Pathology Lab — Premium Interactive Script v2
 * Right-side nav, carousel, 3D tilt, scroll animations, counters, horizontal scroll
 */
document.addEventListener('DOMContentLoaded', () => {

    // ── Telegram Sidebar Toggle (Mobile) ──
    const navToggle = document.getElementById('navToggle');
    const sidebar = document.getElementById('telegramSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const body = document.body;

    function toggleSidebar(show) {
        if (show) {
            sidebar.classList.add('active');
            overlay.classList.add('active');
            body.style.overflow = 'hidden';
        } else {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
            body.style.overflow = '';
        }
    }

    if (navToggle) {
        navToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleSidebar(true);
        });
    }

    if (overlay) {
        overlay.addEventListener('click', () => toggleSidebar(false));
    }

    // Close sidebar on link click
    document.querySelectorAll('.sidebar-link').forEach(link => {
        link.addEventListener('click', () => toggleSidebar(false));
    });

    // ── Theme Toggle (Persist) ──
    const btnDark = document.getElementById('themeDark');
    const btnLight = document.getElementById('themeLight');
    const mobileThemeToggle = document.getElementById('mobileThemeToggle');

    // 1. Check LocalStorage or Default
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);

    function applyTheme(theme) {
        const root = document.documentElement;
        if (theme === 'dark') {
            // DARK MODE (University Style)
            root.style.setProperty('--bg-main', '#0f172a');
            root.style.setProperty('--bg-card', '#1e293b');
            root.style.setProperty('--bg-glass', 'rgba(15, 23, 42, 0.85)');
            root.style.setProperty('--bg-sidebar', '#1e293b');
            root.style.setProperty('--auth-card-bg', '#1e293b');
            
            root.style.setProperty('--text-primary', '#F8FAFC');
            root.style.setProperty('--text-secondary', '#94A3B8');
            
            root.style.setProperty('--border-color', 'rgba(255,255,255,0.08)');
            root.style.setProperty('--hero-gradient', 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)');
            
            document.body.classList.remove('light-theme');
            if(btnDark) { btnDark.classList.add('active'); btnLight.classList.remove('active'); }
        } else {
            // LIGHT MODE (Professional Clean — not plain white)
            root.style.setProperty('--bg-main', '#F0F4F8');
            root.style.setProperty('--bg-card', '#FFFFFF');
            root.style.setProperty('--bg-glass', 'rgba(255, 255, 255, 0.92)');
            root.style.setProperty('--bg-sidebar', '#FFFFFF');
            root.style.setProperty('--auth-card-bg', 'linear-gradient(135deg, #f8faff 0%, #eef2ff 50%, #faf5ff 100%)');
            
            root.style.setProperty('--text-primary', '#0f172a');
            root.style.setProperty('--text-secondary', '#64748B');
            
            root.style.setProperty('--border-color', 'rgba(0,0,0,0.08)');
            root.style.setProperty('--hero-gradient', 'linear-gradient(135deg, #E2E8F0 0%, #F8FAFC 100%)');
            
            document.body.classList.add('light-theme');
            if(btnLight) { btnLight.classList.add('active'); btnDark.classList.remove('active'); }
        }
        localStorage.setItem('theme', theme);
        
        // Update Mobile Icon/Text if exists
        const mobileThemeToggle = document.getElementById('mobileThemeToggle');
        if (mobileThemeToggle) {
             const icon = mobileThemeToggle.querySelector('i');
             if (icon) {
                 icon.className = theme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
             }
        }
    }

    if (btnDark) btnDark.addEventListener('click', () => applyTheme('dark'));
    if (btnLight) btnLight.addEventListener('click', () => applyTheme('light'));

    // Mobile Toggle (One button switches)
    if (mobileThemeToggle) {
        mobileThemeToggle.addEventListener('click', () => {
            const current = localStorage.getItem('theme') || 'dark';
            const newTheme = current === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
            
            // Update Icon
            const icon = mobileThemeToggle.querySelector('i');
            icon.className = newTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
            mobileThemeToggle.innerHTML = `<i class="${icon.className}"></i> ${newTheme === 'dark' ? 'Dark Mode' : 'Light Mode'}`;
        });
    }

    // Back to top
    if (backToTop) {
        backToTop.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // ── Image Carousel ──
    const track = document.querySelector('.carousel-track');
    const slides = document.querySelectorAll('.carousel-slide');
    const dotsContainer = document.querySelector('.carousel-dots');
    const prevBtn = document.querySelector('.carousel-btn-prev');
    const nextBtn = document.querySelector('.carousel-btn-next');

    if (track && slides.length > 0) {
        let currentSlide = 0;
        let autoPlayTimer;
        const totalSlides = slides.length;

        function goToSlide(index) {
            currentSlide = (index + totalSlides) % totalSlides;
            track.style.transform = `translateX(-${currentSlide * 100}%)`;
            updateDots();
        }

        function updateDots() {
            if (!dotsContainer) return;
            dotsContainer.querySelectorAll('.carousel-dot').forEach((dot, i) => {
                dot.classList.toggle('active', i === currentSlide);
            });
        }

        function startAutoPlay() {
            autoPlayTimer = setInterval(() => goToSlide(currentSlide + 1), 4500);
        }

        function stopAutoPlay() {
            clearInterval(autoPlayTimer);
        }

        // Create dots
        if (dotsContainer) {
            slides.forEach((_, i) => {
                const dot = document.createElement('button');
                dot.className = 'carousel-dot' + (i === 0 ? ' active' : '');
                dot.setAttribute('aria-label', `Slide ${i + 1}`);
                dot.addEventListener('click', () => { goToSlide(i); stopAutoPlay(); startAutoPlay(); });
                dotsContainer.appendChild(dot);
            });
        }

        if (prevBtn) prevBtn.addEventListener('click', () => { goToSlide(currentSlide - 1); stopAutoPlay(); startAutoPlay(); });
        if (nextBtn) nextBtn.addEventListener('click', () => { goToSlide(currentSlide + 1); stopAutoPlay(); startAutoPlay(); });

        // Touch/swipe support
        let touchStartX = 0;
        track.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; stopAutoPlay(); }, { passive: true });
        track.addEventListener('touchend', e => {
            const diff = touchStartX - e.changedTouches[0].clientX;
            if (Math.abs(diff) > 50) goToSlide(currentSlide + (diff > 0 ? 1 : -1));
            startAutoPlay();
        }, { passive: true });

        // Pause on hover
        const container = document.querySelector('.carousel-track-container');
        if (container) {
            container.addEventListener('mouseenter', stopAutoPlay);
            container.addEventListener('mouseleave', startAutoPlay);
        }

        startAutoPlay();
    }

    // ── Horizontal Services Auto-Scroll ──
    const scrollTrack = document.getElementById('servicesScrollTrack');
    if (scrollTrack) {
        let scrollSpeed = 1;
        let scrollPaused = false;

        function autoScroll() {
            if (!scrollPaused && scrollTrack.scrollWidth > scrollTrack.clientWidth) {
                scrollTrack.scrollLeft += scrollSpeed;
                // Reset to start when reaching halfway (where duplicates begin)
                if (scrollTrack.scrollLeft >= scrollTrack.scrollWidth / 2) {
                    scrollTrack.scrollLeft = 0;
                }
            }
            requestAnimationFrame(autoScroll);
        }

        scrollTrack.addEventListener('mouseenter', () => { scrollPaused = true; });
        scrollTrack.addEventListener('mouseleave', () => { scrollPaused = false; });
        scrollTrack.addEventListener('touchstart', () => { scrollPaused = true; }, { passive: true });
        scrollTrack.addEventListener('touchend', () => { setTimeout(() => { scrollPaused = false; }, 2000); }, { passive: true });

        requestAnimationFrame(autoScroll);
    }

    // ── 3D Card Tilt Effect ──
    document.querySelectorAll('.test-card').forEach(card => {
        card.addEventListener('mousemove', e => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = ((y - centerY) / centerY) * -8;
            const rotateY = ((x - centerX) / centerX) * 8;
            card.style.transform = `translateY(-12px) perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
        });
    });

    // ── Scroll Animations (Intersection Observer) ──
    const animated = document.querySelectorAll('.animate-on-scroll');
    if (animated.length) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    const parent = entry.target.parentElement;
                    const siblings = parent ? Array.from(parent.querySelectorAll('.animate-on-scroll')) : [entry.target];
                    const idx = siblings.indexOf(entry.target);
                    setTimeout(() => entry.target.classList.add('visible'), idx * 120);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
        animated.forEach(el => observer.observe(el));
    }

    // ── Number Counter Animation ──
    const stats = document.querySelectorAll('.stat-number[data-count]');
    if (stats.length) {
        const statsObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const target = parseInt(el.getAttribute('data-count'));
                    const duration = 2200;
                    const startTime = performance.now();
                    
                    function easeOutExpo(t) { return t === 1 ? 1 : 1 - Math.pow(2, -10 * t); }
                    
                    function update(currentTime) {
                        const elapsed = currentTime - startTime;
                        const progress = Math.min(elapsed / duration, 1);
                        const easedProgress = easeOutExpo(progress);
                        const current = Math.ceil(easedProgress * target);
                        el.textContent = current.toLocaleString() + '+';
                        if (progress < 1) requestAnimationFrame(update);
                    }
                    requestAnimationFrame(update);
                    statsObserver.unobserve(el);
                }
            });
        }, { threshold: 0.4 });
        stats.forEach(stat => statsObserver.observe(stat));
    }

    // ── Client-side Search Filter (Services Page) ──
    const searchInput = document.getElementById('testSearch');
    const testsGrid = document.getElementById('testsGrid');
    if (searchInput && testsGrid) {
        searchInput.addEventListener('input', e => {
            const term = e.target.value.toLowerCase();
            const cards = testsGrid.querySelectorAll('.test-card');
            cards.forEach(card => {
                const title = card.querySelector('h3')?.textContent.toLowerCase() || '';
                const desc = card.querySelector('.test-desc')?.textContent.toLowerCase() || '';
                const match = title.includes(term) || desc.includes(term);
                card.closest('.test-card-3d').style.display = match ? '' : 'none';
                if (match) {
                    card.classList.remove('visible');
                    setTimeout(() => card.classList.add('visible'), 50);
                }
            });
        });
    }

    // ── Flash Message Auto-dismiss ──
    document.querySelectorAll('.flash-message').forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateX(100%)';
            setTimeout(() => msg.remove(), 400);
        }, 5000);
    });

    // ── Desktop Profile Dropdown Click Toggle ──
    const userDropdown = document.querySelector('.nav-user-dropdown');
    if (userDropdown) {
        const userBtn = userDropdown.querySelector('.nav-user-btn') || userDropdown;
        userBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            userDropdown.classList.toggle('active');
        });
        document.addEventListener('click', function(e) {
            if (!userDropdown.contains(e.target)) {
                userDropdown.classList.remove('active');
            }
        });
    }

});
