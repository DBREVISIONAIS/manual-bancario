import streamlit as st

from brand import URL_CALCULOS
from manual_content import PROCEDIMENTO, SCRIPT, TESE


def _render(titulo, secoes):
    topo = st.columns([4, 1.4], vertical_alignment="bottom")
    with topo[0]:
        st.title(titulo)
        st.caption(TESE)
    with topo[1]:
        st.link_button("Abrir sistema de cálculos", URL_CALCULOS, type="primary",
                       icon=":material/calculate:", width="stretch")
    busca = st.text_input("Buscar no manual", placeholder="Ex.: Portocred, RMC, LGPD, honorários")
    if busca:
        achados = [(t, md) for t, md in secoes if busca.lower() in md.lower() or busca.lower() in t.lower()]
        if not achados:
            st.info(f"Nenhuma seção menciona “{busca}”.")
        for t, md in achados:
            with st.expander(t, expanded=True):
                st.markdown(md)
        return
    abas = st.tabs([t for t, _ in secoes])
    for aba, (_, md) in zip(abas, secoes):
        with aba:
            st.markdown(md)


def script():
    _render("Script de vendas – ações revisionais", SCRIPT)


def procedimento():
    _render("Manual de procedimento interno", PROCEDIMENTO)
