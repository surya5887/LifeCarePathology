/**
 * Life Care Pathology Lab — Premium Interactive Script v2
 * Right-side nav, carousel, 3D tilt, scroll animations, counters, horizontal scroll
 */
document.addEventListener('DOMContentLoaded', () => {

    // ── Navbar Scroll Effect & Mobile Toggle (RIGHT SIDE) ──
    const navbar = document.getElementById('navbar');
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.getElementById('navLinks');
    const navOverlay = document.getElementById('navOverlay');
    const backToTop = document.getElementById('backToTop');

    window.addEventListener('scroll', () => {
        if (navbar) navbar.classList.toggle('scrolled', window.scrollY > 30);
        if (backToTop) backToTop.classList.toggle('visible', window.scrollY > 400);
    });

    if (navToggle) {
        navToggle.addEventListener('click', () => {
            navToggle.classList.toggle('active');
            navLinks.classList.toggle('active');
            document.body.style.overflow = navLinks.classList.contains('active') ? 'hidden' : '';
        });
        // Close on link click
        navLinks.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                navToggle.classList.remove('active');
                navLinks.classList.remove('active');
                document.body.style.overflow = '';
            });
        });
    }

    // Close on overlay click
    if (navOverlay) {
        navOverlay.addEventListener('click', () => {
            if (navToggle) navToggle.classList.remove('active');
            if (navLinks) navLinks.classList.remove('active');
            document.body.style.overflow = '';
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

});
