document.addEventListener('DOMContentLoaded', function() {
    const targetElement = document.getElementById('target-element');
    const body = document.body;

    window.addEventListener('scroll', function() {
        const targetPosition = targetElement.getBoundingClientRect().bottom;
        const windowHeight = window.innerHeight;

        if (targetPosition <= windowHeight) {
            // Reached the target element, prevent further scrolling
            body.style.overflow = 'hidden';
        } else {
            // Above the target element, allow scrolling
            body.style.overflow = 'auto';
        }
    });
});
