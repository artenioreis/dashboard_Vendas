# app.py
import urllib
from flask import Flask, jsonify, render_template, request
from sqlalchemy import create_engine, text
import logging
from datetime import date

# ===============================
# 1) Configuração Inicial
# ===============================
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# ===============================
# 2) Conexão com o Banco de Dados
# ===============================
try:
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
    connection = engine.connect()
    connection.close()
    print("Conexão com o banco de dados bem-sucedida.")
except Exception as e:
    print(f"Erro ao conectar ao banco de dados: {e}")
    exit()

# ===============================
# 3) Rotas das Páginas (HTML)
# ===============================
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/vendas')
def vendas():
    return render_template("vendas.html")

@app.route('/contas-a-receber')
def contas_a_receber():
    return render_template("contas_a_receber.html")

@app.route('/contas-a-pagar')
def contas_a_pagar():
    return render_template("contas_a_pagar.html")

# ===============================
# 4) Funções Auxiliares
# ===============================
def get_date_params():
    today = date.today()
    start_date_default = date(today.year, 1, 1).strftime('%Y-%m-%d')
    end_date_default = today.strftime('%Y-%m-%d')
    start_date = request.args.get('start_date', start_date_default)
    end_date = request.args.get('end_date', end_date_default)
    return start_date, end_date

# ===============================
# 5) API Endpoints para VENDAS
# ===============================
@app.route('/totais-mensais')
def totais_mensais():
    start_date, end_date = get_date_params()
    try:
        sql = text("""
            SELECT ano, mes, SUM(total_vendas) AS total_vendas, SUM(total_compras) AS total_compras
            FROM (
                SELECT YEAR(c.Dat_Emissao) AS ano, MONTH(c.Dat_Emissao) AS mes, SUM(i.Qtd_Produto * i.prc_unitario) AS total_vendas, 0 AS total_compras
                FROM NFSCB c JOIN NFSIT i ON c.Num_nota = i.Num_nota
                WHERE c.Tip_Saida IN ('V', 'O') AND CONVERT(date, c.Dat_Emissao) BETWEEN :start_date AND :end_date
                GROUP BY YEAR(c.Dat_Emissao), MONTH(c.Dat_Emissao)
                UNION ALL
                SELECT YEAR(N.Dat_Emissao) AS ano, MONTH(N.Dat_Emissao) AS mes, 0 AS total_vendas, SUM(N.Vlr_Nota) AS total_compras
                FROM NFECB N WHERE N.Status <> 'C' AND CONVERT(date, N.Dat_Emissao) BETWEEN :start_date AND :end_date
                GROUP BY YEAR(N.Dat_Emissao), MONTH(N.Dat_Emissao)
            ) AS totais_mensais GROUP BY ano, mes ORDER BY ano, mes;
        """)
        params = {"start_date": start_date, "end_date": end_date}
        with engine.connect() as conn:
            result = conn.execute(sql, params)
            data = [{"ano": int(r.ano), "mes": int(r.mes), "total_vendas": float(r.total_vendas or 0), "total_compras": float(r.total_compras or 0)} for r in result]
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Erro em /totais-mensais: {e}")
        return jsonify({"error": str(e)}), 500

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

@app.route('/cliente-top')
def cliente_top():
    start_date, end_date = get_date_params()
    try:
        sql = text("""
            SELECT TOP 10 cl.Razao_Social, SUM(i.Qtd_Produto * i.Prc_Unitario) as total_gasto
            FROM NFSCB c JOIN NFSIT i ON c.Num_Nota = i.Num_Nota JOIN clien cl ON c.Cod_Cliente = cl.Codigo
            WHERE c.Tip_Saida IN ('V', 'O') AND CONVERT(date, c.Dat_Emissao) BETWEEN :start_date AND :end_date
            GROUP BY cl.Razao_Social ORDER BY total_gasto DESC
        """)
        params = {"start_date": start_date, "end_date": end_date}
        with engine.connect() as conn:
            result = conn.execute(sql, params)
            data = [{"Razao_Social": r.Razao_Social, "total_gasto": float(r.total_gasto or 0)} for r in result]
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Erro em /cliente-top: {e}")
        return jsonify({"error": f"Erro no servidor: {e}"}), 500

@app.route('/produtos-top')
def produtos_top():
    start_date, end_date = get_date_params()
    try:
        sql = text("""
            SELECT TOP 10 P.Descricao, SUM(S.Qtd_Produto) as total_vendido
            FROM NFSIT AS S INNER JOIN PRODU AS P ON S.Cod_Produto = P.Codigo INNER JOIN NFSCB AS C ON S.Num_Nota = C.Num_Nota
            WHERE CONVERT(date, C.Dat_Emissao) BETWEEN :start_date AND :end_date AND C.Tip_Saida IN ('V', 'O')
            GROUP BY P.Descricao ORDER BY total_vendido DESC
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
# 6) API Endpoints para CONTAS A RECEBER
# ===============================
def get_base_contas_a_receber_query(search_term=""):
    base_sql = "FROM CTREC c JOIN CLIEN cl ON c.Cod_Cliente = cl.Codigo WHERE (c.Status IN ('A', 'P')) AND c.Vlr_Saldo > 0.01"
    if search_term:
        base_sql += " AND cl.Razao_Social LIKE :search_term"
    return base_sql

@app.route('/api/contas-a-receber/kpis')
def contas_a_receber_kpis():
    search_term = request.args.get('search', '')
    params = {'search_term': f'%{search_term}%'} if search_term else {}
    base_query = get_base_contas_a_receber_query(search_term)
    try:
        with engine.connect() as conn:
            sql_kpis = text(f"SELECT SUM(c.Vlr_Saldo) as total, COUNT(*) as count {base_query}")
            kpis_res = conn.execute(sql_kpis, params).fetchone()
            sql_atraso = text(f"""
                SELECT TOP 1 
                    cl.Razao_Social, 
                    DATEDIFF(day, DATEADD(day, ISNULL(c.Qtd_DiaExtVct, 0), c.Dat_Vencimento), GETDATE()) as atraso 
                {base_query} 
                AND c.Dat_Vencimento IS NOT NULL 
                AND GETDATE() > DATEADD(day, ISNULL(c.Qtd_DiaExtVct, 0), c.Dat_Vencimento)
                ORDER BY atraso DESC
            """)
            atraso_res = conn.execute(sql_atraso, params).fetchone()
            dias_atraso = 0
            cliente_atrasado = "N/A"
            if atraso_res:
                dias_atraso = int(atraso_res.atraso or 0)
                cliente_atrasado = atraso_res.Razao_Social
            data = {
                "total_a_receber": float(kpis_res.total or 0),
                "titulos_abertos": int(kpis_res.count or 0),
                "max_dias_atraso": dias_atraso,
                "cliente_mais_atrasado": cliente_atrasado
            }
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Erro em /api/contas-a-receber/kpis: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/contas-a-receber/top-devedores')
def contas_a_receber_top_devedores():
    search_term = request.args.get('search', '')
    params = {'search_term': f'%{search_term}%'} if search_term else {}
    base_query = get_base_contas_a_receber_query(search_term)
    try:
        sql = text(f"SELECT TOP 5 cl.Razao_Social, SUM(c.Vlr_Saldo) as total_saldo {base_query} GROUP BY cl.Razao_Social ORDER BY total_saldo DESC")
        with engine.connect() as conn:
            result = conn.execute(sql, params)
            data = [{"cliente": r.Razao_Social, "saldo": float(r.total_saldo)} for r in result]
        return jsonify(data)
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/contas-a-receber/divida-por-faixa')
def contas_a_receber_divida_por_faixa():
    search_term = request.args.get('search', '')
    params = {'search_term': f'%{search_term}%'} if search_term else {}
    base_query = get_base_contas_a_receber_query(search_term)
    try:
        sql = text(f"""
            SELECT 
                CASE
                    WHEN DATEDIFF(day, DATEADD(day, ISNULL(c.Qtd_DiaExtVct, 0), c.Dat_Vencimento), GETDATE()) < 0 THEN 'A Vencer'
                    WHEN DATEDIFF(day, DATEADD(day, ISNULL(c.Qtd_DiaExtVct, 0), c.Dat_Vencimento), GETDATE()) BETWEEN 0 AND 30 THEN 'Vencido 1-30 dias'
                    WHEN DATEDIFF(day, DATEADD(day, ISNULL(c.Qtd_DiaExtVct, 0), c.Dat_Vencimento), GETDATE()) BETWEEN 31 AND 60 THEN 'Vencido 31-60 dias'
                    WHEN DATEDIFF(day, DATEADD(day, ISNULL(c.Qtd_DiaExtVct, 0), c.Dat_Vencimento), GETDATE()) BETWEEN 61 AND 90 THEN 'Vencido 61-90 dias'
                    ELSE 'Vencido > 90 dias' 
                END as faixa, 
                SUM(c.Vlr_Saldo) as total_saldo 
            {base_query}
            GROUP BY 
                CASE
                    WHEN DATEDIFF(day, DATEADD(day, ISNULL(c.Qtd_DiaExtVct, 0), c.Dat_Vencimento), GETDATE()) < 0 THEN 'A Vencer'
                    WHEN DATEDIFF(day, DATEADD(day, ISNULL(c.Qtd_DiaExtVct, 0), c.Dat_Vencimento), GETDATE()) BETWEEN 0 AND 30 THEN 'Vencido 1-30 dias'
                    WHEN DATEDIFF(day, DATEADD(day, ISNULL(c.Qtd_DiaExtVct, 0), c.Dat_Vencimento), GETDATE()) BETWEEN 31 AND 60 THEN 'Vencido 31-60 dias'
                    WHEN DATEDIFF(day, DATEADD(day, ISNULL(c.Qtd_DiaExtVct, 0), c.Dat_Vencimento), GETDATE()) BETWEEN 61 AND 90 THEN 'Vencido 61-90 dias'
                    ELSE 'Vencido > 90 dias' 
                END
        """)
        with engine.connect() as conn:
            result = conn.execute(sql, params)
            data = [{"faixa": r.faixa, "saldo": float(r.total_saldo)} for r in result]
        return jsonify(data)
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/contas-a-receber/detalhes')
def contas_a_receber_detalhes():
    search_term = request.args.get('search', '')
    params = {'search_term': f'%{search_term}%'} if search_term else {}
    base_query = get_base_contas_a_receber_query(search_term)
    try:
        sql = text(f"""
            SELECT 
                cl.Razao_Social, 
                c.Dat_Vencimento, 
                c.Vlr_Saldo, 
                DATEDIFF(day, DATEADD(day, ISNULL(c.Qtd_DiaExtVct, 0), c.Dat_Vencimento), GETDATE()) as dias_atraso 
            {base_query} 
            ORDER BY dias_atraso DESC
        """)
        with engine.connect() as conn:
            result = conn.execute(sql, params)
            data = [{"cliente": r.Razao_Social, "vencimento": r.Dat_Vencimento.isoformat() if r.Dat_Vencimento else 'N/A', "saldo": float(r.Vlr_Saldo), "dias_atraso": r.dias_atraso if r.dias_atraso and r.dias_atraso > 0 else 0} for r in result]
        return jsonify(data)
    except Exception as e: 
        app.logger.error(f"Erro em /api/contas-a-receber/detalhes: {e}")
        return jsonify({"error": str(e)}), 500

# =========================================================
# 7) API Endpoints para CONTAS A PAGAR (COM CORREÇÃO FINAL)
# =========================================================
def get_base_contas_a_pagar_query_string(search_term=""):
    # Esta função agora retorna apenas a string da CTE e a condição de busca
    cte_part = """
        WITH ContasPagar AS (
            SELECT
                pg.Val_Saldo, pg.Dat_Vencim, DATEDIFF(day, pg.Dat_Vencim, GETDATE()) as dias_atraso,
                CASE
                    WHEN pg.Tip_Docume = 'F' THEN (SELECT Razao_Social FROM FORNE WHERE Codigo = pg.Cod_Fornec)
                    ELSE (SELECT Des_Favore FROM FAVOR WHERE Cod_Favore = pg.Cod_Favore)
                END as credor
            FROM PAGCT pg
            WHERE pg.Val_Saldo > 0.01 AND pg.Sta_Docume NOT IN ('Q', 'C')
        )
    """
    where_part = "WHERE credor LIKE :search_term" if search_term else ""
    return cte_part, where_part

@app.route('/api/contas-a-pagar/kpis')
def contas_a_pagar_kpis():
    search_term = request.args.get('search', '')
    params = {'search_term': f'%{search_term}%'} if search_term else {}
    cte_part, where_part = get_base_contas_a_pagar_query_string(search_term)
    try:
        with engine.connect() as conn:
            sql_kpis = text(f"{cte_part} SELECT SUM(Val_Saldo) as total, COUNT(*) as count FROM ContasPagar {where_part}")
            kpis_res = conn.execute(sql_kpis, params).fetchone()

            sql_credor = text(f"{cte_part} SELECT TOP 1 credor, SUM(Val_Saldo) as total_saldo FROM ContasPagar {where_part} GROUP BY credor ORDER BY total_saldo DESC")
            credor_res = conn.execute(sql_credor, params).fetchone()
            
            data = {
                "total_a_pagar": float(kpis_res.total or 0), "titulos_abertos": int(kpis_res.count or 0),
                "principal_credor": credor_res.credor if credor_res else "N/A",
                "principal_credor_valor": float(credor_res.total_saldo or 0) if credor_res else 0
            }
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Erro em /api/contas-a-pagar/kpis: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/contas-a-pagar/top-credores')
def contas_a_pagar_top_credores():
    search_term = request.args.get('search', '')
    params = {'search_term': f'%{search_term}%'} if search_term else {}
    cte_part, where_part = get_base_contas_a_pagar_query_string(search_term)
    try:
        sql = text(f"{cte_part} SELECT TOP 5 credor, SUM(Val_Saldo) as total_saldo FROM ContasPagar {where_part} GROUP BY credor ORDER BY total_saldo DESC")
        with engine.connect() as conn:
            result = conn.execute(sql, params)
            data = [{"credor": r.credor, "saldo": float(r.total_saldo)} for r in result]
        return jsonify(data)
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/contas-a-pagar/divida-por-faixa')
def contas_a_pagar_divida_por_faixa():
    search_term = request.args.get('search', '')
    params = {'search_term': f'%{search_term}%'} if search_term else {}
    cte_part, where_part = get_base_contas_a_pagar_query_string(search_term)
    try:
        sql = text(f"""
            {cte_part}
            SELECT faixa, SUM(Val_Saldo) as total_saldo
            FROM (
                SELECT Val_Saldo,
                    CASE
                        WHEN dias_atraso < 0 THEN 'A Vencer'
                        WHEN dias_atraso BETWEEN 0 AND 30 THEN 'Vencido 1-30 dias'
                        WHEN dias_atraso BETWEEN 31 AND 60 THEN 'Vencido 31-60 dias'
                        ELSE 'Vencido > 60 dias'
                    END as faixa
                FROM ContasPagar
                {where_part}
            ) as sub2
            GROUP BY faixa
        """)
        with engine.connect() as conn:
            result = conn.execute(sql, params)
            data = [{"faixa": r.faixa, "saldo": float(r.total_saldo)} for r in result]
        return jsonify(data)
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/contas-a-pagar/detalhes')
def contas_a_pagar_detalhes():
    search_term = request.args.get('search', '')
    params = {'search_term': f'%{search_term}%'} if search_term else {}
    cte_part, where_part = get_base_contas_a_pagar_query_string(search_term)
    try:
        sql = text(f"{cte_part} SELECT TOP 100 * FROM ContasPagar {where_part} ORDER BY dias_atraso DESC")
        with engine.connect() as conn:
            result = conn.execute(sql, params)
            data = [{"credor": r.credor, "vencimento": r.Dat_Vencim.isoformat() if r.Dat_Vencim else 'N/A', "saldo": float(r.Val_Saldo), "dias_atraso": r.dias_atraso if r.dias_atraso > 0 else 0} for r in result]
        return jsonify(data)
    except Exception as e: return jsonify({"error": str(e)}), 500

# ===============================
# 8) Rodar a Aplicação
# ===============================
if __name__ == "__main__":
    app.run(debug=True)