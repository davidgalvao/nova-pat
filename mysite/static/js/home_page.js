document.addEventListener('DOMContentLoaded', function () {
    const toggle = document.querySelector('.search-toggle');
    const form = document.querySelector('.search-bar');

    if (!toggle || !form) return;

    toggle.addEventListener('click', function (e) {
        e.preventDefault();
        form.classList.toggle('active');
        if (form.classList.contains('active')) {
            const input = form.querySelector('input[type="search"]');
            if (input) input.focus();
        }
    });

    document.addEventListener('click', function (e) {
        if (!form.classList.contains('active')) return;
        if (e.target.closest('.search-bar') || e.target.closest('.search-toggle')) return;
        form.classList.remove('active');
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') form.classList.remove('active');
    });
});
