# Infraestrutura e Padrões de Git - AeroPost

Este arquivo contém informações técnicas sobre o ambiente de produção e as regras de versionamento do projeto. 

> [!NOTE]
> Para regras específicas da Landing Page (estática), consulte o [INFRASTRUCTURE-LANDING.md](file:///c:/00Projetos/AeroPost/landing/INFRASTRUCTURE-LANDING.md).

Para instruções passo a passo de deployment, consulte o [UPGRADE_MANUAL.md](file:///c:/00Projetos/AeroPost/UPGRADE_MANUAL.md).

## 🖥️ Servidor (VPS)

- **Endereço IP:** `76.13.71.38`
- **Site Principal:** `kran.technology`
- **Site Landing/Demo:** `aeropost.kran.technology`
- **Site-Client-Dexco:** `kran.technology/Dexco/AeroPost`
- **Caminho Landing/Demo:** `/var/www/aeropost-demo`
  - **Banco de Dados:** `aeropost_demo.db`
- **Serviço Demo:** `aeropost-demo.service`
- **Caminho Client Dexco Produção:** `/var/www/Dexco/AeroPost`
- **Caminho Client Dexco Homologação:** `/var/www/Dexco/hml/AeroPost`
- **Caminho Client Dexco Desenvolvimento:** `/var/www/Dexco/dev/AeroPost`
  - **Banco de Dados:** `aeropost.db`
- **Serviço Client Dexco (Prod):** `aeropost.service` (Porta 8000)
- **Serviço Client Dexco (HML):** `aeropost-hml.service` (Porta 8001)
- **Nginx Config (Dexco):** `/etc/nginx/sites-available/aeropost`
  -- **Caminho Novos Clientes Produção:** `/var/www/<ClientName>/AeroPost`
  -- **Caminho Novos Clientes Homologação:** `/var/www/<ClientName>/hml/AeroPost`
  -- **Caminho Novos Clientes Desenvolvimento:** `/var/www/<ClientName>/dev/AeroPost`
    - **Banco de Dados:** `aeropost.db`
- **Usuário SSH:** `root`
- **Comando de Acesso:** `ssh root@76.13.71.38`
- **Banco de Dados Local:** SQLite (`aeropost.db`)

### 🏢 Tabela de Ambientes

| Ambiente | Função | URL | Caminho na VPS |
| :--- | :--- | :--- | :--- |
| **DEV** | Desenvolvimento local | `localhost:5000` | N/A |
| **HML** | Homologação / Testes | `aeropost.kran.technology/Dexco/hml/` | `/var/www/Dexco/hml/AeroPost` |
| **PRD** | Produção | `kran.technology/Dexco/AeroPost` | `/var/www/Dexco/AeroPost` |
| **DEMO** | Demonstração Comercial | `aeropost.kran.technology/demo` | `/var/www/aeropost-demo` |

- **Gerenciador de Arquivos:** `https://aeropost.kran.technology/filebrowser/`
- **Serviço File Browser:** `filebrowser.service`
- **Porta Interna:** `8080` (Proxy reverso via Nginx)
---

## 🌿 Padrões de Git (Git Flow)

Para manter o repositório organizado, adotamos as seguintes nomenclaturas:

### 1. Ramos Principais
- **`main`**: Código estável e testado Demo e novas implantações.
- **`dev/<iniciais>/<versão>`**: Ramos de desenvolvimento por programador.
  - Ex: `dev/d/2.0.0` (d = Desire)
  - Ex: `dev/p/1.2.2` (p = Padula)

### 2. Ramos de Lançamento (Release/Client)
- **`client/<nome>/v<versão>`**: Ramos específicos para entrega em produção.
  - Versão atual em dev: `v3.1.4`
  - *Nota: Estes ramos podem conter configurações específicas de .env para o cliente.*

### 3. Tags (Versões Estáveis)
- **`v<versão>-<sufixo>`**: Pontos fixos no tempo.
  - Ex: `v2.0.0-dexco`
  - Ex: `v1.2.2-d`

---

## 🛠️ Procedimento de Upgrade Seguro (Checklist Produção)

Para atualizar o servidor sem erros, siga rigorosamente esta sequência:

### 1. Acesso e Preparação
```bash
# Entrar na pasta do projeto
cd /var/www/Dexco/AeroPost

### Banco de Dados (SQLite)
- Caminho: `/var/www/Dexco/AeroPost/aeropost.db`
- Backups: Localizados em `/var/www/Dexco/AeroPost/backups/`

### Banco de Dados Clientes (SQLite)
- Caminho: `/var/www/<ClientName>/AeroPost/aeropost.db`
- Backups: Localizados em `/var/www/<ClientName>/AeroPost/backups/`

#### Comando de Backup Manual
```bash
mkdir -p /var/www/Dexco/AeroPost/backups
cp /var/www/Dexco/AeroPost/aeropost.db /var/www/Dexco/AeroPost/backups/aeropost_backup_$(date +%Y%m%d_%H%M%S).db
```

# Ativar o ambiente virtual
# (No Linux use bin/activate)
source .venv/bin/activate

# Sair do ambiente virtual
deactivate
```

### 2. Backup de Segurança (CRÍTICO)
```bash
# Recomenda-se usar a data e hora no nome do arquivo
cp aeropost.db aeropost.db.backup_$(date +%Y%m%d_%H%M)
```

### 3. Atualização de Código e Dependências
```bash
# Limpar nomes antigos e baixar novos do GitHub
git fetch --prune origin

# Entrar no branch de produção correspondente
git checkout client/dexco/v2.0.0

# ⚠️ SEMPRE instale as dependências (pode haver bibliotecas novas)
pip install -r requirements.txt
```

### 4. Aplicação de Migrações
```bash
# Executa o script que adapta o banco de dados sem apagar os dados
# IMPORTANTE: Se o banco tiver nome diferente (ex: Demo), use DATABASE_URL
export DATABASE_URL=aeropost_demo.db # Apenas se necessário (Ambiente Demo)
python migrations/v3.0.0.py
```

### 5. Reinicialização e Verificação
```bash
# Reinicia o serviço correspondente (aeropost ou aeropost-demo)
systemctl restart <nome_do_serviço>

# Verifica se o serviço subiu sem erros
systemctl status <nome_do_serviço>

# Se der erro 502, olhe os logs aqui:
journalctl -u aeropost -n 50 --no-pager
```

---

## 🎨 Padrões de Interface (UI/UX)

Para manter a consistência e funcionalidade em todo o sistema:

### 1. Tabelas Ordenáveis
Toda tabela de dados deve preferencialmente suportar ordenação por clique no cabeçalho.
- **Implementação**:
  1. A `<table>` deve possuir um `id` único.
  2. Os cabeçalhos `<th>` ordenáveis devem ter a classe `sortable`.
  3. Devem chamar `onclick="sortTable('ID_DA_TABELA', INDICE)"`.
- **Exemplo**:
  ```html
  <table id="minha-tabela">
    <thead>
      <tr>
        <th class="sortable" onclick="sortTable('minha-tabela', 0)">Nome</th>
      </tr>
    </thead>
  </table>
  ```
- **Nota**: A lógica global está centralizada em `templates/base.html`.

---

## 🧹 Higiene de Código e Testes

### Arquivos Temporários
- Logs de erro, dumps de terminal ou saídas de debug gerados manualmente (`.txt`, `.log`) **DEVEM** ser salvos dentro da pasta `tests/`.
- **Exemplo**: `pytest > tests/debug_log.txt`
- **IMPORTANTE**: Scripts de migração manual (ex: `update_db_*.py`) e/ou arquivos de teste descartáveis e/ou arquivos descartáveis devem ser **DELETADOS** imediatamente após o sucesso da operação.
- Mantenha a raiz do projeto limpa, contendo apenas arquivos de configuração essenciais (`.env`, `requirements.txt`, `schema.sql`, `pytest.ini`, etc.).

---

## 📂 Padrões de Organização de Arquivos

Para manter a escalabilidade do AeroPost, siga esta estrutura para novos scripts:

### 1. `/migrations`
- **O que**: Scripts que alteram a estrutura do banco de dados (DDL).
- **Regra**: Nomear por versão (ex: `v4.0.0.py`). Devem ser idempotentes (poder rodar mais de uma vez sem erro fatal).

> [!IMPORTANT]
> **Atenção com Alterações no Banco**: Sempre que você alterar o `schema.sql` ou adicionar colunas/tabelas novas, é **OBRIGATÓRIO** criar um script de migração correspondente nesta pasta. Isso garante que as bases de dados existentes em produção (Dexco, Demo, etc.) possam ser atualizadas sem perda de dados.

### 2. `/utils`
- **O que**: Ferramentas auxiliares, funções compartilhadas e **scripts de utilidade operacional**.
- **Exemplo**: Scripts para popular dados iniciais, limpeza de logs ou exportações customizadas que não são disparadas pelo usuário no front-end.

### 3. `/scripts`
- **O que**: Automações que rodam via agendamento (Cron) ou disparadores externos ao servidor web Flask.
- **Exemplo**: `cron_notifications.py`.

### 4. `/tests`
- **O que**: Arquivos de teste automatizado (`test_*.py`) e massas de dados exclusivas para o ambiente de testes (`fixtures`).

---
## 📂 Gerenciador de Arquivos (File Browser)

O File Browser está configurado como um Proxy Reverso através do Nginx, permitindo a gestão visual de arquivos e edição de configurações diretamente pelo navegador.

### 1. Configurações de Acesso
- **URL:** `https://aeropost.kran.technology/filebrowser/`
- **Utilizador:** `padula.one`
- **Escopo (Scope):** `/` (Acesso total à raiz do servidor)
- **Base de Dados:** `/etc/filebrowser/filebrowser.db`

> [!WARNING]
> **Segurança de Senha**: O sistema exige um mínimo de 12 caracteres. Alterações de senha via interface ou CLI devem respeitar este limite.

### 2. Integração Nginx
A rota está definida no arquivo `/etc/nginx/sites-available/aeropost-landing`. 
- **Upload Limit:** Configurado para `500M` no bloco `client_max_body_size`.

---

## 🚀 Comandos Úteis (CLI)

- `flask bootstrap`: Faz o setup completo (DB + Admin + Unidade + Local) em um só comando.
- `flask init-db`: Inicializa apenas as tabelas do banco de dados.
- `flask create-admin`: Cria apenas um novo usuário administrador (Interativo).
- `flask test-email`: Testa as configurações de SMTP.

### Gerenciamento do File Browser
- `systemctl restart filebrowser`: Reinicia o serviço do gerenciador.
- `systemctl stop filebrowser`: Para o serviço (necessário para manipulação direta do banco `.db`).
- `filebrowser users update padula.one --password <nova_senha> --database /etc/filebrowser/filebrowser.db`: Atualiza senha via terminal.
