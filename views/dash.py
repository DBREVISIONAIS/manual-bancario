import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit as st

from data import EXEC_DATAS

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


def num(v, casas=0):
    if pd.isna(v):
        return "–"
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


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
    c[1].metric("Honorários contratuais estimados", brl(reg["Contratuais"].sum(), 0))
    c[2].metric("Prazos cumpridos (total)", num(len(prz)))
    c[3].metric("Mediana distribuição → sentença", f"{num(reg['Distribuição → Sentença'].median())} dias")

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
        g = reg.groupby("Banco - Réu").size().nlargest(12).sort_values().reset_index(name="Processos")
        _chart(px.bar(g, x="Processos", y="Banco - Réu", orientation="h", title="Bancos mais demandados"), 420)
    with dir_:
        g = reg.groupby("Tribunal").size().sort_values().reset_index(name="Processos")
        _chart(px.bar(g, x="Processos", y="Tribunal", orientation="h", title="Processos por tribunal"), 420)


def processos():
    reg, prz, _ = _dados()
    st.title("Processos e sentenças")

    st.subheader("Qual tipo de ação tem mais sentença")
    t = reg.groupby("Demanda").agg(
        Processos=("Cliente", "size"),
        Sentenciados=("Tem sentença", "sum"),
        Procedentes=("Resultado", lambda s: s.isin(["Procedente", "Parcialmente procedente"]).sum()),
        Improcedentes=("Resultado", lambda s: (s == "Improcedente").sum()),
        Valor_médio=("Valor da causa", "mean"),
        Dias_até_sentença=("Distribuição → Sentença", "median"),
    ).reset_index()
    t["% sentenciado"] = 100 * t["Sentenciados"] / t["Processos"]
    t["% êxito (entre sentenciados)"] = 100 * t["Procedentes"] / t["Sentenciados"].where(t["Sentenciados"] > 0)
    t = t.sort_values("Sentenciados", ascending=False)
    st.dataframe(t, hide_index=True, width="stretch", column_config={
        "Valor_médio": st.column_config.NumberColumn("Valor médio da causa", format="R$ %.2f"),
        "Dias_até_sentença": st.column_config.NumberColumn("Mediana até sentença (dias)", format="%.0f"),
        "% sentenciado": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100),
        "% êxito (entre sentenciados)": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100),
    })
    g = reg.assign(Resultado=reg["Resultado"].fillna("Sem sentença")).groupby(["Demanda", "Resultado"]).size()
    _chart(px.bar(g.reset_index(name="Processos"), x="Demanda", y="Processos", color="Resultado",
                  color_discrete_map=COR_RES, title="Resultado por tipo de ação"))

    st.subheader("Quais tribunais são mais rápidos")
    st.caption("Mediana de dias corridos entre distribuição e sentença, só com processos já sentenciados. "
               "Tribunais com poucos processos têm leitura frágil; use o mínimo abaixo para filtrar.")
    minimo = st.slider("Mínimo de sentenças por tribunal", 1, 10, 2)
    rap = _tempo_por(reg, "Tribunal", "Distribuição → Sentença", minimo)
    if rap.empty:
        st.info("Nenhum tribunal atinge esse mínimo de sentenças.")
    else:
        fig = px.bar(rap, x="Mediana", y="Tribunal", orientation="h", text="Processos",
                     title="Dias até a sentença (mediana)", labels={"Mediana": "dias"})
        fig.update_traces(texttemplate="%{text} sent.", textposition="outside")
        fig.update_yaxes(categoryorder="total descending")
        _chart(fig, 80 + 38 * len(rap))
    abertos = reg[reg["Distribuição"].notna() & ~reg["Tem sentença"]]
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
    por = st.radio("Comparar por", ["Demanda", "Banco - Réu", "Tribunal", "Rito"], horizontal=True)
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
    por_v = st.radio("Agrupar valor por", ["Demanda", "Banco - Réu", "Tribunal"], horizontal=True, key="pv")
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
    n_prz = prz.groupby("cnj").size()
    base = reg.assign(PrazosAba=reg["cnj"].map(n_prz).fillna(0))
    t = base.groupby("Cliente (base)").agg(
        Ações=("Cliente", "size"),
        Bancos=("Banco - Réu", lambda s: ", ".join(sorted(s.dropna().unique()))),
        Demandas=("Demanda", lambda s: ", ".join(sorted(s.dropna().unique()))),
        Valor_total=("Valor da causa", "sum"),
        Valor_médio=("Valor da causa", "mean"),
        Contratuais=("Contratuais", "sum"),
        Sentenças=("Tem sentença", "sum"),
        Prazos=("PrazosAba", "sum"),
        Primeira_distribuição=("Distribuição", "min"),
    ).reset_index().sort_values("Valor_total", ascending=False)

    c = st.columns(4)
    c[0].metric("Clientes", num(len(t)))
    c[1].metric("Ações por cliente (média)", num(t["Ações"].mean(), 2))
    c[2].metric("Valor da causa por cliente (média)", brl(t["Valor_total"].mean()))
    c[3].metric("Clientes com mais de uma ação", num((t["Ações"] > 1).sum()))

    _chart(px.histogram(t, x="Ações", title="Quantas ações cada cliente tem",
                        labels={"Ações": "ações por cliente"}).update_layout(bargap=.15, yaxis_title="clientes"), 300)

    st.dataframe(t, hide_index=True, width="stretch", column_config={
        "Valor_total": st.column_config.NumberColumn("Valor da causa (soma)", format="R$ %.2f"),
        "Valor_médio": st.column_config.NumberColumn("Valor da causa (média)", format="R$ %.2f"),
        "Contratuais": st.column_config.NumberColumn("Honorários contratuais", format="R$ %.2f"),
        "Prazos": st.column_config.NumberColumn(format="%d"),
        "Primeira_distribuição": st.column_config.DateColumn("1ª distribuição", format="DD/MM/YYYY"),
    })

    cli = st.selectbox("Abrir cliente", t["Cliente (base)"], index=None, placeholder="Escolha um cliente")
    if cli:
        r = reg[reg["Cliente (base)"] == cli]
        st.markdown(f"#### {cli}")
        st.dataframe(r[["Demanda", "Banco - Réu", "Nº processo", "Tribunal", "Distribuição", "Valor da causa",
                        "Sentença", "Data Sent.", "Trâns. Julgado", "Dias em curso (calc.)"]],
                     hide_index=True, width="stretch",
                     column_config={"Valor da causa": st.column_config.NumberColumn(format="R$ %.2f"),
                                    **{c: st.column_config.DateColumn(format="DD/MM/YYYY")
                                       for c in ["Distribuição", "Data Sent.", "Trâns. Julgado"]}})
        p = prz[prz["cnj"].isin(r["cnj"]) | (prz["Cliente (base)"] == cli)]
        st.markdown(f"**Prazos ({len(p)})**")
        st.dataframe(p[["PROCESSO", "DEMANDA", "CONCLUSÃO", "FATAL", "Antecedência (dias)"]]
                     .sort_values("CONCLUSÃO"), hide_index=True, width="stretch",
                     column_config={c: st.column_config.DateColumn(format="DD/MM/YYYY") for c in ["CONCLUSÃO", "FATAL"]})
        e = exe[exe["Cliente (base)"] == cli]
        if len(e):
            st.markdown("**Execuções**")
            st.dataframe(e[["CLIENTE", "CUMPRIMENTO", "Etapa atual", "TOTAL", "HONORARIOS"]], hide_index=True,
                         width="stretch")


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
    c[1].metric("Honorários contratuais", brl(r["Contratuais"]))
    c[2].metric("Tribunal", r["Tribunal"] or "–")
    c[3].metric("Dias em curso", num(r["Dias em curso (calc.)"]))
    st.markdown(f"**Status:** {r['Status'] or '–'}  |  **Rito:** {r['Rito'] or '–'}  |  "
                f"**Contratos:** {num(r['Contratos'])}  |  **Sentença:** {r['Sentença'] or 'sem sentença'}  |  "
                f"**Pedidos:** {r['Pedidos'] or '–'}")
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
