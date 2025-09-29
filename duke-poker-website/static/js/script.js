document.addEventListener('DOMContentLoaded', function () {
    const btn = document.getElementById('announcement-btn');
    const modal = document.getElementById('announcement-modal');
    const closeBtn = document.getElementById('modal-close');

    if (!modal) return;

    function openModal() {
        modal.classList.add('open');
        modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        modal.classList.remove('open');
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    }

    if (btn) btn.addEventListener('click', openModal);
    if (closeBtn) closeBtn.addEventListener('click', closeModal);

    modal.addEventListener('click', function (e) {
        if (e.target === modal) closeModal();
    });

    // Auto-open only on first visit (per browser). Change the key to reset.
    try {
        const key = 'duke_poker_seen_announcement_v1';
        const seen = localStorage.getItem(key);
        if (!seen) {
            openModal();
            localStorage.setItem(key, '1');
        }
    } catch (e) {
        // localStorage may be disabled; ignore
    }
});
