import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import base64

# Configuração da página
st.set_page_config(page_title="Bigodario Dashboard", layout="wide")

# LOGIN SIMPLES
usuarios = {
    "admin": "Flamengo",
    "marcos": "Bigodario"
}
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = ""

if not st.session_state.autenticado:
    st.title("🔐 Login - Dashboard Barbearia")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if usuario in usuarios and senha == usuarios[usuario]:
            st.session_state.autenticado = True
            st.session_state.usuario = usuario
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
    st.stop()

# Abrir e converter a imagem em base64
def mostrar_logo(path, largura=200):
    with open(path, "rb") as img_file:
        img_bytes = img_file.read()
        encoded = base64.b64encode(img_bytes).decode()
        img_html = f"""
        <div style="text-align: center;">
            <img src="data:image/png;base64,{encoded}" width="{largura}">
        </div>
        """
        return img_html

# Exibir o logo e nome centralizados
st.markdown(mostrar_logo("image.png"), unsafe_allow_html=True)
st.markdown("""
    <h1 style='text-align: center; color: white; margin-bottom: 0;'>Bigodario Barbearia</h1>
    <p style='text-align: center; color: #aaa; font-size: 18px; margin-top: 0;'>Estilo, tradição e dados na lâmina</p>
    <hr style='border:1px solid #555;'>
""", unsafe_allow_html=True)

# MENU LATERAL
pagina = st.sidebar.selectbox(
    "📁 Selecione uma página:",
    ["Visão Geral", "Relatórios Mensais", "Histórico de Clientes"]
)

# CARREGAR DADOS
df = pd.read_csv("Agendamentos_Barbearia_Final.csv", parse_dates=["Data"])
df["Hora"] = pd.to_datetime(df["Horário"], format="%H:%M", errors="coerce").dt.hour
df["Mês"] = df["Data"].dt.to_period("M").astype(str)
dias_semana_pt = {
    "Monday": "Segunda", "Tuesday": "Terça", "Wednesday": "Quarta",
    "Thursday": "Quinta", "Friday": "Sexta", "Saturday": "Sábado", "Sunday": "Domingo"
}
df["Dia da Semana"] = df["Data"].dt.day_name().replace(dias_semana_pt)
ordem_dias = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
df["Dia da Semana"] = pd.Categorical(df["Dia da Semana"], categories=ordem_dias, ordered=True)

# VISÃO GERAL
if pagina == "Visão Geral":
    data_inicial, data_final = st.date_input("Filtrar por período:", [df["Data"].min(), df["Data"].max()])
    df_filtrado = df[(df["Data"] >= pd.to_datetime(data_inicial)) & (df["Data"] <= pd.to_datetime(data_final))]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🧍 Clientes", df_filtrado["Cliente"].nunique())
    col2.metric("💰 Faturamento Bruto", f"R$ {df_filtrado['Valor (R$)'].sum():,.2f}")
    col3.metric("🧾 Agendamentos", len(df_filtrado))
    ticket_medio = df_filtrado["Valor (R$)"].mean()
    col4.metric("🎟️ Ticket Médio", f"R$ {ticket_medio:.2f}" if not pd.isna(ticket_medio) else "N/A")

    st.markdown("---")

    # Gráficos
    st.subheader("📅 Faturamento por Dia")
    fig_dia = px.bar(df_filtrado.groupby("Data")["Valor (R$)"].sum().reset_index(),
                     x="Data", y="Valor (R$)", title="Faturamento Diário")
    st.plotly_chart(fig_dia, use_container_width=True)

    st.subheader("📆 Faturamento Mensal")
    fig_mes = px.line(df_filtrado.groupby("Mês")["Valor (R$)"].sum().reset_index(),
                      x="Mês", y="Valor (R$)", markers=True, title="Faturamento por Mês")
    st.plotly_chart(fig_mes, use_container_width=True)

    st.subheader("💇 Por Produto")
    fig_produto = px.bar(df_filtrado.groupby("Produto")["Valor (R$)"].sum().reset_index().sort_values("Valor (R$)", ascending=False),
                         x="Produto", y="Valor (R$)", title="Faturamento por Tipo de Serviço")
    st.plotly_chart(fig_produto, use_container_width=True)

    st.subheader("⏰ Faturamento por Hora (Geral)")
    fig_hora = px.bar(df_filtrado.groupby("Hora")["Valor (R$)"].sum().reset_index(),
                      x="Hora", y="Valor (R$)", title="Faturamento por Hora - Geral")
    st.plotly_chart(fig_hora, use_container_width=True)

    st.subheader("📅 Faturamento por Hora do Dia da Semana")
    dia_escolhido = st.selectbox("Escolha um dia da semana:", ordem_dias)
    df_hora_dia = df_filtrado[df_filtrado["Dia da Semana"] == dia_escolhido]
    fig_hora_dia = px.bar(df_hora_dia.groupby("Hora")["Valor (R$)"].sum().reset_index(),
                          x="Hora", y="Valor (R$)", title=f"Faturamento por Hora - {dia_escolhido}")
    st.plotly_chart(fig_hora_dia, use_container_width=True)

# RELATÓRIOS MENSAIS
elif pagina == "Relatórios Mensais":
    st.subheader("📆 Relatório Consolidado por Mês")
    df_mensal = df.groupby("Mês").agg({
        "Valor (R$)": "sum",
        "Cliente": "nunique",
        "Produto": "count"
    }).rename(columns={"Valor (R$)": "Faturamento", "Cliente": "Clientes Únicos", "Produto": "Atendimentos"}).reset_index()

    st.dataframe(df_mensal)

    st.subheader("📈 Evolução Mensal")
    fig = px.line(df_mensal, x="Mês", y="Faturamento", markers=True)
    st.plotly_chart(fig, use_container_width=True)

# HISTÓRICO DE CLIENTES
elif pagina == "Histórico de Clientes":
    st.subheader("🧍 Histórico de Clientes")
    cliente_selecionado = st.selectbox("Escolha um cliente:", df["Cliente"].dropna().unique())
    historico = df[df["Cliente"] == cliente_selecionado].sort_values("Data", ascending=False)
    st.dataframe(historico)
