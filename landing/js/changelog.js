async function loadChangelog() {
    const markdownBody = document.getElementById('markdown-body');
    try {
        // Tenta buscar o caminho da landing (específico e simplificado)
        const response = await fetch('CHANGELOG-LANDING.md');

        if (!response.ok) throw new Error('O arquivo de novidades (CHANGELOG-LANDING.md) não foi encontrado no servidor.');

        const text = await response.text();
        markdownBody.innerHTML = marked.parse(text);
    } catch (error) {
        markdownBody.innerHTML = `<p style="color: #ff4d4d; text-align: center;">Erro: ${error.message}</p>`;
    }
}

document.addEventListener("DOMContentLoaded", loadChangelog);
