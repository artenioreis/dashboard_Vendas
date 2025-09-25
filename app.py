# app.py
import os
from flask import Flask, render_template, request
import pandas as pd
from sqlalchemy import create_engine, text
import urllib

app = Flask(__name__)

# === Conexão com SQL Server usando seu conn_str ===
conn_str = (
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=localhost;'
    'DATABASE=DMD;'
    'UID=sa;'
    'PWD=arte171721;'
    'Encrypt=yes;'
    'TrustServerCertificate=yes;'
)

# A string precisa ser codificada para uso no SQLAlchemy
#params = urllib.parse.quote_plus(conn_str)
#engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}", fast_executemany=True)

# === Funções para buscar dados ===
def get_top_products(start_date, end_date, top_n=10):
    sql = text("""
    SELECT p.Codigo AS produto_id, p.Descricao AS produto,
           SUM(i.Qtd_Produto) AS qtd_vendida,
           SUM(i.Qtd_Produto * i.Prc_Unitario) AS receita
    FROM NFSIT i
    JOIN PRODU p ON i.Cod_Produto = p.Codigo
    JOIN NFSCB c ON i.Num_Nota = c.Num_Nota
    WHERE c.Dat_Emissao BETWEEN :start_date AND :end_date
    GROUP BY p.Codigo, p.Descricao
    ORDER BY qtd_vendida DESC
    """)
    df = pd.read_sql(sql, engine, params={"start_date": start_date, "end_date": end_date})
    return df.head(top_n)

def get_top_customer(start_date, end_date):
    sql = text("""
    SELECT c.Cod_Cliente, cl.Nome, SUM(i.Qtd_Produto * i.Prc_Unitario) AS total_gasto
    FROM NFSIT i
    JOIN NFSCB c ON i.Num_Nota = c.Num_Nota
    JOIN CLIENTES cl ON c.Cod_Cliente = cl.Cod_Cliente
    WHERE c.Dat_Emissao BETWEEN :start_date AND :end_date
    GROUP BY c.Cod_Cliente, cl.Nome
    ORDER BY total_gasto DESC
    """)
    df = pd.read_sql(sql, engine, params={"start_date": start_date, "end_date": end_date})
    return df.iloc[0] if not df.empty else None

def get_monthly_totals(start_date, end_date):
    sql = text("""
    SELECT YEAR(c.Dat_Emissa_
