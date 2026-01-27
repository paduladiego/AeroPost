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
 
- ### Menu Compartilhado
- O menu é injetado dinamicamente via JavaScript para evitar duplicidade de código. Qualquer alteração estrutural deve ser feita exclusivamente no arquivo `menu.html`.
- 
- ### Renderização de Changelog
- O arquivo `CHANGELOG.md` é renderizado automaticamente no front-end. O sistema busca primeiro a versão local na pasta `landing/` e utiliza a raiz do projeto como fallback apenas para desenvolvimento.
- 
- ---
- 
- ## 🎨 Padrões de Design (UI/UX)
- 
- - **Identidade**: Tipografia Outfit (Google Fonts) e paleta baseada em tons de azul e escuro (`#00d2ff`, `#0f172a`).
- - **Estética**: Uso de Glassmorphism, gradientes modernos e animações de revelação (reveal) ao rolar a página.
- 
- ---
- 
- ## ⚠️ Checklist de Manutenção
- 
- - [ ] **Novo Release**: Reescrever as novidades técnicas do projeto em linguagem comercial no `landing/CHANGELOG.md`.
- - [ ] **Consistência**: Validar se o `menu-placeholder` está presente em todas as novas páginas HTML.
- - [ ] **Assets**: Garantir que novos caminhos de imagens e estilos sejam sempre relativos.
