# app.py
from flask import Flask, jsonify, render_template
from sqlalchemy import create_engine, text

# ===============================
# 1) Inicialização do Flask
# ===============================
app = Flask(__name__)

# ===============================
# 2) Conexão com SQL Server
# ===============================
# Usando sqlalchemy para facilitar a execução de SQLs
conn_str = (
    "mssql+pyodbc://sa:arte171721@localhost/DMD?"
    "driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes"
)
engine = create_engine(conn_str)

# ===============================
# 3) Rota Principal (Frontend)
# ===============================
@app.route('/')
def index():
    # Renderiza o HTML da pasta templates/index.html
    return render_template("index.html")


# ===============================
# 4) Endpoint: Totais Mensais
# ===============================
@app.route('/totais-mensais')
def totais_mensais():
    sql = text("""
        SELECT
            ano,
            mes,
            SUM(total_vendas) AS total_vendas,
            SUM(total_compras) AS total_compras
        FROM (
            SELECT
                YEAR(c.Dat_Emissao) AS ano,
                MONTH(c.Dat_Emissao) AS mes,
                SUM(i.Qtd_Produto * i.prc_unitario) AS total_vendas,
                0 AS total_compras
            FROM NFSCB c
            JOIN NFSIT i ON c.Num_nota = i.Num_nota
            WHERE c.Tip_Saida IN ('V', 'O')
              AND c.Dat_Emissao BETWEEN :start_date AND :end_date
            GROUP BY YEAR(c.Dat_Emissao), MONTH(c.Dat_Emissao)

            UNION ALL

            SELECT
                YEAR(c.Dat_Emissao) AS ano,
                MONTH(c.Dat_Emissao) AS mes,
                0 AS total_vendas,
                SUM(e.Qtd_pedFat * e.Prc_Unitario) AS total_compras
            FROM NFSCB c
            JOIN NFEIT e ON c.cod_estabe = e.cod_estabe
            WHERE c.Dat_Emissao BETWEEN :start_date AND :end_date
            GROUP BY YEAR(c.Dat_Emissao), MONTH(c.Dat_Emissao)
        ) AS totais_mensais
        GROUP BY ano, mes
        ORDER BY ano, mes;
    """)

    params = {"start_date": "2025-01-01", "end_date": "2025-12-31"}
    with engine.connect() as conn:
        result = conn.execute(sql, params)
        data = [{"ano": int(r.ano), "mes": int(r.mes),
                 "total_vendas": float(r.total_vendas or 0),
                 "total_compras": float(r.total_compras or 0)} for r in result]
    return jsonify(data)


# ===============================
# 5) Endpoint: Série Diária
# ===============================
@app.route('/serie-diaria')
def serie_diaria():
    sql = text("""
        SELECT 
            CONVERT(date, c.Dat_Emissao) AS data,
            SUM(i.Qtd_Produto * i.Prc_Unitario) AS total_vendas
        FROM NFSIT i
        JOIN NFSCB c ON i.Num_Nota = c.Num_Nota
        WHERE c.Dat_Emissao BETWEEN :start_date AND :end_date
        GROUP BY CONVERT(date, c.Dat_Emissao)
        ORDER BY data
    """)

    params = {"start_date": "2025-01-01", "end_date": "2025-12-31"}
    with engine.connect() as conn:
        result = conn.execute(sql, params)
        data = [{"data": str(r.data), "total_vendas": float(r.total_vendas or 0)} for r in result]
    return jsonify(data)


# ===============================
# 6) Rodar o Flask
# ===============================
if __name__ == "__main__":
    app.run(debug=True)
