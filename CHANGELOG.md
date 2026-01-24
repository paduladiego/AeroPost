# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [v4.1.1] - 2026-01-24

### 🛠️ Refatoração e Melhorias de UI
- **Código Limpo (DRY) 🧹**: Implementação massiva de Macros Jinja2 para padronizar `Badges de Status` e `Modais de Configuração`, reduzindo duplicação de código e facilitando manutenção.
- **Componentes Reutilizáveis**: O Modal de Ocorrência foi centralizado e agora é compartilhado entre o Dashboard e o Histórico.
- **Home do Usuário Turbinada 🏠**:
    - **Ordenação**: Agora é possível ordenar as tabelas clicando nos cabeçalhos.
    - **Busca Instantânea**: Novo campo de filtro que pesquisa em tempo real nas duas tabelas da tela inicial.
- **Regras de Negócio**: Ajuste na permissão de recuperação de itens; administradores agora podem reabrir itens com status `ENTREGUE` (além de `DEVOLVIDO`).


## [v4.1.0] - 2026-01-24

### 🛂 Auditoria e Ocorrências
- **Registro de Ocorrências (Extraordinário) ⚠️**: Implementação de sistema para registro de itens Extraviados, Devolvidos ou Recuperados com validação por senha.
- **Auditoria de Histórico 📈**: O histórico agora exibe notas de ocorrências e status diferenciados para acompanhamento de perdas.

## [v4.0.0] - 2026-01-24

### 📱 Aplicação (App)
- **Suporte Multi-Unidades (Core) 🏢**:
    - Implementação de arquitetura multi-tenant para gerenciar múltiplos prédios/unidades em uma única conta.
    - Campos `unit_id` adicionados a itens, locais, movimentos e grupos de e-mail.
    - Seletor de Unidade Ativa integrado ao Navbar para troca rápida de contexto operacional.
    - Filtro global de dados baseado na unidade selecionada na sessão.
    - Atribuição de `default_unit_id` para usuários, definindo a unidade padrão ao logar.
- **Gestão de Perfil e Edição de Usuários 👥**: 
    - Nova funcionalidade que permite ao usuário editar seus próprios dados diretamente pela interface.
    - **Edição Administrativa**: Usuários com perfil `ADMIN` ou `FACILITIES` podem editar dados de outros usuários (Nome, E-mail, Unidade, etc.) através de um botão de ação na listagem que direciona para a página de perfil.
    - **Segurança Root Mantida**: A trava de segurança que impede a alteração de dados sensíveis (como senha) do administrador principal (ID 1) via interface web permanece ativa.
- **Segurança de Conta Root (ID 1) 🔐**: Implementada trava de segurança que bloqueia a troca ou reset de senha do administrador principal via interface web, garantindo proteção contra sequestro de conta (mudanças apenas via acesso direto ao banco de dados).
- **Criação de Admin Interativa 🛠️**: O comando `flask create-admin` agora é interativo, permitindo definir Username, Senha, Nome e E-mail via terminal.
- **Automação Bootstrap 🚀**: Novo comando `flask bootstrap` que orquestra a inicialização do banco, criação do admin e configuração da primeira unidade e local em uma única execução.
- **Melhoria na Gestão de Usuários 👥**: 
    - Refatoração da tela administrativa com separação de usuários ativos e bloqueados.
    - **Interatividade**: Tabelas colapsáveis, classificação de colunas e **relógio de sistema em tempo real** no rodapé para sincronia operacional.
    - **Busca Global**: Novo campo de pesquisa em tempo real que filtra por Nome, E-mail, Unidade, Função ou Andar em todas as tabelas simultaneamente.
- **Melhoria no Painel da Portaria 🛂**:
    - Separação da visualização em duas tabelas: **Recebidos Hoje** e **Pendentes (Dias Anteriores)**.
    - Destaque visual (cor amarela) para itens pendentes de dias passados para facilitar a triagem.
    - Contadores e cabeçalhos colapsáveis integrados ao painel.
- **Melhoria no Cadastro de Equipe (Portaria) 🛂**: O formulário de cadastro de novos porteiros agora exige a seleção explícita da Unidade de trabalho no momento da criação.
- **Segurança de Unidade (Portaria) 🛡️**: Implementada trava para usuários de Portaria, limitando visualização e registro de encomendas exclusivamente à sua unidade de cadastro. Além disso, o acesso à edição de perfil foi desativado para este cargo por questões de governança de dados.

### 🌐 Landing Page
- **Isolamento de Landing 🚀**: Refatoração completa para portabilidade estática total. A pasta `landing/` agora é independente do Flask.
- **ChangeLog Público com Fallback**: Nova página que renderiza o Markdown via JS com sistema de fallback inteligente (local ou raiz).
- **Componente de Menu DRY**: Cabeçalho unificado em `menu.html` carregado dinamicamente via JavaScript em todas as páginas da landing.
- **Arquitetura de Assets (Best Practices)**: Extração de todos os estilos e scripts internos para arquivos externos em `/css` e `/js`.
- **Governança de Desenvolvimento**: Adicionado `INFRASTRUCTURE-LANDING.md` para regras de manutenção da landing page.

## [v3.1.4] - 2026-01-22
### Adicionado
- **Notificações Recorrentes 🔔**: Implementada automação via script `cron_notifications.py` que reenviar alertas a cada 3 dias para encomendas pendentes.
- **Reenvio Manual**: Novo botão de sino (🔔) no Painel Facilities para disparo imediato de notificações.
- **Gestão de Banco de Dados**: Adicionada coluna `last_notified_at` para rastreamento preciso de alertas.
- **Otimização de UI/UX**:
    - **Tabelas Responsivas**: Novo layout mobile-first com `table-responsive`.
    - **Gestão de Espaço**: Ocultação automática de colunas secundárias em telas pequenas e ajuste de espaçamento entre botões de ação.
    - **Refatoração DRY**: Centralização da lógica de ordenação de tabelas no template base.
    - **Edição de Grupos**: Possibilidade de editar membros de grupos de e-mail diretamente nas configurações.
### Corrigido
- **Navegação**: Correção de erros de rota no Painel Facilities e ajuste na persistência de abas após ações.
- **Estética**: Alinhamento de logotipos e ajustes de branding.
### Segurança & Qualidade
- **Cobertura de Testes (End-to-End)**:
    - Implementada suíte completa de testes de integração cobrindo os módulos Admin, Portaria e Facilities.
    - Validação automática de fluxos críticos: Registro -> Triagem -> Entrega (Senha/Assinatura).
    - CRUD automatizado para configurações de sistema e usuários.


## [v3.0.2] - 2026-01-20
### Adicionado
- **Gestão Inteligente de Versão 🏷️**: Centralizada a versão no código (`base_version`), permitindo adicionar sufixos (ex: `-demo`, `-dexco`) via variável de ambiente `APP_SUFFIX` no `.env`. Isso evita a necessidade de atualizar o número da versão manualmente em cada servidor.


## [v3.0.1] - 2026-01-20
### Alterado
- **Neutralidade de Marca**: Generalizados placeholders e textos de ajuda na página de cadastro corporativo para remover referências específicas à Dexco/Deca.


## [v3.0.0] - 2026-01-20
### Adicionado
- **Persistência de Estado (UX)**: O sistema agora lembra a aba ativa no Painel Facilities. Redirecionamentos inteligentes mantêm o contexto do usuário.
- **Ordenação Dinâmica de Tabelas 📊**: Reorganização instantânea por ID, Item, Destinatário ou Local com clique no cabeçalho.
- **Canal de Suporte 🆘**: Botão "Reportar Problema" com modal integrado e envio automático de metadados para suporte.
- **Grupos de Email**: Gestão de grupos para notificações em lote na alocação de itens.
- **Melhorias Visuais e Portaria**: Unificação de colunas ID/Rastreio, melhor visibilidade de itens pendentes na portaria e Favicon (✉️).
### Corrigido
- **Autenticação Híbrida**: Persistência de e-mail entre telas e validação assíncrona de usuários corporativos.
- **Responsividade**: Ajustes no canvas de assinatura e larguras de tabelas.

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
