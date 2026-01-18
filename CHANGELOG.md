# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [v2.0.0] - 2026-01-18
### Adicionado
- **Papel Híbrido "Facilities Portaria"**:
    - Novo tipo de usuário `FACILITIES_PORTARIA` que unifica o acesso aos painéis de Portaria e Facilities.
    - Ação na tela de Gerenciar Usuários para conceder/revogar este acesso extra a usuários Facilities.
- **Melhorias no Painel Facilities**:
    - **Opção "Novo Cadastro"**: Possibilidade de cadastrar destinatários manuais diretamente na triagem (Alocar Local).
    - **Interface Inteligente**: Campos manuais (Nome, Andar/Setor) aparecem condicionalmente via JavaScript.
    - **Layout Compacto**: Redesign dos campos de triagem para otimizar espaço vertical.
- **Backend e Segurança**:
    - Migração de banco de dados para suporte ao novo `CHECK` de roles.
    - Atualização de todos os decorators `@role_required` para suporte ao papel híbrido.

## [v1.2.2d] - 2026-01-16
### Adicionado
- **Controle de Senhas e Segurança**:
    - Funcionalidade de **Troca de Senha Obrigatória**: Usuários podem ser forçados a mudar a senha no próximo login.
    - **Reset de Senha por Admin**: Botão 🔑 na listagem de usuários que redefine a senha para um padrão (`mudar123`) e exige troca imediata.
    - Nova rota `/change_password` e página dedicada para redefinição segura.
- **Melhorias na Gestão de Usuários**:
    - Refinamento visual na tabela de usuários com novos ícones de ação.
    - Verificação defensiva no backend para colunas de banco de dados durante transições de versão.

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
