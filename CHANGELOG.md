# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [v1.0.0] - 2026-01-15

### Adicionado
- **Autenticação e Perfis**:
    - Sistema de Login unificado (Email/Username).
    - Cadastro automático para domínios corporativos (`@dex.co`, `@deca.com.br`, etc.).
    - Papeis de usuário: `ADMIN`, `FACILITIES`, `PORTARIA`, `USER`.
- **Módulo Portaria**:
    - Cadastro rápido de correspondências (Caixa/Envelope).
    - Geração de IDs internos rastreáveis.
    - Associação com email ou nome manual.
- **Módulo Facilities**:
    - Dashboard Kanban (Portaria -> Triagem -> Disponível -> Entregue).
    - Ações de Coleta e Alocação de Local (Armários/Salas).
    - **Assinatura Digital**: Captura de assinatura em canvas HTML5 na entrega.
    - Histórico de Entregas com filtros por data e busca textual.
- **Módulo Usuário**:
    - Dashboard "Minhas Encomendas" (Items vinculados ao email).
    - Lista de "Itens Não Reivindicados" (sem email vinculado).
- **Admin**:
    - Gestão de usuários (Listar, Criar Portaria).
    - Promoção/Rebaixamento de cargos.
    - Bloqueio/Desbloqueio de acesso (`is_active`).

### Segurança
- Hashing de senhas com `werkzeug.security`.
- Decorators `@login_required` e `@role_required` para proteção de rotas.

### Infraestrutura
- Banco de dados SQLite (`aeropost.db`).
- Script de inicialização (`init-db`) e criação de admin (`create-admin`).
