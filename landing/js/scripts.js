function reveal() {
    var reveals = document.querySelectorAll(".reveal");
    for (var i = 0; i < reveals.length; i++) {
        var windowHeight = window.innerHeight;
        var elementTop = reveals[i].getBoundingClientRect().top;
        var elementVisible = 150;
        if (elementTop < windowHeight - elementVisible) {
            reveals[i].classList.add("active");
        }
    }
}
async function loadMenu() {
    const placeholder = document.getElementById('menu-placeholder');
    if (!placeholder) return;

    try {
        const response = await fetch('menu.html');
        if (response.ok) {
            const html = await response.text();
            placeholder.innerHTML = html;
        }
    } catch (error) {
        console.error('Erro ao carregar o menu:', error);
    }
}

document.addEventListener("DOMContentLoaded", loadMenu);
window.addEventListener("scroll", reveal);
reveal(); // Run on initiate
