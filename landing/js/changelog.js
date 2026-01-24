async function loadChangelog() {
    const markdownBody = document.getElementById('markdown-body');
    try {
        // Tenta primeiro o caminho local (landing/)
        let response = await fetch('CHANGELOG.md');

        // Se não achar localmente (404), tenta o caminho da raiz
        if (!response.ok) {
            console.log('CHANGELOG.md não encontrado na pasta landing, tentando raiz...');
            response = await fetch('../CHANGELOG.md');
        }

        if (!response.ok) throw new Error('Não foi possível localizar o arquivo CHANGELOG.md em nenhum dos diretórios.');

        const text = await response.text();
        markdownBody.innerHTML = marked.parse(text);
    } catch (error) {
        markdownBody.innerHTML = `<p style="color: #ff4d4d; text-align: center;">Erro: ${error.message}</p>`;
    }
}

document.addEventListener("DOMContentLoaded", loadChangelog);
