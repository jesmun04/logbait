// Hacer barra de navegación transparente cuando no se ha hecho scroll.
const navbar = document.getElementById('mainNavbar');
function checkScroll() {
    if (window.scrollY > 10) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
}
window.addEventListener('scroll', checkScroll);
document.addEventListener('DOMContentLoaded', checkScroll);