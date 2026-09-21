import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit as st

from data import EXEC_DATAS, FASES_FIN, fase_financeira, financeiro_execucao

RITOS_JUD = ["Procedimento comum", "Juizado Especial (JEC)"]

# ------------------------------------------------------------------ estilo
CORES = ["#00315F", "#2F7CC1", "#7FA7D1", "#5B6B7F", "#C9A227", "#3E8E7E", "#B55A4A"]
COR_RES = {
    "Procedente": "#3E8E7E", "Parcialmente procedente": "#7FA7D1", "Improcedente": "#B55A4A",
    "Extinção sem mérito": "#5B6B7F", "Acordo": "#C9A227", "Sem sentença": "#D9E1EA",
}
pio.templates["dbadv"] = pio.templates["plotly_white"]
pio.templates["dbadv"].layout.colorway = CORES
pio.templates["dbadv"].layout.font = dict(family="Inter, Segoe UI, sans-serif", color="#1B2A3D")
pio.templates.default = "dbadv"


def brl(v, casas=2):
    if pd.isna(v):
        return "–"
    s = f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def brl_md(v, casas=2):
    """brl() para texto em markdown (caption, warning): '$' sozinho vira fórmula LaTeX."""
    return brl(v, casas).replace("$", r"\$")


def num(v, casas=0):
    if pd.isna(v):
        return "–"
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _txt(v, vazio="–"):
    return vazio if v is None or (not isinstance(v, str) and pd.isna(v)) or str(v).strip() == "" else str(v)


def _chart(fig, h=360):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=40, b=10), legend_title_text="")
    st.plotly_chart(fig, width="stretch")


def _dados():
    if st.session_state.get("sem_dados"):
        st.info("Conecte a planilha (secrets) ou envie o .xlsx pela barra lateral para ver o painel.")
        st.stop()
    s = st.session_state
    if s.get("filtrado"):
        st.caption(f"Filtro ativo: {len(s.reg)} de {len(s.reg_all)} processos.")
    return s.reg, s.prz, s.exe


def _tempo_por(df, grupo, col, minimo=1):
    t = (df.dropna(subset=[col]).groupby(grupo)[col]
         .agg(Processos="count", Mediana="median", Média="mean", Mínimo="min", Máximo="max")
         .reset_index())
    return t[t["Processos"] >= minimo].sort_values("Mediana")


def _tabela_resultados(reg, grupo):
    t = reg.groupby(grupo).agg(
        Processos=("Cliente", "size"),
        Sentenciados=("Tem sentença", "sum"),
        Procedentes=("Resultado", lambda s: s.isin(["Procedente", "Parcialmente procedente"]).sum()),
        Improcedentes=("Resultado", lambda s: (s == "Improcedente").sum()),
        Extinções=("Resultado", lambda s: (s == "Extinção sem mérito").sum()),
        Valor_médio=("Valor da causa", "mean"),
        Dias_até_sentença=("Distribuição → Sentença", "median"),
        Em_curso=("Dias em curso (calc.)", "median"),
    ).reset_index()
    merito = reg[reg["Resultado"].notna() & (reg["Resultado"] != "Extinção sem mérito")]
    t["Dias_até_mérito"] = t[grupo].map(merito.groupby(grupo)["Distribuição → Sentença"].median())
    t["% sentenciado"] = 100 * t["Sentenciados"] / t["Processos"]
    t["% êxito (entre sentenciados)"] = 100 * t["Procedentes"] / t["Sentenciados"].where(t["Sentenciados"] > 0)
    cols = [c for c in t.columns if c != "Dias_até_mérito"]
    cols.insert(cols.index("Dias_até_sentença") + 1, "Dias_até_mérito")
    return t[cols].sort_values("Processos", ascending=False)


_CFG_RES = {
    "Valor_médio": st.column_config.NumberColumn("Valor médio da causa", format="R$ %.2f"),
    "Dias_até_sentença": st.column_config.NumberColumn("Mediana até sentença (dias)", format="%.0f"),
    "Dias_até_mérito": st.column_config.NumberColumn("Mediana até sentença de mérito (dias)", format="%.0f",
                                                      help="Exclui extinções sem mérito, que encurtam a média."),
    "Em_curso": st.column_config.NumberColumn("Mediana em curso (dias)", format="%.0f"),
    "% sentenciado": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100),
    "% êxito (entre sentenciados)": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100),
}



# ------------------------------------------------------------------ financeiro (comum)
COR_FASE = {"Não distribuído": "#D9E1EA", "Aguardando sentença": "#7FA7D1", "Sentença favorável": "#2F7CC1",
            "Em execução": "#C9A227", "Alvará expedido": "#3E8E7E", "Improcedente / extinto": "#B55A4A"}
MOEDA = lambda rot=None: st.column_config.NumberColumn(rot, format="R$ %.2f")  # noqa: E731


def _premissas():
    s = st.session_state
    s.setdefault("pct_contr", 30.0)
    s.setdefault("fixo_contr", 500.0)
    return s.pct_contr / 100, s.fixo_contr


def _editar_premissas():
    s = st.session_state
    _premissas()
    for k in ("pct_contr", "fixo_contr"):
        if "_" + k not in s:
            s["_" + k] = s[k]
    with st.expander("Premissas do cálculo de honorários na execução"):
        c1, c2 = st.columns(2)
        c1.number_input("Contratuais (% sobre o êxito do cliente)", 0.0, 100.0, step=1.0, key="_pct_contr",
                        on_change=lambda: s.update(pct_contr=s._pct_contr))
        c2.number_input("Parcela fixa padrão (R$)", 0.0, step=100.0, key="_fixo_contr",
                        on_change=lambda: s.update(fixo_contr=s._fixo_contr))
        st.caption("Contratuais na execução = percentual sobre o êxito do cliente + parcela fixa. A parcela fixa vem "
                   "da coluna Honorários Parc. do processo no Registro; o padrão acima só é usado quando a coluna "
                   "não existe ou o cumprimento não está vinculado a um processo do Registro. "
                   "Êxito do cliente = REPETIÇÃO + MULTA 10%. Sucumbência = HONORARIOS + HON. 10%.")


def _base_fin(reg, exe):
    pct, fixo = _premissas()
    ex = financeiro_execucao(exe, pct, fixo, st.session_state.get("reg_all"))
    r = reg.assign(**{"Fase financeira": fase_financeira(reg, exe)})
    return r, ex

# ------------------------------------------------------------------ páginas
def visao_geral():
    reg, prz, exe = _dados()
    st.title("Visão geral do núcleo")

    distrib = reg["Distribuição"].notna()
    sentenciados = reg["Tem sentença"]
    c = st.columns(4)
    c[0].metric("Processos", num(len(reg)), f"{num(distrib.sum())} distribuídos", delta_color="off")
    c[1].metric("Clientes", num(reg["Cliente (base)"].nunique()),
                f"{num(len(reg) / max(reg['Cliente (base)'].nunique(), 1), 2)} ações por cliente", delta_color="off")
    c[2].metric("Valor da causa médio", brl(reg["Valor da causa"].mean()),
                f"mediana {brl(reg['Valor da causa'].median())}", delta_color="off")
    c[3].metric("Com sentença", num(sentenciados.sum()),
                f"{num(100 * sentenciados.mean(), 1)}% dos processos", delta_color="off")

    c = st.columns(4)
    c[0].metric("Soma dos valores da causa", brl(reg["Valor da causa"].sum(), 0))
    c[1].metric("Honorários contratuais estimados", brl(reg["Contratuais (total)"].sum(), 0))
    c[2].metric("Prazos cumpridos (total)", num(len(prz)))
    c[3].metric("Mediana distribuição → sentença", f"{num(reg['Distribuição → Sentença'].median())} dias")

    ritos = reg["Rito (grupo)"].value_counts()
    c = st.columns(max(len(ritos), 1))
    for col, (rito, n) in zip(c, ritos.items()):
        sub = reg[reg["Rito (grupo)"] == rito]
        col.metric(rito, num(n), f"{num(sub['Tem sentença'].sum())} com sentença", delta_color="off")

    esq, dir_ = st.columns(2)
    with esq:
        mes = reg.dropna(subset=["Distribuição"]).assign(
            Mês=lambda d: d["Distribuição"].dt.to_period("M").dt.to_timestamp())
        g = mes.groupby(["Mês", "Demanda"]).size().reset_index(name="Processos")
        _chart(px.bar(g, x="Mês", y="Processos", color="Demanda", title="Distribuições por mês"))
    with dir_:
        g = reg.assign(Resultado=reg["Resultado"].fillna("Sem sentença")).groupby("Resultado").size()
        fig = px.pie(g.reset_index(name="Processos"), names="Resultado", values="Processos", hole=.55,
                     title="Situação das sentenças", color="Resultado", color_discrete_map=COR_RES)
        _chart(fig)

    esq, dir_ = st.columns(2)
    with esq:
        g = reg.groupby("Banco").size().nlargest(12).sort_values().reset_index(name="Processos")
        _chart(px.bar(g, x="Processos", y="Banco", orientation="h", title="Bancos mais demandados"), 420)
    with dir_:
        g = reg.groupby(["Tribunal", "Rito (grupo)"]).size().reset_index(name="Processos")
        fig = px.bar(g, x="Processos", y="Tribunal", color="Rito (grupo)", orientation="h",
                     title="Processos por tribunal e rito", labels={"Rito (grupo)": "Rito"})
        fig.update_yaxes(categoryorder="total ascending")
        _chart(fig, 420)


def financeiro():
    reg, _, exe_all = _dados()
    st.title("Financeiro")
    _editar_premissas()
    r, ex_all = _base_fin(reg, exe_all)
    # execuções só dos processos que passaram pelos filtros (as sem vínculo com o Registro entram sem filtro)
    if st.session_state.get("filtrado"):
        ex = ex_all[ex_all["cnj_orig"].isin(r["cnj"])]
    else:
        ex = ex_all

    st.subheader("Carteira projetada")
    st.caption("Valores da aba Registro. É a projeção se cada ação for julgada procedente como pedida: "
               "valor da causa não é valor de condenação.")
    c = st.columns(3)
    c[0].metric("Valor da causa", brl(r["Valor da causa"].sum(), 0))
    c[1].metric("Causa sem danos morais", brl(r["Causa s/ danos"].sum(), 0))
    c[2].metric("Honorários previstos (total)", brl(r["Honorários previstos"].sum(), 0))
    c = st.columns(3)
    c[0].metric("Contratuais (percentual)", brl(r["Contratuais"].sum(), 0))
    c[1].metric("Contratuais (parcela fixa)", brl(r["Honorários Parc."].sum(), 0),
                f"{num((r['Honorários Parc.'] > 0).sum())} ações com parcela", delta_color="off")
    c[2].metric("Sucumbência prevista", brl(r["Sucumbenciais"].sum(), 0))

    fase = (r.groupby("Fase financeira").agg(
        Processos=("Cliente", "size"), Valor_causa=("Valor da causa", "sum"),
        Contratuais=("Contratuais (total)", "sum"), Sucumbência=("Sucumbenciais", "sum"),
        Total=("Honorários previstos", "sum")).reindex(FASES_FIN).dropna(how="all").reset_index())
    esq, dir_ = st.columns([3, 2])
    with esq:
        g = fase.melt(id_vars="Fase financeira", value_vars=["Contratuais", "Sucumbência"],
                      var_name="Tipo", value_name="R$")
        fig = px.bar(g, x="Fase financeira", y="R$", color="Tipo", title="Honorários previstos por fase",
                     color_discrete_sequence=["#00315F", "#C9A227"], labels={"Fase financeira": ""})
        _chart(fig, 380)
    with dir_:
        st.markdown("**Onde está o dinheiro previsto**")
        st.dataframe(fase, hide_index=True, width="stretch", column_config={
            "Valor_causa": MOEDA("Valor da causa"), "Contratuais": MOEDA(), "Sucumbência": MOEDA(),
            "Total": MOEDA("Honorários previstos")})
    risco = r.loc[r["Fase financeira"] == "Improcedente / extinto", "Honorários previstos"].sum()
    favor = r.loc[r["Fase financeira"] == "Sentença favorável", "Honorários previstos"].sum()
    st.caption(f"Já com sentença favorável e ainda sem execução: {brl_md(favor)}. "
               f"Perdidos ou em risco (improcedentes e extintos, sujeitos a recurso): {brl_md(risco)}.")

    esq, dir_ = st.columns(2)
    with esq:
        g = (r.groupby("Rito (grupo)")[["Contratuais (total)", "Sucumbenciais"]].sum()
             .rename(columns={"Contratuais (total)": "Contratuais"}).reset_index())
        _chart(px.bar(g.melt(id_vars="Rito (grupo)", var_name="Tipo", value_name="R$"), x="Rito (grupo)", y="R$",
                      color="Tipo", barmode="group", title="Honorários previstos por rito",
                      color_discrete_sequence=["#00315F", "#C9A227"], labels={"Rito (grupo)": ""}))
        suc_jec = r.loc[r["Rito (grupo)"] == "Juizado Especial (JEC)", "Sucumbenciais"].sum()
        if suc_jec > 0:
            st.warning(f"Há {brl_md(suc_jec)} de sucumbência prevista em processos do JEC. Em 1º grau do "
                       "Juizado não há condenação em honorários de sucumbência, salvo litigância de má-fé; "
                       "confira essas linhas.")
    with dir_:
        g = (r.groupby("Banco")["Honorários previstos"].sum().nlargest(10).sort_values().reset_index())
        _chart(px.bar(g, x="Honorários previstos", y="Banco", orientation="h",
                      title="Honorários previstos por banco (10 maiores)"))

    mes = r.dropna(subset=["Distribuição"]).assign(
        Mês=lambda d: d["Distribuição"].dt.to_period("M").dt.to_timestamp())
    g = (mes.groupby("Mês")[["Contratuais (total)", "Sucumbenciais"]].sum()
         .rename(columns={"Contratuais (total)": "Contratuais"}).reset_index())
    _chart(px.bar(g.melt(id_vars="Mês", var_name="Tipo", value_name="R$"), x="Mês", y="R$", color="Tipo",
                  title="Honorários previstos pela data de distribuição",
                  color_discrete_sequence=["#00315F", "#C9A227"]), 320)

    st.subheader("Execuções: o que vamos receber")
    if ex.empty:
        st.info("Nenhum cumprimento de sentença no recorte atual.")
        return
    receber = ex[~ex["Alvará expedido"]]
    recebido = ex[ex["Alvará expedido"]]
    c = st.columns(4)
    c[0].metric("Total executado", brl(ex["TOTAL"].sum()), f"{num(ex['TOTAL'].notna().sum())} cumprimentos com valor",
                delta_color="off")
    c[1].metric("Receita do escritório", brl(ex["Receita do escritório"].sum()),
                f"sucumbência {brl(ex['Sucumbência (execução)'].sum())}", delta_color="off")
    c[2].metric("Contratuais na execução", brl(ex["Contratuais (execução)"].sum()),
                f"sobre êxito de {brl(ex['Êxito do cliente'].sum())}", delta_color="off")
    c[3].metric("Repasse estimado aos clientes", brl(ex["Repasse ao cliente"].sum()))
    c = st.columns(4)
    c[0].metric("A receber (sem alvará)", brl(receber["Receita do escritório"].sum()))
    c[1].metric("Já com alvará expedido", brl(recebido["Receita do escritório"].sum()),
                f"alvarás: {brl(recebido['ALVARA'].sum())}", delta_color="off")
    c[2].metric("Sucumbência a receber", brl(receber["Sucumbência (execução)"].sum()))
    c[3].metric("Contratuais a receber", brl(receber["Contratuais (execução)"].sum()))

    esq, dir_ = st.columns(2)
    with esq:
        g = ex.groupby("Etapa atual")[["Sucumbência (execução)", "Contratuais (execução)"]].sum()
        g = g.reindex(["Não distribuído"] + EXEC_DATAS).dropna(how="all").reset_index()
        _chart(px.bar(g.melt(id_vars="Etapa atual", var_name="Tipo", value_name="R$"), x="Etapa atual", y="R$",
                      color="Tipo", title="Receita do escritório por etapa da execução",
                      color_discrete_sequence=["#C9A227", "#00315F"], labels={"Etapa atual": ""}))
    with dir_:
        alv = ex.dropna(subset=["EXP. ALVARÁ"]).assign(
            Mês=lambda d: d["EXP. ALVARÁ"].dt.to_period("M").dt.to_timestamp())
        if alv.empty:
            st.info("Ainda não há alvará expedido.")
        else:
            g = alv.groupby("Mês")["Receita do escritório"].sum().reset_index()
            _chart(px.bar(g, x="Mês", y="Receita do escritório", title="Receita com alvará expedido, por mês"))

    lim = ex[ex["Contratuais limitados ao êxito"]]
    if len(lim):
        st.warning(f"Em {len(lim)} cumprimento(s) o êxito do cliente é pequeno e {num(100 * _premissas()[0])}% + "
                   "a parcela fixa passaria do valor dele. O cálculo limitou os contratuais ao êxito, "
                   "com repasse zero: " + ", ".join(lim["CLIENTE"].astype(str)) + ". Confira como o contrato trata "
                   "esses casos.")
    vis = ["CLIENTE", "CUMPRIMENTO", "Etapa atual", "TOTAL", "Êxito do cliente", "Parcela fixa",
           "Sucumbência (execução)", "Contratuais (execução)", "Receita do escritório", "Repasse ao cliente", "ALVARA",
           "Origem da parcela fixa"]
    st.dataframe(ex[vis].sort_values("Receita do escritório", ascending=False), hide_index=True, width="stretch",
                 column_config={c: MOEDA() for c in vis[3:-1]})

    st.subheader("Previsto × execução")
    st.caption("Para os processos já em cumprimento: honorários previstos no Registro comparados com a "
               "receita calculada na execução.")
    cmp_ = r[["cnj", "Cliente", "Honorários previstos"]].merge(
        ex[["cnj_orig", "Receita do escritório", "Etapa atual"]], left_on="cnj", right_on="cnj_orig")
    if cmp_.empty:
        st.info("Nenhum processo do Registro com cumprimento vinculado pelo número CNJ.")
    else:
        cmp_["Diferença"] = cmp_["Receita do escritório"] - cmp_["Honorários previstos"]
        st.dataframe(cmp_.drop(columns=["cnj", "cnj_orig"]), hide_index=True, width="stretch",
                     column_config={c: MOEDA() for c in ["Honorários previstos", "Receita do escritório", "Diferença"]})


def processos():
    reg, prz, _ = _dados()
    st.title("Processos e sentenças")

    st.subheader("Por rito")
    st.caption("Procedimento comum, Juizado Especial (JEC) e Administrativo seguem lógicas diferentes de prazo, "
               "recurso e custo. Compare os indicadores sempre dentro do mesmo rito.")
    tr = _tabela_resultados(reg, "Rito (grupo)")
    st.dataframe(tr, hide_index=True, width="stretch",
                 column_config={"Rito (grupo)": "Rito", **_CFG_RES})
    esq, dir_ = st.columns(2)
    with esq:
        g = reg.assign(Resultado=reg["Resultado"].fillna("Sem sentença")).groupby(["Rito (grupo)", "Resultado"]).size()
        _chart(px.bar(g.reset_index(name="Processos"), x="Rito (grupo)", y="Processos", color="Resultado",
                      color_discrete_map=COR_RES, title="Resultado por rito", labels={"Rito (grupo)": ""}))
    with dir_:
        m = pd.crosstab(reg["Demanda"], reg["Rito (grupo)"])
        fig = px.imshow(m, text_auto=True, aspect="auto", color_continuous_scale=["#FFFFFF", "#00315F"],
                        title="Tipo de ação × rito (processos)", labels=dict(x="", y="", color="Processos"))
        fig.update_coloraxes(showscale=False)
        _chart(fig)
    jec = reg[reg["Rito (grupo)"] == "Juizado Especial (JEC)"]
    if len(jec):
        ext = (jec["Resultado"] == "Extinção sem mérito").sum()
        st.caption(f"No JEC, {ext} de {len(jec)} processos foram extintos sem mérito "
                   f"({num(100 * ext / len(jec), 1)}%). Os motivos estão na coluna Pedidos da planilha.")

    st.subheader("Qual tipo de ação tem mais sentença")
    rito_acao = st.segmented_control("Rito", ["Todos"] + [r for r in tr["Rito (grupo)"]], default="Todos",
                                     key="rito_acao")
    base = reg if rito_acao in (None, "Todos") else reg[reg["Rito (grupo)"] == rito_acao]
    t = _tabela_resultados(base, "Demanda").sort_values("Sentenciados", ascending=False)
    st.dataframe(t, hide_index=True, width="stretch", column_config=_CFG_RES)
    g = base.assign(Resultado=base["Resultado"].fillna("Sem sentença")).groupby(["Demanda", "Resultado"]).size()
    _chart(px.bar(g.reset_index(name="Processos"), x="Demanda", y="Processos", color="Resultado",
                  color_discrete_map=COR_RES, title="Resultado por tipo de ação"))

    st.subheader("Quais tribunais são mais rápidos")
    st.caption("Mediana de dias corridos entre distribuição e sentença, só com processos já sentenciados. "
               "Tribunais com poucos processos têm leitura frágil; use o mínimo abaixo para filtrar.")
    c1, c2 = st.columns([2, 1])
    with c1:
        rito_trib = st.segmented_control("Rito", ["Todos"] + [r for r in RITOS_JUD if r in set(reg["Rito (grupo)"])],
                                         default="Procedimento comum" if "Procedimento comum" in set(reg["Rito (grupo)"])
                                         else "Todos", key="rito_trib")
    with c2:
        minimo = st.slider("Mínimo de sentenças por tribunal", 1, 10, 2)
    base_t = reg if rito_trib in (None, "Todos") else reg[reg["Rito (grupo)"] == rito_trib]
    rap = _tempo_por(base_t, "Tribunal", "Distribuição → Sentença", minimo)
    if rap.empty:
        st.info("Nenhum tribunal atinge esse mínimo de sentenças.")
    else:
        fig = px.bar(rap, x="Mediana", y="Tribunal", orientation="h", text="Processos",
                     title="Dias até a sentença (mediana)", labels={"Mediana": "dias"})
        fig.update_traces(texttemplate="%{text} sent.", textposition="outside")
        fig.update_yaxes(categoryorder="total descending")
        _chart(fig, 80 + 38 * len(rap))
    abertos = base_t[base_t["Distribuição"].notna() & ~base_t["Tem sentença"]]
    if len(abertos):
        a = abertos.groupby("Tribunal")["Dias em curso (calc.)"].agg(["count", "median"]).reset_index()
        a.columns = ["Tribunal", "Aguardando sentença", "Mediana em curso (dias)"]
        st.caption("Processos ainda sem sentença, para não ler só quem já terminou:")
        st.dataframe(a.sort_values("Mediana em curso (dias)", ascending=False), hide_index=True,
                     width="stretch")

    st.subheader("Duração das etapas")
    etapas = ["Assinatura → Distribuição", "Distribuição → Sentença", "Sentença → Trânsito",
              "Distribuição → Trânsito"]
    resumo = pd.DataFrame({e: reg[e].describe()[["count", "mean", "50%", "min", "max"]] for e in etapas}).T
    resumo.columns = ["Processos", "Média", "Mediana", "Mínimo", "Máximo"]
    st.dataframe(resumo.style.format("{:.0f}"), width="stretch")
    por = st.radio("Comparar por", ["Rito (grupo)", "Demanda", "Banco", "Tribunal"], horizontal=True,
                   format_func=lambda c: "Rito" if c == "Rito (grupo)" else c)
    etapa = st.selectbox("Etapa", etapas, index=1)
    _chart(px.box(reg.dropna(subset=[etapa]), x=por, y=etapa, points="all",
                  title=f"{etapa} (dias) por {por.lower()}"))

    st.subheader("Pedidos acolhidos")
    ped = (reg["Pedidos"].dropna().str.split(",").explode().str.strip())
    ped = ped[ped != ""].value_counts().reset_index()
    ped.columns = ["Pedido", "Ocorrências"]
    _chart(px.bar(ped, x="Ocorrências", y="Pedido", orientation="h",
                  title="Frequência na coluna Pedidos").update_yaxes(categoryorder="total ascending"),
           80 + 30 * len(ped))

    st.subheader("Valor da causa")
    por_v = st.radio("Agrupar valor por", ["Demanda", "Banco", "Tribunal"], horizontal=True, key="pv")
    v = reg.groupby(por_v)["Valor da causa"].agg(["count", "mean", "median", "sum"]).reset_index()
    v.columns = [por_v, "Processos", "Média", "Mediana", "Soma"]
    st.dataframe(v.sort_values("Soma", ascending=False), hide_index=True, width="stretch",
                 column_config={c: st.column_config.NumberColumn(format="R$ %.2f") for c in ["Média", "Mediana", "Soma"]})


def prazos():
    reg, prz, _ = _dados()
    st.title("Prazos")
    st.caption("A antecedência é FATAL menos CONCLUSÃO, em dias corridos (é a coluna DIAS com o sinal invertido). "
               "Zero significa peça concluída no dia do fatal.")

    dmin, dmax = prz["CONCLUSÃO"].min(), prz["CONCLUSÃO"].max()
    if pd.notna(dmin):
        per = st.date_input("Concluídos entre", (dmin.date(), dmax.date()), format="DD/MM/YYYY")
        if len(per) == 2:
            prz = prz[prz["CONCLUSÃO"].between(pd.Timestamp(per[0]), pd.Timestamp(per[1]))]
    resp = sorted(prz["ELABADO"].dropna().unique())
    if len(resp) > 1:
        sel = st.multiselect("Responsável", resp)
        if sel:
            prz = prz[prz["ELABADO"].isin(sel)]

    ant = prz["Antecedência (dias)"]
    c = st.columns(5)
    c[0].metric("Prazos cumpridos", num(len(prz)))
    c[1].metric("Antecedência média", f"{num(ant.mean(), 1)} dias")
    c[2].metric("Antecedência mediana", f"{num(ant.median())} dias")
    c[3].metric("No dia do fatal", f"{num(100 * prz['No dia do fatal'].mean(), 1)}%")
    c[4].metric("Após o fatal", num(prz["Após o fatal"].sum()))

    proc_com_prazo = prz["cnj"].nunique()
    c = st.columns(3)
    c[0].metric("Processos com prazo lançado", num(proc_com_prazo))
    c[1].metric("Prazos por processo (média)", num(len(prz) / max(proc_com_prazo, 1), 2))
    c[2].metric("Prazos por cliente (média)", num(len(prz) / max(prz["Cliente (base)"].nunique(), 1), 2))

    esq, dir_ = st.columns(2)
    with esq:
        g = prz.groupby("Mês").size().reset_index(name="Prazos")
        _chart(px.bar(g, x="Mês", y="Prazos", title="Prazos cumpridos por mês"))
    with dir_:
        _chart(px.histogram(prz, x="Antecedência (dias)", nbins=30, title="Distribuição da antecedência"))

    esq, dir_ = st.columns(2)
    with esq:
        g = prz.groupby("Tipo de peça").agg(Prazos=("cnj", "size"), Antecedência=("Antecedência (dias)", "mean"))
        g = g.sort_values("Prazos").reset_index()
        _chart(px.bar(g, x="Prazos", y="Tipo de peça", orientation="h", hover_data=["Antecedência"],
                      title="Prazos por tipo de peça"), 520)
    with dir_:
        g = prz.groupby("SISTEMA").agg(Prazos=("cnj", "size"),
                                       Antecedência=("Antecedência (dias)", "median")).reset_index()
        _chart(px.bar(g.sort_values("Prazos"), x="Prazos", y="SISTEMA", orientation="h",
                      hover_data=["Antecedência"], title="Prazos por sistema"), 520)

    st.subheader("Processos com mais prazos")
    top = (prz.groupby(["cnj", "PROCESSO"]).agg(Cliente=("AUTOR / PEDIDO", "first"), Prazos=("DEMANDA", "size"),
                                                  Último=("CONCLUSÃO", "max")).reset_index()
           .sort_values("Prazos", ascending=False).drop(columns="cnj"))
    st.dataframe(top.head(30), hide_index=True, width="stretch",
                 column_config={"Último": st.column_config.DateColumn(format="DD/MM/YYYY")})

    with st.expander("Todos os lançamentos"):
        st.dataframe(prz[["AUTOR / PEDIDO", "PROCESSO", "SISTEMA", "DEMANDA", "Tipo de peça", "CONCLUSÃO",
                          "FATAL", "Antecedência (dias)", "ELABADO"]].sort_values("CONCLUSÃO", ascending=False),
                     hide_index=True, width="stretch",
                     column_config={"CONCLUSÃO": st.column_config.DateColumn(format="DD/MM/YYYY"),
                                    "FATAL": st.column_config.DateColumn(format="DD/MM/YYYY")})


def execucao():
    _, _, exe = _dados()
    st.title("Execução e alvarás")
    if exe.empty:
        st.info("A aba Execução ainda não tem lançamentos.")
        return

    c = st.columns(4)
    c[0].metric("Cumprimentos", num(len(exe)), f"{num(exe['DISTRIB.'].notna().sum())} distribuídos",
                delta_color="off")
    c[1].metric("Total executado", brl(exe["TOTAL"].sum()))
    c[2].metric("Honorários", brl(exe["HONORARIOS"].sum()))
    c[3].metric("Alvarás expedidos", num(exe["EXP. ALVARÁ"].notna().sum()))

    esq, dir_ = st.columns(2)
    with esq:
        funil = pd.DataFrame({"Etapa": EXEC_DATAS, "Processos": [exe[e].notna().sum() for e in EXEC_DATAS]})
        _chart(px.funnel(funil, x="Processos", y="Etapa", title="Até onde cada cumprimento chegou"))
    with dir_:
        cols = [c for c in exe.columns if "→" in c]
        t = exe[cols].agg(["count", "mean", "median"]).T.reset_index()
        t.columns = ["Intervalo", "Processos", "Média (dias)", "Mediana (dias)"]
        st.markdown("**Tempo entre etapas**")
        st.dataframe(t, hide_index=True, width="stretch",
                     column_config={"Média (dias)": st.column_config.NumberColumn(format="%.0f"),
                                    "Mediana (dias)": st.column_config.NumberColumn(format="%.0f")})

    vis = ["CLIENTE", "ORIGINARIO", "CUMPRIMENTO", "TRIBUNAL", "Etapa atual"] + EXEC_DATAS + \
          [c for c in ["TOTAL", "HONORARIOS", "REPETIÇÃO", "MULTA 10%", "HON. 10%", "ALVARA"] if c in exe]
    cfg = {c: st.column_config.DateColumn(format="DD/MM/YYYY") for c in EXEC_DATAS}
    cfg.update({c: st.column_config.NumberColumn(format="R$ %.2f")
                for c in ["TOTAL", "HONORARIOS", "REPETIÇÃO", "MULTA 10%", "HON. 10%", "ALVARA"]})
    st.dataframe(exe[vis], hide_index=True, width="stretch", column_config=cfg)


def clientes():
    reg, prz, exe = _dados()
    st.title("Clientes")
    r, ex = _base_fin(reg, exe)
    n_prz = prz.groupby("cnj").size()
    r = r.assign(PrazosAba=r["cnj"].map(n_prz).fillna(0))
    ex_cli = ex.groupby("Cliente (base)").agg(
        Executado=("TOTAL", "sum"), Receita_exec=("Receita do escritório", "sum"),
        Alvarás=("ALVARA", "sum"), Execuções=("CLIENTE", "size"))
    t = r.groupby("Cliente (base)").agg(
        Ações=("Cliente", "size"),
        Bancos=("Banco", lambda s: ", ".join(sorted(s.dropna().unique()))),
        Demandas=("Demanda", lambda s: ", ".join(sorted(s.dropna().unique()))),
        Valor_total=("Valor da causa", "sum"),
        Contratuais=("Contratuais (total)", "sum"),
        Parcela=("Honorários Parc.", "sum"),
        Sucumbência=("Sucumbenciais", "sum"),
        Previstos=("Honorários previstos", "sum"),
        Sentenças=("Tem sentença", "sum"),
        Prazos=("PrazosAba", "sum"),
        Primeira_distribuição=("Distribuição", "min"),
    ).join(ex_cli, how="left").reset_index().sort_values("Previstos", ascending=False)

    c = st.columns(4)
    c[0].metric("Clientes", num(len(t)))
    c[1].metric("Ações por cliente (média)", num(t["Ações"].mean(), 2))
    c[2].metric("Honorários previstos por cliente (média)", brl(t["Previstos"].mean()))
    c[3].metric("Clientes com mais de uma ação", num((t["Ações"] > 1).sum()))

    esq, dir_ = st.columns(2)
    with esq:
        g = t["Ações"].value_counts().sort_index().reset_index()
        g.columns = ["Ações", "Clientes"]
        _chart(px.bar(g, x="Ações", y="Clientes", text="Clientes", title="Quantas ações cada cliente tem",
                      labels={"Ações": "ações por cliente"}).update_xaxes(type="category"), 320)
    with dir_:
        g = t.nlargest(10, "Previstos").sort_values("Previstos")
        g = g.melt(id_vars="Cliente (base)", value_vars=["Contratuais", "Sucumbência"], var_name="Tipo", value_name="R$")
        _chart(px.bar(g, x="R$", y="Cliente (base)", color="Tipo", orientation="h",
                      title="10 clientes com mais honorários previstos",
                      color_discrete_sequence=["#00315F", "#C9A227"], labels={"Cliente (base)": ""}), 320)

    st.dataframe(t, hide_index=True, width="stretch", column_config={
        "Valor_total": MOEDA("Valor da causa"), "Contratuais": MOEDA("Contratuais previstos"),
        "Parcela": MOEDA("dos quais parcela fixa"),
        "Sucumbência": MOEDA("Sucumbência prevista"), "Previstos": MOEDA("Honorários previstos"),
        "Executado": MOEDA("Em execução"), "Receita_exec": MOEDA("Receita na execução"),
        "Alvarás": MOEDA("Alvarás"), "Prazos": st.column_config.NumberColumn(format="%d"),
        "Execuções": st.column_config.NumberColumn(format="%d"),
        "Primeira_distribuição": st.column_config.DateColumn("1ª distribuição", format="DD/MM/YYYY"),
    })

    cli = st.selectbox("Abrir cliente", t["Cliente (base)"], index=None, placeholder="Escolha um cliente")
    if not cli:
        return
    rc = r[r["Cliente (base)"] == cli]
    ec = ex[ex["Cliente (base)"] == cli]
    st.markdown(f"### {cli}")

    c = st.columns(4)
    c[0].metric("Ações", num(len(rc)), f"{num(rc['Tem sentença'].sum())} com sentença", delta_color="off")
    c[1].metric("Valor da causa", brl(rc["Valor da causa"].sum()),
                f"sem danos: {brl(rc['Causa s/ danos'].sum())}", delta_color="off")
    c[2].metric("Contratuais previstos", brl(rc["Contratuais (total)"].sum()),
                f"parcela fixa: {brl(rc['Honorários Parc.'].sum())}", delta_color="off")
    c[3].metric("Sucumbência prevista", brl(rc["Sucumbenciais"].sum()))
    c = st.columns(4)
    c[0].metric("Honorários previstos", brl(rc["Honorários previstos"].sum()))
    c[1].metric("Em execução", brl(ec["TOTAL"].sum()), f"{num(len(ec))} cumprimentos", delta_color="off")
    c[2].metric("Receita do escritório na execução", brl(ec["Receita do escritório"].sum()))
    c[3].metric("Repasse estimado ao cliente", brl(ec["Repasse ao cliente"].sum()))

    fases = rc["Fase financeira"].value_counts().reindex(FASES_FIN).dropna()
    st.caption("Situação das ações: " + "  |  ".join(f"{f}: {int(n)}" for f, n in fases.items()))

    st.markdown("**Ações**")
    cols = ["Demanda", "Rito (grupo)", "Banco - Réu", "Benefício", "Nº processo", "Tribunal", "Fase financeira", "Distribuição",
            "Valor da causa", "Contratuais", "Honorários Parc.", "Sucumbenciais", "Honorários previstos", "Sentença",
            "Data Sent.",
            "Trâns. Julgado"]
    st.dataframe(rc[cols], hide_index=True, width="stretch", column_config={
        "Rito (grupo)": "Rito", "Banco - Réu": "Banco",
        "Contratuais": MOEDA("Contratuais (%)"), "Honorários Parc.": MOEDA("Parcela fixa"),
        **{c: MOEDA() for c in ["Valor da causa", "Sucumbenciais", "Honorários previstos"]},
        **{c: st.column_config.DateColumn(format="DD/MM/YYYY") for c in ["Distribuição", "Data Sent.", "Trâns. Julgado"]}})

    if len(ec):
        st.markdown("**Execuções**")
        vis = ["CLIENTE", "CUMPRIMENTO", "Etapa atual", "TOTAL", "Êxito do cliente", "Parcela fixa",
               "Sucumbência (execução)", "Contratuais (execução)", "Receita do escritório", "Repasse ao cliente", "ALVARA"]
        st.dataframe(ec[vis], hide_index=True, width="stretch", column_config={c: MOEDA() for c in vis[3:]})

    p = prz[prz["cnj"].isin(rc["cnj"]) | (prz["Cliente (base)"] == cli)]
    with st.expander(f"Prazos ({len(p)})"):
        st.dataframe(p[["PROCESSO", "DEMANDA", "CONCLUSÃO", "FATAL", "Antecedência (dias)"]].sort_values("CONCLUSÃO"),
                     hide_index=True, width="stretch",
                     column_config={c: st.column_config.DateColumn(format="DD/MM/YYYY") for c in ["CONCLUSÃO", "FATAL"]})


def ficha():
    _, prz, exe = _dados()
    reg = st.session_state.reg_all
    st.title("Ficha do processo")
    rot = (reg["Cliente (base)"] + " | " + reg["Demanda"].fillna("") + " | " + reg["Banco - Réu"].fillna("")
           + " | " + reg["Nº processo"].fillna("sem número"))
    escolha = st.selectbox("Processo", rot.index, format_func=lambda i: rot[i], index=None,
                           placeholder="Busque pelo nome, banco ou número")
    if escolha is None:
        return
    r = reg.loc[escolha]

    c = st.columns(4)
    c[0].metric("Valor da causa", brl(r["Valor da causa"]))
    c[1].metric("Honorários contratuais", brl(r["Contratuais (total)"]),
                f"parcela fixa: {brl(r['Honorários Parc.'])}", delta_color="off")
    c[2].metric("Tribunal", _txt(r["Tribunal"]))
    c[3].metric("Dias em curso", num(r["Dias em curso (calc.)"]))
    st.markdown(f"**Status:** {_txt(r['Status'])}  |  **Rito:** {r['Rito (grupo)']}{'  |  **Benefício:** ' + r['Benefício'] if isinstance(r.get('Benefício'), str) else ''}  |  "
                f"**Contratos:** {num(r['Contratos'])}  |  **Sentença:** {_txt(r['Sentença'], 'sem sentença')}  |  "
                f"**Pedidos:** {_txt(r['Pedidos'])}")
    if isinstance(r.get("Bitrix processo"), str) and r["Bitrix processo"].startswith("http"):
        st.link_button("Abrir no Bitrix", r["Bitrix processo"])

    p = prz[prz["cnj"] == r["cnj"]] if pd.notna(r["cnj"]) else prz.iloc[0:0]
    e = exe[exe["cnj_orig"] == r["cnj"]] if pd.notna(r["cnj"]) else exe.iloc[0:0]

    eventos = [("Assinatura", r["Assinatura"]), ("Distribuição", r["Distribuição"]),
               ("Sentença", r["Data Sent."]), ("Trânsito em julgado", r["Trâns. Julgado"])]
    eventos += [(f"Prazo: {d}", c) for d, c in zip(p["DEMANDA"], p["CONCLUSÃO"])]
    for _, x in e.iterrows():
        eventos += [(f"Execução: {c}", x[c]) for c in EXEC_DATAS]
    ev = pd.DataFrame(eventos, columns=["Evento", "Data"]).dropna().sort_values("Data")
    if len(ev):
        ev["Trilha"] = ev["Evento"].str.split(":").str[0].replace(
            {"Assinatura": "Processo", "Distribuição": "Processo", "Sentença": "Processo",
             "Trânsito em julgado": "Processo"})
        fig = px.scatter(ev, x="Data", y="Trilha", color="Trilha", hover_name="Evento", title="Linha do tempo")
        fig.update_traces(marker=dict(size=13, line=dict(width=1, color="white")))
        _chart(fig, 260)
        st.dataframe(ev[["Data", "Evento"]], hide_index=True, width="stretch",
                     column_config={"Data": st.column_config.DateColumn(format="DD/MM/YYYY")})


def qualidade():
    st.title("Qualidade dos dados")
    st.caption("Inconsistências na planilha que distorcem os indicadores. Corrija na origem.")
    avisos = st.session_state.get("avisos", [])
    if not avisos:
        st.success("Nenhuma inconsistência encontrada nas regras verificadas.")
    for a in avisos:
        st.warning(a)
    reg, prz, exe = st.session_state.reg_all, st.session_state.prz, st.session_state.exe
    conhecidos = set(reg["cnj"].dropna()) | set(exe["cnj_cump"].dropna())
    orf = prz[prz["cnj"].notna() & ~prz["cnj"].isin(conhecidos)]
    if len(orf):
        st.markdown("**Prazos cujo processo não está no Registro nem na Execução**")
        st.dataframe(orf[["AUTOR / PEDIDO", "PROCESSO", "SISTEMA", "DEMANDA", "CONCLUSÃO"]].drop_duplicates("PROCESSO"),
                     hide_index=True, width="stretch",
                     column_config={"CONCLUSÃO": st.column_config.DateColumn(format="DD/MM/YYYY")})
    fora = reg[reg["cnj"].isna() & reg["Nº processo"].notna()]
    if len(fora):
        st.markdown("**Números fora do padrão CNJ no Registro**")
        st.dataframe(fora[["Cliente", "Demanda", "Nº processo"]], hide_index=True, width="stretch")
