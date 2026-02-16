// Mobile Navbar Toggle
document.addEventListener("DOMContentLoaded", function () {

    const toggle = document.getElementById("navToggle");
    const navLinks = document.getElementById("navLinks");

    if (toggle) {
        toggle.addEventListener("click", function () {
            navLinks.classList.toggle("active");
        });
    }

    // Auto close flash messages
    setTimeout(() => {
        document.querySelectorAll(".flash-message").forEach(msg => {
            msg.style.opacity = "0";
            setTimeout(() => msg.remove(), 400);
        });
    }, 4000);

});
