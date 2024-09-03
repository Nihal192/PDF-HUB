// Example: Adding a hover effect to the tool container
document.addEventListener("DOMContentLoaded", function() {
    const toolContainer = document.querySelector('.tool-container');

    toolContainer.addEventListener('mouseover', function() {
        toolContainer.style.transform = 'scale(1.05)';
    });

    toolContainer.addEventListener('mouseout', function() {
        toolContainer.style.transform = 'scale(1)';
    });
});
