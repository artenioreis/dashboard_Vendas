# app.py
import urllib
from flask import Flask, jsonify, render_template, request
from sqlalchemy import create_engine, text
import logging
from datetime import date, timedelta

# Configura o logging
logging.basicConfig(level=logging.INFO)

# ===============================
# 1) Inicialização do Flask
# ===============================
app = Flask(__name__)

# ===============================
# 2) Conexão com SQL Server
# ===============================
odbc_conn_str = (
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=localhost;'
    'DATABASE=DMD;'
    'UID=sa;'
    'PWD=arte171721;'
    'Encrypt=yes;'
    'TrustServerCertificate=yes;'
)
params = urllib.parse.quote_plus(odbc_conn_str)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")


# ===============================
# 3) Rota Principal (Frontend)
# ===============================
@app.route('/')
def index():
    return render_template("index.html")


def get_date_params():
    """Função auxiliar para pegar as datas da requisição ou usar um padrão."""
    today = date.today()
    start_date_default = date(today.year, 1, 1).strftime('%Y-%m-%d')
    end_date_default = today.strftime('%Y-%m-%d')

    start_date = request.args.get('start_date', start_date_default)
    end_date = request.args.get('end_date', end_date_default)
    return start_date, end_date

# ===============================
# 4) Endpoint: Totais Mensais
# ===============================
@app.route('/totais-mensais')
def totais_mensais():
    start_date, end_date = get_date_params()
    try:
        sql = text("""
            SELECT
                ano, mes, SUM(total_vendas) AS total_vendas, SUM(total_compras) AS total_compras
            FROM (
                SELECT YEAR(c.Dat_Emissao) AS ano, MONTH(c.Dat_Emissao) AS mes, SUM(i.Qtd_Produto * i.prc_unitario) AS total_vendas, 0 AS total_compras
                FROM NFSCB c JOIN NFSIT i ON c.Num_nota = i.Num_nota
                WHERE c.Tip_Saida IN ('V', 'O') AND CONVERT(date, c.Dat_Emissao) BETWEEN :start_date AND :end_date
                GROUP BY YEAR(c.Dat_Emissao), MONTH(c.Dat_Emissao)
                UNION ALL
                SELECT YEAR(c.Dat_Emissao) AS ano, MONTH(c.Dat_Emissao) AS mes, 0 AS total_vendas, SUM(e.Qtd_pedFat * e.Prc_Unitario) AS total_compras
                FROM NFSCB c JOIN NFEIT e ON c.Cod_Estabe = e.Cod_Estabe
                WHERE CONVERT(date, c.Dat_Emissao) BETWEEN :start_date AND :end_date
                GROUP BY YEAR(c.Dat_Emissao), MONTH(c.Dat_Emissao)
            ) AS totais_mensais
            GROUP BY ano, mes ORDER BY ano, mes;
        """)
        params = {"start_date": start_date, "end_date": end_date}
        with engine.connect() as conn:
            result = conn.execute(sql, params)
            data = [{"ano": int(r.ano), "mes": int(r.mes), "total_vendas": float(r.total_vendas or 0), "total_compras": float(r.total_compras or 0)} for r in result]
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Erro em /totais-mensais: {e}")
        return jsonify({"error": str(e)}), 500


# ===============================
# 5) Endpoint: Série Diária
# ===============================
@app.route('/serie-diaria')
def serie_diaria():
    start_date, end_date = get_date_params()
    try:
        sql = text("""
            SELECT CONVERT(date, c.Dat_Emissao) AS data, SUM(i.Qtd_Produto * i.Prc_Unitario) AS total_vendas
            FROM NFSIT i JOIN NFSCB c ON i.Num_Nota = c.Num_Nota
            WHERE CONVERT(date, c.Dat_Emissao) BETWEEN :start_date AND :end_date
            GROUP BY CONVERT(date, c.Dat_Emissao) ORDER BY data
        """)
        params = {"start_date": start_date, "end_date": end_date}
        with engine.connect() as conn:
            result = conn.execute(sql, params)
            data = [{"data": str(r.data), "total_vendas": float(r.total_vendas or 0)} for r in result]
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Erro em /serie-diaria: {e}")
        return jsonify({"error": str(e)}), 500


# ===============================
# 6) Endpoint: Cliente Top
# ===============================
@app.route('/cliente-top')
def cliente_top():
    start_date, end_date = get_date_params()
    try:
        sql = text("""
            SELECT TOP 10
                cl.Razao_Social,
                SUM(i.Qtd_Produto * i.Prc_Unitario) as total_gasto
            FROM NFSCB c
            JOIN NFSIT i ON c.Num_Nota = i.Num_Nota
            JOIN clien cl ON c.Cod_Cliente = cl.Codigo
            WHERE c.Tip_Saida IN ('V', 'O')
              AND CONVERT(date, c.Dat_Emissao) BETWEEN :start_date AND :end_date
            GROUP BY cl.Razao_Social
            ORDER BY total_gasto DESC
        """)
        params = {"start_date": start_date, "end_date": end_date}
        with engine.connect() as conn:
            result = conn.execute(sql, params)
            data = [{"Razao_Social": r.Razao_Social, "total_gasto": float(r.total_gasto or 0)} for r in result]
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Erro em /cliente-top: {e}")
        return jsonify({"error": f"Erro no servidor: {e}"}), 500

# ===============================
# 7) NOVO Endpoint: Produtos Top
# ===============================
@app.route('/produtos-top')
def produtos_top():
    start_date, end_date = get_date_params()
    try:
        # Consulta para buscar os 10 produtos mais vendidos por quantidade
        sql = text("""
            SELECT TOP 10
                P.Descricao,
                SUM(S.Qtd_Produto) as total_vendido
            FROM NFSIT AS S
            INNER JOIN PRODU AS P ON S.Cod_Produto = P.Codigo
            INNER JOIN NFSCB AS C ON S.Num_Nota = C.Num_Nota
            WHERE CONVERT(date, C.Dat_Emissao) BETWEEN :start_date AND :end_date
              AND C.Tip_Saida IN ('V', 'O')
            GROUP BY P.Descricao
            ORDER BY total_vendido DESC
        """)
        params = {"start_date": start_date, "end_date": end_date}
        with engine.connect() as conn:
            result = conn.execute(sql, params)
            data = [{"descricao": r.Descricao, "total_vendido": float(r.total_vendido or 0)} for r in result]
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Erro em /produtos-top: {e}")
        return jsonify({"error": f"Erro no servidor: {e}"}), 500


# ===============================
# 8) Rodar o Flask
# ===============================
if __name__ == "__main__":
    app.run(debug=True)

