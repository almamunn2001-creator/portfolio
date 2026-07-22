document.addEventListener('DOMContentLoaded', function () {

    // ----- Footer year -----
    var yearEl = document.getElementById('year');
    if (yearEl) yearEl.textContent = new Date().getFullYear();

    // ----- Mobile nav toggle -----
    var navToggle = document.getElementById('navToggle');
    var navList = document.querySelector('nav ul');

    if (navToggle && navList) {
        navToggle.addEventListener('click', function () {
            navList.classList.toggle('open');
        });

        navList.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                navList.classList.remove('open');
            });
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

    window.addEventListener('scroll', setActiveLink);
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

});
