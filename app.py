import pandas as pd
import streamlit as st

from auth import botao_sair, exigir_login
from brand import URL_CALCULOS
from data import (load_from_gsheets, load_from_public_link, load_from_xlsx, prep_execucao, prep_prazos,
                  prep_registro, quality_report)

st.set_page_config(page_title="Núcleo Bancário | Dutra Bitencourt", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
header[data-testid="stHeader"] {background:#00315F; border-bottom:3px solid #C9A227;}
header[data-testid="stHeader"] a, header[data-testid="stHeader"] span,
header[data-testid="stHeader"] p, header[data-testid="stHeader"] button {color:#E8EEF6 !important;}
[data-testid="stAppDeployButton"], [data-testid="stMainMenu"] {display:none;}
.block-container {padding-top:4.5rem;}
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

from views import dash, manual  # noqa: E402

PAINEL = [
    st.Page(dash.visao_geral, title="Visão geral", icon=":material/insights:", default=True),
    st.Page(dash.processos, title="Processos e sentenças", icon=":material/gavel:"),
    st.Page(dash.prazos, title="Prazos", icon=":material/event_available:"),
    st.Page(dash.execucao, title="Execução e alvarás", icon=":material/payments:"),
    st.Page(dash.clientes, title="Clientes", icon=":material/groups:"),
    st.Page(dash.ficha, title="Ficha do processo", icon=":material/description:"),
    st.Page(dash.qualidade, title="Qualidade dos dados", icon=":material/rule:"),
]
MANUAL = [
    st.Page(manual.script, title="Script de vendas", icon=":material/call:"),
    st.Page(manual.procedimento, title="Procedimento interno", icon=":material/menu_book:"),
]
pagina = st.navigation({"Painel": PAINEL, "Manual": MANUAL}, position="top")
no_painel = pagina.title in {p.title for p in PAINEL}


# ------------------------------------------------------------------ barra de ações
FILTROS = ("f_per", "f_rit", "f_dem", "f_ban", "f_tri", "f_sem")


def _preparar(chave, opcoes=None):
    """Recria o widget com o último valor salvo, só quando ele não existe.

    O Streamlit apaga o estado do widget quando a página não o desenha (ex.: Manual).
    O valor salvo em `chave` sobrevive e é devolvido ao widget `_chave`.
    Nunca sobrescreve `_chave` se ele já existe: isso desfaria a seleção recém-feita.
    """
    w = "_" + chave
    if w not in st.session_state:
        valor = st.session_state[chave]
        if opcoes is not None:
            valor = [v for v in valor if v in opcoes]
        st.session_state[w] = valor


def _salvar(chave):
    st.session_state[chave] = st.session_state["_" + chave]


def _limpar():
    for k in FILTROS:
        st.session_state.pop(k, None)
        st.session_state.pop("_" + k, None)


barra = st.columns([6, 2, 2, 1.4, 1], vertical_alignment="center")
with barra[2]:
    st.link_button("Sistema de cálculos", URL_CALCULOS, icon=":material/calculate:", width="stretch")
with barra[3]:
    if st.button("Atualizar", icon=":material/refresh:", width="stretch"):
        st.cache_data.clear()
with barra[4]:
    botao_sair()


# ------------------------------------------------------------------ dados
def _carrega():
    if _secret("gcp_service_account"):
        return load_from_gsheets()
    sheet = _secret("sheet") or {}
    if sheet.get("id"):
        return load_from_public_link(sheet["id"])
    # modo sem Secrets: o arquivo enviado fica guardado na sessão para sobreviver à troca de página
    if no_painel and "xlsx_bytes" not in st.session_state:
        up = st.file_uploader("Sem planilha configurada nos Secrets. Envie o .xlsx exportado da planilha.",
                              type="xlsx")
        if up is not None:
            st.session_state.xlsx_bytes = up.getvalue()
            st.rerun()
    if "xlsx_bytes" in st.session_state:
        import io
        return load_from_xlsx(io.BytesIO(st.session_state.xlsx_bytes))
    return None


try:
    raw = _carrega()
except Exception as e:  # noqa: BLE001
    raw = None
    st.error(f"Falha ao ler a planilha: {e}")

hoje = pd.Timestamp.today().normalize()
if raw:
    reg_all = prep_registro(raw["registro"], hoje)
    prz_all = prep_prazos(raw["prazos"])
    exe_all = prep_execucao(raw["execucao"])

    dmin, dmax = reg_all["Distribuição"].min(), reg_all["Distribuição"].max()
    periodo_padrao = (dmin.date(), dmax.date()) if pd.notna(dmin) else None
    for k, v in (("f_per", periodo_padrao), ("f_dem", []), ("f_ban", []), ("f_tri", []), ("f_rit", []), ("f_sem", True)):
        st.session_state.setdefault(k, v)

    if no_painel:
        with barra[1]:
            ativos = sum(bool(st.session_state[k]) for k in ("f_rit", "f_dem", "f_ban", "f_tri"))
            with st.popover(f"Filtros{f' ({ativos})' if ativos else ''}", icon=":material/filter_list:",
                            width="stretch"):
                if periodo_padrao:
                    p = st.session_state.f_per
                    if not p or any(d < dmin.date() or d > dmax.date() for d in p):
                        st.session_state.f_per = periodo_padrao  # dados mudaram: volta ao período cheio
                        st.session_state.pop("_f_per", None)
                    _preparar("f_per")
                    st.date_input("Distribuídos entre", key="_f_per", min_value=dmin.date(),
                                  max_value=dmax.date(), format="DD/MM/YYYY",
                                  on_change=_salvar, args=("f_per",))
                for k, rot, col in (("f_rit", "Rito", "Rito (grupo)"), ("f_dem", "Tipo de ação", "Demanda"),
                                    ("f_ban", "Banco", "Banco"), ("f_tri", "Tribunal", "Tribunal")):
                    opcoes = sorted(reg_all[col].dropna().unique())
                    _preparar(k, opcoes)
                    st.multiselect(rot, opcoes, key="_" + k, placeholder="Todos",
                                   on_change=_salvar, args=(k,))
                _preparar("f_sem")
                st.toggle("Incluir não distribuídos", key="_f_sem", on_change=_salvar, args=("f_sem",))
                st.button("Limpar filtros", width="stretch", on_click=_limpar)

    periodo, demandas = st.session_state.f_per, st.session_state.f_dem
    bancos, tribunais, incluir_sem_dist = st.session_state.f_ban, st.session_state.f_tri, st.session_state.f_sem
    ritos = st.session_state.f_rit

    reg = reg_all.copy()
    if periodo and len(periodo) == 2:
        ini, fim = pd.Timestamp(periodo[0]), pd.Timestamp(periodo[1])
        dentro = reg["Distribuição"].between(ini, fim)
        reg = reg[dentro | (reg["Distribuição"].isna() & incluir_sem_dist)]
    elif not incluir_sem_dist:
        reg = reg[reg["Distribuição"].notna()]
    if ritos:
        reg = reg[reg["Rito (grupo)"].isin(ritos)]
    if demandas:
        reg = reg[reg["Demanda"].isin(demandas)]
    if bancos:
        reg = reg[reg["Banco"].isin(bancos)]
    if tribunais:
        reg = reg[reg["Tribunal"].isin(tribunais)]

    st.session_state.update(
        reg=reg, reg_all=reg_all, prz=prz_all, exe=exe_all, hoje=hoje,
        avisos=quality_report(reg_all, prz_all, exe_all),
        filtrado=len(reg) != len(reg_all),
    )
    st.session_state.pop("sem_dados", None)
else:
    st.session_state.sem_dados = True

pagina.run()
