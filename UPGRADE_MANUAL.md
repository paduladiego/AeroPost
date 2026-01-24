# Manual de Atualização AeroPost 🚀

Este guia contém o procedimento passo a passo para realizar atualizações seguras, desde o commit local até o deployment na VPS.

> [!IMPORTANT]
> **Fluxo Obrigatório**: NUNCA realize uma atualização diretamente em Produção (PRD) sem antes validá-la em Homologação (HML). O ambiente HML serve para garantir que as migrações de dados não gerem inconsistências ou "dados invisíveis".

---

## 1. Preparação Local (Desenvolvimento)

Sempre realize os commits e as tags no seu ambiente de desenvolvimento antes de subir para o servidor.

### Passo 1: Salvar alterações
```bash
git add .
git commit -m "Descrição clara das mudanças"
```

### Passo 2: Gerar versão (Tag)
Substitua `vX.Y.Z` pela versão atual (ex: `v3.1.4`).
```bash
# O sufixo -f força a atualização se a tag já existir
git tag -af vX.Y.Z -m "Release vX.Y.Z"
```

### Passo 3: Sincronizar com GitHub
```bash
git push origin main --tags -f
```

---

## 2. Atualização na VPS (SSH)

Conecte-se ao servidor: `ssh root@76.13.71.38`.

### 🧪 ambiente DEMO (`aeropost.kran.technology`)
Caminho: `/var/www/aeropost-demo`

```bash
cd /var/www/aeropost-demo

# 1. Atualizar Código
git fetch --all
git reset --hard origin/main

# 2. Ambiente e Migração
source .venv/bin/activate
pip install -r requirements.txt

# 💡 DICA: Defina a variável na mesma linha do comando para não "sujar" a sessão
DATABASE_URL=aeropost_demo.db python migrations/vX.Y.Z.py

# População de dados para demonstração (Divisões Desire Studio)
DATABASE_URL=aeropost_demo.db python utils/populate_units.py

# 3. Reiniciar
systemctl restart aeropost-demo
```

---

### 🏢 Ambiente do Cliente (Produção)
Caminho: `/var/www/<ClientName>/AeroPost`

```bash
cd /var/www/<ClientName>/AeroPost

# 1. Backup Preventivo (NUNCA PULE ESTE PASSO)
mkdir -p backups
cp aeropost.db backups/aeropost_$(date +%Y%m%d_%H%M).db

# 2. Atualizar Código
git fetch --all
git reset --hard origin/main

# 3. Ambiente e Migração
source .venv/bin/activate
pip install -r requirements.txt

# 💡 DICA: Use explicitamente o nome do banco para evitar erros de sessão
DATABASE_URL=aeropost.db python migrations/vX.Y.Z.py

systemctl restart aeropost
```

---

### 👥 Novos Clientes (`ClientName`)
Caminho: `/var/www/<ClientName>/AeroPost`

**Setup Rápido (Recomendado):**
1. Clone o repositório e configure o `.env`.
2. `flask bootstrap` (Siga os prompts para criar DB, Admin, Unidade e Local).
3. O sistema já estará pronto para uso imediato.

**Setup Manual (Caso o bootstrap falhe):**
1. `flask init-db` (Cria a estrutura das tabelas).
2. `flask create-admin` (Cria o usuário administrador via prompt).
3. Acesse o painel `/admin/settings` para cadastrar manualmente:
   - A primeira **Unidade** (Empresa).
   - O primeiro **Local** de alocação vinculado a essa unidade.
4. Acesse `/admin/users` para vincular o administrador à Unidade Padrão criada.

Para atualização de clientes existentes, siga o mesmo procedimento da Dexco, ajustando o caminho:
1. `cd /var/www/<ClientName>/AeroPost`
2. Backup do `aeropost.db`.
3. `git pull` / `git reset`.
4. Sobreescreva a variável: `DATABASE_URL=aeropost.db python migrations/v3.1.4.py`.
5. `systemctl restart aeropost` (ou o serviço específico do cliente).

---

## ⚠️ Dicas de Segurança (Higiene)

1. **Sessão do Terminal**: Se você usou `export DATABASE_URL=...` e vai mudar de pasta, SEMPRE use `unset DATABASE_URL` antes. 
2. **Caminho Seguro**: Prefira rodar a migração com a variável na frente: `DATABASE_URL=nome_do_banco.db python script.py`. Isso garante que o script só use aquele banco naquela execução específica.
3. **Limpeza**: Após o deployment, apague arquivos `.txt` ou scripts temporários que não fazem parte do repositório oficial.
4. **Mapeamento Multi-Unidade**: Em caso de upgrades estruturais (v4.0.0+), caso os dados históricos sumam da interface, utilize o script `python utils/fix_hml_mapping.py` para unificar os registros na unidade principal (ID 1).
