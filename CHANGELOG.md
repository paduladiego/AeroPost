# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [v1.2.0] - 2026-01-15
### Adicionado
- **Gestão Dinâmica de Configurações**:
    - Nova página `Configurações` para admins e facilities.
    - CRUD completo para **Tipos de Item** (Envelope, Caixa...).
    - CRUD completo para **Locais de Alocação** (Armários, Salas...).
    - CRUD completo para **Empresas/Unidades** (Dexco, Deca...).
    - **Gestão de Domínios**: Admin pode definir quais domínios de email são permitidos no cadastro.
- **Exportação de Dados**:
    - Botão "Exportar CSV" no Histórico, gerando relatório detalhado de entregas.

## [v1.1.0] - 2026-01-15
### Adicionado
- **Entrega Segura via Senha**:
    - Alternativa à assinatura digital.
    - O destinatário digita sua senha de login para confirmar o recebimento.
    - Badge "Autenticado via Senha" no comprovante.
- **Landing Page Comercial**:
    - Nova `index.html` com apresentação do produto (KRÒS / Desire Studios).
    - Tabela de preços e funcionalidades.
### Alterado
- **Fluxo Otimizado**:
    - Identificação do destinatário movida da Portaria para o Facilities (Triagem).
    - Portaria foca apenas no registro rápido (Tipo/Rastreio).

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
