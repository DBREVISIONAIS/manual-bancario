import pandas as pd
import streamlit as st

from auth import botao_sair, exigir_login
from data import (load_from_gsheets, load_from_xlsx, prep_execucao, prep_prazos,
                  prep_registro, quality_report)

st.set_page_config(page_title="Núcleo Bancário | Dutra Bitencourt", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
header[data-testid="stHeader"] {background:transparent;}
[data-testid="stSidebar"] {background:#00315F;}
[data-testid="stSidebar"] * {color:#E8EEF6 !important;}
[data-testid="stSidebar"] [data-baseweb="select"] * , [data-testid="stSidebar"] input {color:#1B2A3D !important;}
[data-testid="stSidebar"] .stButton button {background:transparent; border:1px solid #7FA7D1;}
[data-testid="stSidebar"] .stButton button:hover {border-color:#C9A227;}
[data-testid="stSidebar"] [data-testid="stFileUploader"] section * {color:#1B2A3D !important;}
[data-testid="stMetricValue"] {font-variant-numeric: tabular-nums; color:#00315F;}
blockquote {border-left:3px solid #2F7CC1; background:#F3F7FB; padding:.6rem 1rem; font-style:italic;}
h1, h2, h3, h4 {color:#00315F;}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ acesso
exigir_login()


def _secret(chave):
    try:
        return st.secrets.get(chave)
    except Exception:  # noqa: BLE001  (sem secrets.toml)
        return None


st.logo("assets/logo.png", size="large")

# ------------------------------------------------------------------ dados
def _carrega():
    if _secret("gcp_service_account"):
        return load_from_gsheets()
    st.sidebar.caption("Sem conexão configurada com o Google Sheets. Envie o .xlsx exportado da planilha.")
    up = st.sidebar.file_uploader("Planilha (.xlsx)", type="xlsx")
    if up is None:
        return None
    return load_from_xlsx(up)


with st.sidebar:
    botao_sair()
    if st.button("Atualizar dados"):
        st.cache_data.clear()

try:
    raw = _carrega()
except Exception as e:  # noqa: BLE001
    raw = None
    st.sidebar.error(f"Falha ao ler a planilha: {e}")

hoje = pd.Timestamp.today().normalize()
if raw:
    reg_all = prep_registro(raw["registro"], hoje)
    prz_all = prep_prazos(raw["prazos"])
    exe_all = prep_execucao(raw["execucao"])

    with st.sidebar:
        st.markdown("#### Filtros dos processos")
        dmin, dmax = reg_all["Distribuição"].min(), reg_all["Distribuição"].max()
        if pd.notna(dmin):
            periodo = st.date_input("Distribuídos entre", (dmin.date(), dmax.date()),
                                    min_value=dmin.date(), max_value=dmax.date(), format="DD/MM/YYYY")
        else:
            periodo = None
        demandas = st.multiselect("Tipo de ação", sorted(reg_all["Demanda"].dropna().unique()))
        bancos = st.multiselect("Banco", sorted(reg_all["Banco - Réu"].dropna().unique()))
        tribunais = st.multiselect("Tribunal", sorted(reg_all["Tribunal"].dropna().unique()))
        incluir_sem_dist = st.toggle("Incluir não distribuídos", value=True)

    reg = reg_all.copy()
    if periodo and len(periodo) == 2:
        ini, fim = pd.Timestamp(periodo[0]), pd.Timestamp(periodo[1])
        dentro = reg["Distribuição"].between(ini, fim)
        reg = reg[dentro | (reg["Distribuição"].isna() & incluir_sem_dist)]
    elif not incluir_sem_dist:
        reg = reg[reg["Distribuição"].notna()]
    if demandas:
        reg = reg[reg["Demanda"].isin(demandas)]
    if bancos:
        reg = reg[reg["Banco - Réu"].isin(bancos)]
    if tribunais:
        reg = reg[reg["Tribunal"].isin(tribunais)]

    st.session_state.update(
        reg=reg, reg_all=reg_all, prz=prz_all, exe=exe_all, hoje=hoje,
        avisos=quality_report(reg_all, prz_all, exe_all),
        filtrado=bool(demandas or bancos or tribunais) or len(reg) != len(reg_all),
    )
    st.session_state.pop("sem_dados", None)
else:
    st.session_state.sem_dados = True


# ------------------------------------------------------------------ navegação
from views import dash, manual  # noqa: E402

paginas = {
    "Painel": [
        st.Page(dash.visao_geral, title="Visão geral", icon=":material/insights:", default=True),
        st.Page(dash.processos, title="Processos e sentenças", icon=":material/gavel:"),
        st.Page(dash.prazos, title="Prazos", icon=":material/event_available:"),
        st.Page(dash.execucao, title="Execução e alvarás", icon=":material/payments:"),
        st.Page(dash.clientes, title="Clientes", icon=":material/groups:"),
        st.Page(dash.ficha, title="Ficha do processo", icon=":material/description:"),
        st.Page(dash.qualidade, title="Qualidade dos dados", icon=":material/rule:"),
    ],
    "Manual": [
        st.Page(manual.script, title="Script de vendas", icon=":material/call:"),
        st.Page(manual.procedimento, title="Procedimento interno", icon=":material/menu_book:"),
    ],
}
st.navigation(paginas).run()
