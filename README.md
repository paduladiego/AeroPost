# AeroPost ✉️

**Sistema de Gestão de Correspondências e Encomendas Corporativas.**

O AeroPost é uma aplicação web desenvolvida para otimizar o fluxo de recebimento, triagem e entrega de encomendas em edifícios corporativos. Desenvolvido para eliminar o papel e garantir rastreabilidade total.

## 🚀 Funcionalidades Principais

### 1. Portaria (Recepção)
- **Registro Rápido**: Cadastro de items com remetente, tipo e rastreio.
- **Identificação**: Vínculo com email corporativo ou nome manual para terceiros.
- **Geração de ID**: Códigos internos automáticos (ex: `AP-20240115-AH2B`).

### 2. Facilities (Triagem e Entrega)
- **Gestão de Espaços**: Alocação de itens em armários ou salas específicas.
- **Entrega Híbrida**: Assinatura digital no dispositivo (tablet) ou autenticação via senha.
- **Auditoria**: Histórico completo com filtros e exportação CSV para relatórios.
- **Suporte Multi-Unidades**: Gestão de múltiplos prédios ou unidades corporativas com troca de contexto fluida.
- **Configurações Dinâmicas**: Cadastro de empresas, domínios, locais e tipos de item via interface.

### 3. Colaboradores (Usuários Finais)
- **Auto-cadastro**: Restrito a domínios corporativos autorizados.
- **Painel Pessoal**: Visualização de encomendas pendentes e histórico.

## 🏗️ Arquitetura Modular (v2.0.0)

O sistema utiliza **Flask Blueprints** para uma organização limpa:
- `/routes`: Lógica separada por módulos (auth, admin, portaria, facilities, settings).
- `/utils`: Centralização de banco de dados, middlewares e segurança.
- `/migrations`: Scripts de manutenção e evolução do banco.
- `/templates`: Estrutura organizada por contexto de uso.

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.12+ / Flask.
- **Banco de Dados**: SQLite (Desenvolvimento) / PostgreSQL (Produção).
- **Segurança**: Variáveis de ambiente (`.env`), Hashing de senhas (PBKDF2).
- **Frontend**: Bootstrap 5, SignaturePad.js.

## ⚙️ Instalação e Execução

### 1. Preparação
```bash
git clone https://github.com/SEU_USUARIO/aeropost.git
cd aeropost
python -m venv .venv
# Ative o venv (Scripts\activate no Windows ou source bin/activate no Linux)
pip install -r requirements.txt
```

### 2. Configuração (.env)
Crie um arquivo `.env` na raiz:
```env
SECRET_KEY=sua_chave_secreta_aqui
DATABASE_URL=aeropost.db
APP_VERSION=v2.0.0
```
> [!TIP]
> Em produção (VPS), utilize `DATABASE_URL=postgresql://user:pass@localhost/dbname`.

### 3. Inicialização (Novo Cliente)
Para configurar um novo cliente do zero em uma única etapa:
```bash
flask bootstrap
```
Este comando irá criar as tabelas, o administrador e a primeira unidade/local operacional.

### 4. Execução
```bash
python app.py
```

## 🔐 Perfis de Acesso

1. **User**: Colaborador final (vê apenas seus itens).
2. **Portaria**: Registro de entrada de encomendas.
3. **Facilities**: Gestor logístico (coleta, aloca e entrega).
4. **Facilities Portaria**: Perfil híbrido com acesso total aos fluxos de entrada e saída.
5. **Admin**: Gestor técnico (usuários e configurações de sistema).

## 📄 Licença e Marca

Desenvolvido por **Desire Studios Ltda** sob o selo tecnológico **KRÒS / Divisão KRAN**.
MVP focado em eficiência logística e conformidade digital.

---
**Versão Atual:** v3.1.4 (Stable)

## 🧪 Testes Automatizados

O AeroPost utiliza `pytest` para garantir a estabilidade das funções críticas. A suíte atual cobre:

- **Admin**: Gestão de usuários e configurações do sistema.
- **Portaria**: Registro de entrada e validação de dashboard.
- **Facilities**: Fluxo completo de coleta, alocação e entrega.

### Como rodar os testes:
1. Ative seu ambiente virtual:
   ```bash
   source .venv/Scripts/activate
   ```
2. Instale as dependências de teste:
   ```bash
   pip install pytest pytest-flask
   ```
3. Execute os testes:
   ```bash
   pytest
   ```

