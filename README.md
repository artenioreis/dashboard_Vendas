# Sistema de Análise Gerencial (SAG)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python) ![Flask](https://img.shields.io/badge/Flask-2.0-black?logo=flask) ![JavaScript](https://img.shields.io/badge/JavaScript-ES6-yellow?logo=javascript) ![Chart.js](https://img.shields.io/badge/Chart.js-4.x-ff6384?logo=chartdotjs)

Um painel de gestão (dashboard) web desenvolvido para fornecer uma visão integrada e em tempo real das principais métricas de um negócio. A aplicação centraliza dados de **Vendas**, **Contas a Pagar** e **Contas a Receber**, apresentando-os de forma visual e intuitiva através de gráficos e tabelas interativas.

## 🚀 Funcionalidades Principais

O sistema é dividido em quatro dashboards principais:

### 1. Dashboard Geral
Uma tela inicial que consolida os KPIs (Indicadores-Chave de Desempenho) mais importantes de cada seção para uma análise rápida:
* **Vendas vs. Compras:** Gráfico mensal comparativo do volume financeiro.
* **Top 5 Maiores Devedores:** Identificação rápida dos principais clientes com saldo a receber.
* **Top 5 Maiores Credores:** Visão clara dos principais fornecedores com saldo a pagar.

### 2. Módulo de Vendas
Análise detalhada da performance comercial da empresa, com filtros por período:
* Gráfico de totais mensais de Vendas e Compras.
* Gráfico de evolução diária das vendas.
* Ranking dos 5 clientes que mais compraram.
* Ranking dos 10 produtos mais vendidos.

### 3. Módulo de Contas a Receber
Gestão completa dos títulos a receber, com busca dinâmica por cliente:
* KPIs de **Valor Total a Receber**, **Total de Títulos** e **Cliente com Maior Atraso**.
* Gráfico com a distribuição da dívida por faixa de vencimento (A Vencer, Vencido 1-30 dias, etc.).
* Ranking dos 5 maiores devedores.
* Tabela detalhada com todos os títulos em aberto.

### 4. Módulo de Contas a Pagar
Visão clara e organizada das obrigações financeiras da empresa, com busca por fornecedor:
* KPIs de **Valor Total a Pagar**, **Total de Títulos** e **Principal Credor**.
* Gráfico com a distribuição das contas por faixa de vencimento.
* Ranking dos 5 maiores credores.
* Tabela detalhada com os títulos a pagar.

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python
    * **Flask:** Micro-framework web para a criação da API e serviço das páginas.
    * **SQLAlchemy:** ORM para a comunicação com o banco de dados.
    * **pyodbc:** Driver para a conexão com o SQL Server.
* **Frontend:**
    * HTML5
    * CSS3 (com design responsivo)
    * JavaScript (ES6+)
    * **Chart.js:** Biblioteca para a renderização dos gráficos interativos.
* **Banco de Dados:**
    * Microsoft SQL Server

## ⚙️ Pré-requisitos

Antes de começar, garanta que você tem os seguintes softwares instalados:
* Python 3.8 ou superior
* Microsoft ODBC Driver for SQL Server
* Um servidor SQL Server com a base de dados (`DMD`) e as tabelas utilizadas pelo projeto.

## 🚀 Instalação e Execução

Siga os passos abaixo para executar o projeto localmente:

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
    cd seu-repositorio
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    # Para Windows
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

    # Para macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Instale as dependências:**
    Crie um ficheiro `requirements.txt` com o seguinte conteúdo:
    ```txt
    Flask
    SQLAlchemy
    pyodbc
    ```
    E depois instale-as:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure a Conexão com o Banco de Dados:**
    Abra o ficheiro `app.py` e ajuste a string de conexão (`odbc_conn_str`) com as suas credenciais do SQL Server:
    ```python
    odbc_conn_str = (
        'DRIVER={ODBC Driver 18 for SQL Server};'
        'SERVER=SEU_SERVIDOR;'      # Ex: localhost
        'DATABASE=SUA_DATABASE;'  # Ex: DMD
        'UID=SEU_USUARIO;'        # Ex: sa
        'PWD=SUA_SENHA;'          # Ex: arte171721
        'Encrypt=yes;'
        'TrustServerCertificate=yes;'
    )
    ```

5.  **Execute a Aplicação:**
    ```bash
    python app.py
    ```

6.  **Acesse o Dashboard:**
    Abra o seu navegador e acesse [http://127.0.0.1:5000](http://127.0.0.1:5000).

## 📈 Melhorias Futuras

* [ ] Implementar autenticação de utilizadores.
* [ ] Adicionar filtros por vendedor nos dashboards de Vendas e Contas a Receber.
* [ ] Criar um módulo de controlo de stock.
* [ ] Permitir a exportação dos dados das tabelas para CSV ou Excel.
