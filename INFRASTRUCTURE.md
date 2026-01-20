# Infraestrutura e Padrões de Git - AeroPost

Este arquivo contém informações técnicas sobre o ambiente de produção e as regras de versionamento do projeto.

## 🖥️ Servidor (VPS)

- **Endereço IP:** `76.13.71.38`
- **Site Principal:** `kran.technology`
- **Site Landing/Demo:** `aeropost.kran.technology`
- **Site-Client-Dexco:** `kran.technology/Dexco/AeroPost`
- **Caminho Landing/Demo:** `/var/www/aeropost-demo`
- **Caminho Client Dexco:** `/var/www/Dexco/AeroPost`
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
# Reinicia o serviço principal
systemctl restart aeropost

# Verifica se o serviço subiu sem erros (Status deve ser 'active (running)')
systemctl status aeropost

# Se der erro 502, olhe os logs aqui:
journalctl -u aeropost -n 50 --no-pager
```
