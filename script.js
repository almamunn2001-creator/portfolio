document.addEventListener('DOMContentLoaded', function () {

    // ----- Footer year -----
    var yearEl = document.getElementById('year');
    if (yearEl) yearEl.textContent = new Date().getFullYear();

    // ----- Mobile nav toggle -----
    var navToggle = document.getElementById('navToggle');
    var navList = document.querySelector('nav ul');

    if (navToggle && navList) {
        navToggle.addEventListener('click', function () {
            var open = navList.classList.toggle('open');
            navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        });

        navList.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                navList.classList.remove('open');
                navToggle.setAttribute('aria-expanded', 'false');
            });
        });
    }

    // ----- Theme toggle -----
    var root = document.documentElement;
    var themeBtn = document.getElementById('themeToggle');

    function syncThemeBtn() {
        if (!themeBtn) return;
        var dark = root.getAttribute('data-theme') === 'dark';
        themeBtn.innerHTML = dark ? '&#9788;' : '&#9790;';
        themeBtn.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
    }

    if (themeBtn) {
        themeBtn.addEventListener('click', function () {
            var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            root.setAttribute('data-theme', next);
            try { localStorage.setItem('theme', next); } catch (e) {}
            syncThemeBtn();
        });
    }
    syncThemeBtn();

    // ----- Nav shadow + back-to-top -----
    var nav = document.querySelector('nav');
    var toTop = document.getElementById('toTop');

    function onScrollUi() {
        if (nav) nav.classList.toggle('scrolled', window.scrollY > 10);
        if (toTop) toTop.classList.toggle('show', window.scrollY > 600);
    }
    window.addEventListener('scroll', onScrollUi, { passive: true });
    onScrollUi();

    if (toTop) {
        toTop.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // ----- Active nav link on scroll -----
    var sections = document.querySelectorAll('section[id]');
    var navLinks = document.querySelectorAll('.nav-link');

    function setActiveLink() {
        var scrollPos = window.scrollY + 120;
        sections.forEach(function (section) {
            var top = section.offsetTop;
            var height = section.offsetHeight;
            var id = section.getAttribute('id');
            if (scrollPos >= top && scrollPos < top + height) {
                navLinks.forEach(function (link) {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === '#' + id) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }

    window.addEventListener('scroll', setActiveLink, { passive: true });
    setActiveLink();

    // ----- Project filter -----
    var filterButtons = document.querySelectorAll('.filter-btn');
    var projectCards = document.querySelectorAll('.project-card');

    filterButtons.forEach(function (btn) {
        btn.addEventListener('click', function () {
            filterButtons.forEach(function (b) { b.classList.remove('active'); });
            btn.classList.add('active');

            var filter = btn.getAttribute('data-filter');

            projectCards.forEach(function (card) {
                if (filter === 'all' || card.getAttribute('data-category') === filter) {
                    card.hidden = false;
                } else {
                    card.hidden = true;
                }
            });
        });
    });

    // ----- Scroll reveal -----
    var revealTargets = document.querySelectorAll(
        '.stats .card, .project-card, .skill-card, .timeline-item, .contact-card, .about-text, .about-facts'
    );

    revealTargets.forEach(function (el) { el.classList.add('reveal'); });

    var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
        revealTargets.forEach(function (el) { el.classList.add('visible'); });
    } else if ('IntersectionObserver' in window) {
        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12 });

        revealTargets.forEach(function (el) { observer.observe(el); });
    } else {
        revealTargets.forEach(function (el) { el.classList.add('visible'); });
    }

    // ----- Count-up stats -----
    var counters = document.querySelectorAll('[data-count]');

    function runCounter(el) {
        var target = parseFloat(el.getAttribute('data-count'));
        var decimals = parseInt(el.getAttribute('data-decimals') || '0', 10);
        var suffix = el.getAttribute('data-suffix') || '';
        var duration = 1200;
        var start = null;

        function tick(ts) {
            if (start === null) start = ts;
            var p = Math.min((ts - start) / duration, 1);
            var eased = 1 - Math.pow(1 - p, 3);
            el.textContent = (target * eased).toFixed(decimals) + suffix;
            if (p < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    }

    if (!prefersReducedMotion && 'IntersectionObserver' in window) {
        var counterObserver = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    runCounter(entry.target);
                    counterObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.6 });
        counters.forEach(function (el) { counterObserver.observe(el); });
    }

});
