# Infraestrutura e Padrões - AeroPost Landing Page

Este documento define as regras de desenvolvimento e organização para a Landing Page do AeroPost, garantindo **portabilidade total** e **independência do backend Flask**.

## 🚀 Princípios Core

1. **Portabilidade Estática**: O conteúdo da pasta `landing/` deve ser capaz de ser servido por qualquer servidor web (Nginx, S3, GitHub Pages) sem necessidade de um interpretador Python.
2. **Zero Dependência Interna**: Não utilize sintaxe Jinja2 (`{{ ... }}`) ou rotas Flask aqui. Utilize caminhos relativos para todos os assets.
3. **DRY (Don't Repeat Yourself)**: Componentes comuns devem ser isolados em arquivos HTML e carregados dinamicamente via JavaScript.

---

## 📂 Organização de Arquivos

- `/assets`: Imagens, ícones e logotipos.
- `/css`: Arquivos de estilo.
  - `styles.css`: Estilo base, variáveis e efeitos globais.
  - `changelog.css`: Estilos específicos para renderização de notas de versão.
- `/js`: Lógica de comportamento.
  - `scripts.js`: Lógica global (reveal animations, carregamento de menu).
  - `changelog.js`: Lógica específica para fetch e render do ChangeLog.
- `menu.html`: Componente compartilhado do cabeçalho.
- `CHANGELOG.md`: Fonte de verdade para as notas de versão.

---

## 🛠️ Componentes e Carregamento

### Menu Compartilhado
O menu é injetado dinamicamente para evitar duplicidade de código:
```javascript
// Localizado em js/scripts.js
async function loadMenu() {
    const placeholder = document.getElementById('menu-placeholder');
    // Faz o fetch do menu.html e injeta no DOM
}
```
Regra: Qualquer alteração no menu deve ser feita EXCLUSIVAMENTE em `menu.html`.

### Renderização de Markdown
Utilizamos a biblioteca **marked.js** via CDN para transformar o `CHANGELOG.md` em HTML no lado do cliente.
Regra: O sistema tenta carregar primeiro `landing/CHANGELOG.md`. Caso não encontre (404), ele tenta buscar na raiz do projeto (`../CHANGELOG.md`). Isso facilita o desenvolvimento sem necessidade de cópia constante.

---

## 🎨 Padrões de Design (UI/UX)

- **Fonte**: Outfit (Google Fonts) - Pesos 300, 400, 600, 800.
- **Cores**:
  - Primary: `#00d2ff`
  - Secondary: `#3a7bd5`
  - Dark: `#0f172a`
- **Efeitos**: 
  - Glassmorphism (blur 10px-15px, background semi-transparente).
  - Gradientes dinâmicos para links e botões CTA.
  - Reveal animations ao scroll (classe `.reveal`).

---

## ⚠️ Checklist de Manutenção

- [ ] Ao atualizar o sistema, copie o `CHANGELOG.md` da raiz para `landing/`.
- [ ] Teste links relativos entre `index.html` e `changelog.html`.
- [ ] Verifique se o `menu-placeholder` está presente em novas páginas.
