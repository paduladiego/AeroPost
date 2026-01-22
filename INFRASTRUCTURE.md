# Infraestrutura e Padrões de Git - AeroPost

Este arquivo contém informações técnicas sobre o ambiente de produção e as regras de versionamento do projeto.

## 🖥️ Servidor (VPS)

- **Endereço IP:** `76.13.71.38`
- **Site Principal:** `kran.technology`
- **Site Landing/Demo:** `aeropost.kran.technology`
- **Site-Client-Dexco:** `kran.technology/Dexco/AeroPost`
- **Caminho Landing/Demo:** `/var/www/aeropost-demo`
- **Serviço Demo:** `aeropost-demo.service`
- **Caminho Client Dexco:** `/var/www/Dexco/AeroPost`
- **Serviço Client Dexco:** `aeropost.service`
  -- **Caminho Novos Clientes:** `/var/www/<ClientName>/AeroPost`
- **Usuário SSH:** `root`
- **Comando de Acesso:** `ssh root@76.13.71.38`
- **Banco de Dados Local:** SQLite (`aeropost.db`)

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
  - Versão atual em dev: `v3.0.0`
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
python migrations/v2.0.0.py
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
