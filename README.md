# AeroPost ✉️

**Sistema de Gestão de Correspondências e Encomendas Corporativas.**

O AeroPost é uma aplicação web desenvolvida para otimizar o fluxo de recebimento, triagem e entrega de encomendas em edifícios corporativos. Ele gerencia todo o ciclo de vida do item, desde a chegada na portaria até a assinatura digital do destinatário no ato da entrega.

## 🚀 Funcionalidades Principais

### 1. Portaria (Recepção)
- **Registro Rápido**: Cadastro de items com remetente, tipo (Caixa/Envelope) e rastreio.
- **Destinatário Flexível**: Vínculo com email corporativo ou nome manual (para visitantes/terceiros).
- **Geração de ID**: Criação automática de códigos internos (ex: `AP-20240115-AH2B`) para rastreabilidade.

### 2. Facilities (Triagem e Entrega)
- **Dashboard de Controle**: Visão em tempo real de itens na Portaria, em Triagem e Disponíveis.
- **Fluxo de Trabalho**:
    1.  **Coleta**: Facilities retira o item da portaria.
    2.  **Alocação**: Define onde o item ficará guardado (Armário, Sala, etc.).
    3.  **Entrega**: Realiza a entrega ao destinatário final.
- **Assinatura Digital**: Captura de assinatura direto na tela (tablet/celular) para comprovação de entrega.
- **Gestão de Usuários**: Bloqueio, desbloqueio e promoção de usuários (User -> Facilities).
- **Histórico**: Consulta de entregas passadas com filtros por data e busca textual.
- **Exportação CSV**: Geração de relatório detalhado de entregas para análise externa (v1.2+).
- **Gestão de Configurações**: (v1.2+) Interface para cadastro dinâmico de Tipos de Item, Locais, Empresas e Domínios de E-mail.

### 3. Colaboradores (Usuários Finais)
- **Auto-cadastro**: Registro permitido apenas para domínios corporativos autorizados (`@dex.co`, `@deca.com.br`, etc.).
- **Meus Itens**: Painel pessoal listando todas as encomendas vinculadas ao email do usuário.
- **Itens Não Reivindicados**: Lista pública de itens sem email vinculado para identificação ativa.

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3, Flask.
- **Banco de Dados**: SQLite.
- **Frontend**: HTML5, CSS3, Bootstrap 5.
- **Outros**: SignaturePad.js (assinaturas), Jinja2 (templates).

## ⚙️ Instalação e Execução Local

1.  **Clone o repositório**
    ```bash
    git clone https://github.com/SEU_USUARIO/aeropost.git
    cd aeropost
    ```

2.  **Crie e ative um ambiente virtual**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```

3.  **Instale as dependências**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Inicialize o Banco de Dados**
    ```bash
    flask init-db
    flask create-admin
    ```
    *Isso criará o usuário `admin` com senha `admin123`.*
    
    **(Para atualizações v1.2+) Execute a migração de dados:**
    ```bash
    python migrate_v120.py
    *(Opcional) Para adicionar a coluna `is_active` em bancos antigos:*
    ```bash
    python update_db_users.py
    ```

5.  **Execute a aplicação**
    ```bash
    flask run
    # ou
    python app.py
    ```
    Acesse em: `http://127.0.0.1:5000`

## 🔐 Perfis de Acesso

- **User**: Visualiza suas próprias encomendas.
- **Portaria**: Registra entrada de itens.
- **Facilities**: Gere todo o fluxo, aloca itens e realiza entregas.
- **Admin**: Acesso total, incluindo gestão de usuários.

## 📄 Licença

Este projeto foi desenvolvido como um MVP (Mínimo Produto Viável) para uso corporativo interno.

---
---
*Versão 1.2.0*
