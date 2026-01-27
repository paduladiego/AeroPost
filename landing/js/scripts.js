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
            setupMenu(); // Inicializa a lógica após carregar o HTML
        }
    } catch (error) {
        console.error('Erro ao carregar o menu:', error);
    }
}

function setupMenu() {
    const toggle = document.querySelector('.menu-toggle');
    const nav = document.querySelector('nav');
    const links = document.querySelectorAll('nav a');

    if (!toggle || !nav) return;

    toggle.addEventListener('click', () => {
        toggle.classList.toggle('active');
        nav.classList.toggle('active');
        document.body.style.overflow = nav.classList.contains('active') ? 'hidden' : 'auto';
    });

    // Fecha o menu ao clicar em qualquer link
    links.forEach(link => {
        link.addEventListener('click', () => {
            toggle.classList.remove('active');
            nav.classList.remove('active');
            document.body.style.overflow = 'auto';
        });
    });
}

document.addEventListener("DOMContentLoaded", loadMenu);
window.addEventListener("scroll", reveal);
reveal(); // Run on initiate
