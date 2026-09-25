"""Leitura e tratamento das abas Registro, Prazos e Execução.

Só estas três abas são lidas. A planilha tem outras abas com dados sensíveis
que nunca devem entrar no app.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------- utilidades

def _norm(txt: str) -> str:
    txt = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", txt).strip().lower()


def _money_one(v) -> float | None:
    """Aceita 'R$ 8.880,68' (texto da planilha) e '8880.68' (número vindo do .xlsx)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    t = re.sub(r"[R$\s]", "", str(v))
    if not t or t in {"-", "–"}:
        return None
    if "," in t:                                # padrão brasileiro
        t = t.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+", t):   # 'R$ 1.000' sem centavos
        t = t.replace(".", "")
    try:
        return float(t)
    except ValueError:
        return None


def parse_money(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.map(_money_one), errors="coerce")


def parse_date(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s.astype(str).str.strip(), format="%d/%m/%Y", errors="coerce")


def cnj_digits(s: pd.Series) -> pd.Series:
    """Número CNJ só com dígitos (20), usado como chave entre as abas."""
    d = s.astype(str).str.replace(r"\D", "", regex=True)
    return d.where(d.str.len() == 20)


# Res. CNJ 65/2008: segmento J.TR do número único
_TR_ESTADUAL = {
    "01": "TJAC", "02": "TJAL", "03": "TJAP", "04": "TJAM", "05": "TJBA", "06": "TJCE",
    "07": "TJDFT", "08": "TJES", "09": "TJGO", "10": "TJMA", "11": "TJMT", "12": "TJMS",
    "13": "TJMG", "14": "TJPA", "15": "TJPB", "16": "TJPR", "17": "TJPE", "18": "TJPI",
    "19": "TJRJ", "20": "TJRN", "21": "TJRS", "22": "TJRO", "23": "TJRR", "24": "TJSC",
    "25": "TJSE", "26": "TJSP", "27": "TJTO",
}


def tribunal_from_cnj(d: pd.Series) -> pd.Series:
    def one(x):
        if not isinstance(x, str):
            return None
        j, tr = x[13], x[14:16]
        if j == "8":
            return _TR_ESTADUAL.get(tr)
        if j == "4":
            return f"TRF{int(tr)}"
        return None
    return d.map(one)


_BENEFICIO = r"PENS[AÃ]O|APOSENTADORIA|APOSENT\.?"


def banco_base(s: pd.Series) -> pd.Series:
    """Deixa só o nome do banco.

    Remove o tipo de benefício e a modalidade RMC/RCC ('FACTA PENSÃO', 'PAN RCC APOSENTADORIA', 'PAN (APOSENTADORIA)', 'FACTA - PENSÃO 2')
    e a numeração do contrato ('AGIBANK 9', 'AGIBANK9', 'AGIBANK (2)', 'AGIBANK - 3', 'AGIBANK nº 4').
    """
    t = s.astype("string").str.strip().str.upper()
    t = t.str.replace(rf"[\s\-–_/(]*\b({_BENEFICIO})\b[\s)]*", " ", regex=True)
    t = t.str.replace(r"[\s\-–_/(]*\b(RMC|RCC)\b[\s)]*", " ", regex=True)  # modalidade já está em Demanda
    t = t.str.replace(r"[\s\-–_#.]*(N[º°O]\.?\s*)?\(?\d+\)?\s*$", "", regex=True)
    return t.str.replace(r"\s+", " ", regex=True).str.strip(" -–_/")


def beneficio(s: pd.Series) -> pd.Series:
    """Pensão ou Aposentadoria, quando indicado junto do banco."""
    t = s.astype("string").str.upper()
    return pd.Series(pd.NA, index=s.index, dtype="string").mask(
        t.str.contains(r"PENS[AÃ]O", regex=True, na=False), "Pensão").mask(
        t.str.contains(r"APOSENT", regex=True, na=False), "Aposentadoria")


def cliente_base(s: pd.Series) -> pd.Series:
    """'FULANO x AGIBANK 2' -> 'FULANO'."""
    return (s.astype(str).str.split(r"\s+x\s+", n=1, regex=True).str[0]
            .str.replace(r"\s+", " ", regex=True).str.strip().str.upper())


def build_frame(values: list[list[str]], must_have: tuple[str, ...]) -> pd.DataFrame:
    """Localiza a linha de cabeçalho (há linhas de totais acima dela)."""
    keys = [_norm(k) for k in must_have]
    for i, row in enumerate(values[:15]):
        normed = [_norm(c) for c in row]
        if all(k in normed for k in keys):
            header = [c.strip() or f"col_{j}" for j, c in enumerate(row)]
            body = [r + [""] * (len(header) - len(r)) for r in values[i + 1:]]
            df = pd.DataFrame([r[: len(header)] for r in body], columns=header)
            df = df.replace({"": pd.NA}).dropna(how="all")
            acima = [r for r in values[:i] if any(str(c).strip() for c in r)]
            if acima:  # linha de totais da planilha, usada para conferência
                ult = acima[-1] + [""] * (len(header) - len(acima[-1]))
                df.attrs["totais"] = dict(zip(header, ult[: len(header)]))
            return df
    raise ValueError(f"Cabeçalho não encontrado (procurei {must_have}).")


# ---------------------------------------------------------------- leitura

TABS = {
    "registro": ("Cliente", "Situação", "Demanda"),
    "prazos": ("AUTOR / PEDIDO", "PROCESSO", "FATAL"),
    "execucao": ("DISTRIB.", "CLIENTE", "ORIGINARIO"),
}


def _match_ws(titles: list[str], wanted: str) -> str | None:
    w = _norm(wanted)
    for t in titles:
        if _norm(t) == w:
            return t
    for t in titles:
        if w in _norm(t):
            return t
    return None


@st.cache_data(ttl=600, show_spinner="Lendo a planilha…")
def load_from_gsheets() -> dict[str, list[list[str]]]:
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    sh = gspread.authorize(creds).open_by_key(st.secrets["sheet"]["id"])
    titles = [ws.title for ws in sh.worksheets()]
    names = st.secrets["sheet"].get("tabs", {})
    out = {}
    for key, default in (("registro", "Registro"), ("prazos", "Prazos"), ("execucao", "Execução")):
        title = _match_ws(titles, names.get(key, default))
        if title is None:
            raise ValueError(f"Aba '{names.get(key, default)}' não encontrada. Abas: {titles}")
        out[key] = sh.worksheet(title).get_all_values()
    return out


def _celula_xlsx(v) -> str:
    """Converte a célula do .xlsx para o mesmo texto que a planilha exibe.

    Números viram texto com vírgula decimal ('185,829'), para não serem
    confundidos com separador de milhar ('185.829' seria lido como 185 mil).
    """
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, (pd.Timestamp, datetime)):
        return v.strftime("%d/%m/%Y")
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if v.is_integer():
            return str(int(v))
        return repr(v).replace(".", ",")
    return str(v).strip()


NOMES_PADRAO = (("registro", "Registro"), ("prazos", "Prazos"), ("execucao", "Execução"))


def _nomes_abas() -> dict[str, str]:
    """Nomes das abas, com possível ajuste em [sheet.tabs] nos Secrets."""
    try:
        custom = dict(st.secrets.get("sheet", {}).get("tabs", {}))
    except Exception:  # noqa: BLE001
        custom = {}
    return {k: custom.get(k, v) for k, v in NOMES_PADRAO}


@st.cache_data(ttl=600, show_spinner="Lendo a planilha…")
def load_from_public_link(sheet_id: str) -> dict[str, list[list[str]]]:
    """Baixa a planilha inteira em .xlsx pelo link de visualização pública.

    Exige compartilhamento 'Qualquer pessoa com o link: Leitor'. Use SOMENTE com a
    planilha auxiliar que contém apenas Registro, Prazos e Execução.
    """
    import io
    import urllib.error
    import urllib.request

    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            conteudo = r.read()
            tipo = r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 404):
            raise ValueError("A planilha não está pública. Em Compartilhar, defina "
                             "'Qualquer pessoa com o link: Leitor' e confira o ID.") from e
        raise ValueError(f"O Google recusou o download (HTTP {e.code}).") from e
    if "spreadsheetml" not in tipo and not conteudo.startswith(b"PK"):
        raise ValueError("O Google devolveu uma página de login em vez da planilha. "
                         "Confira se o acesso está como 'Qualquer pessoa com o link'.")
    return load_from_xlsx(io.BytesIO(conteudo))


def load_from_xlsx(file) -> dict[str, list[list[str]]]:
    xl = pd.ExcelFile(file)
    out = {}
    for key, default in _nomes_abas().items():
        title = _match_ws(xl.sheet_names, default)
        if title is None:
            raise ValueError(f"Aba '{default}' não encontrada. Abas na planilha: {xl.sheet_names}")
        df = xl.parse(title, header=None, dtype=object)
        out[key] = df.map(_celula_xlsx).values.tolist()
    return out


# ---------------------------------------------------------------- tratamento

def _padroniza(df: pd.DataFrame, canonicos: list[str]) -> pd.DataFrame:
    """Aceita variações de acento, caixa e espaço nos títulos ('ALVARÁ' -> 'ALVARA')
    e cria vazias as colunas esperadas que a planilha não tiver, para o painel não quebrar."""
    alvo = {_norm(c): c for c in canonicos}
    df = df.rename(columns=lambda c: alvo.get(_norm(c), c))
    faltando = [c for c in canonicos if c not in df.columns]
    for c in faltando:
        df[c] = pd.NA
    df.attrs["colunas_ausentes"] = faltando
    return df


REG_COLUNAS = ["Cliente", "Situação", "Demanda", "Banco - Réu", "Assinatura", "Valor da causa", "Causa s/ danos",
               "Contratuais", "Honorários Parc.", "Sucumbenciais", "Contratos", "Status", "Rito", "Distribuição",
               "UF", "Nº processo", "Prazos", "Sentença", "Data Sent.", "Pedidos", "Trâns. Julgado", "Execução",
               "Bitrix processo"]


def prep_registro(values, hoje: pd.Timestamp) -> pd.DataFrame:
    df = build_frame(values, TABS["registro"])
    totais = df.attrs.get("totais", {})
    df = df[df["Cliente"].notna()].copy()
    # "Honorários Parc." = parcela fixa dos contratuais (ex.: R$ 500 em só uma das ações do contrato).
    # Planilhas antigas não têm a coluna: ela é criada vazia e a execução usa o valor padrão das premissas.
    tem_parc = _norm("Honorários Parc.") in [_norm(c) for c in df.columns]
    df = _padroniza(df, REG_COLUNAS)
    VALORES = ["Valor da causa", "Causa s/ danos", "Contratuais", "Honorários Parc.", "Sucumbenciais"]
    for c in VALORES:
        df[c] = parse_money(df[c])
    df["Contratuais (total)"] = df[["Contratuais", "Honorários Parc."]].sum(axis=1, min_count=1)
    # percentual contratado em cada ação, lido do próprio Registro (Contratuais / Valor da causa)
    df["% contratual"] = (df["Contratuais"] / df["Valor da causa"]).where(df["Valor da causa"] > 0)
    df["Honorários previstos"] = df[["Contratuais (total)", "Sucumbenciais"]].sum(axis=1, min_count=1)
    df.attrs["tem_parc"] = tem_parc
    df.attrs["totais"] = {c: _money_one(totais.get(c)) for c in VALORES + ["Contratos"]}
    for c in ["Assinatura", "Distribuição", "Data Sent.", "Trâns. Julgado"]:
        df[c] = parse_date(df[c])
    for c in ["Contratos", "Prazos"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["Nº processo"] = df["Nº processo"].astype("string").str.strip()
    df["cnj"] = cnj_digits(df["Nº processo"])
    df["Tribunal"] = tribunal_from_cnj(df["cnj"])
    df["Cliente (base)"] = cliente_base(df["Cliente"])
    # 'AGIBANK 9' identifica o 9º contrato; para análise, o banco é 'AGIBANK'
    df["Banco"] = banco_base(df["Banco - Réu"])
    df["Benefício"] = beneficio(df["Banco - Réu"])
    df["Situação"] = df["Situação"].astype("string").str.strip().str.capitalize()
    df["Rito (grupo)"] = df["Rito"].map(_classifica_rito)
    df["Sentença"] = df["Sentença"].astype("string").str.strip()
    df["Tem sentença"] = df["Sentença"].notna()
    df["Resultado"] = df["Sentença"].map(_classifica_sentenca)

    # tempos (dias corridos)
    df["Assinatura → Distribuição"] = (df["Distribuição"] - df["Assinatura"]).dt.days
    df["Distribuição → Sentença"] = (df["Data Sent."] - df["Distribuição"]).dt.days
    df["Sentença → Trânsito"] = (df["Trâns. Julgado"] - df["Data Sent."]).dt.days
    df["Distribuição → Trânsito"] = (df["Trâns. Julgado"] - df["Distribuição"]).dt.days
    fim = df["Trâns. Julgado"].fillna(hoje)
    df["Dias em curso (calc.)"] = (fim - df["Distribuição"]).dt.days
    df["Encerrado"] = df["Trâns. Julgado"].notna()
    return df


RITOS = ["Procedimento comum", "Juizado Especial (JEC)", "Administrativo", "Não informado"]


def _classifica_rito(s):
    if not isinstance(s, str) or not s.strip():
        return "Não informado"
    n = _norm(s)
    if "jec" in n or "juizado" in n or "jef" in n:
        return "Juizado Especial (JEC)"
    if n.startswith("adm"):
        return "Administrativo"
    if "comum" in n or "ordinari" in n:
        return "Procedimento comum"
    return s.strip()


def _classifica_sentenca(s):
    if not isinstance(s, str) or not s.strip():
        return None
    n = _norm(s)
    if "parcial" in n:
        return "Parcialmente procedente"
    if "improced" in n:
        return "Improcedente"
    if "proced" in n:
        return "Procedente"
    if "extin" in n:
        return "Extinção sem mérito"
    if "acordo" in n or "homolog" in n:
        return "Acordo"
    return s.strip()


def prep_prazos(values) -> pd.DataFrame:
    df = build_frame(values, TABS["prazos"])
    df = df[df["AUTOR / PEDIDO"].notna()].copy()
    # a coluna já se chamou "ELABADO" (erro de digitação na planilha); aceita os dois nomes
    df = df.rename(columns={c: "ELABORADO" for c in df.columns if _norm(c) in ("elabado", "elaborado")})
    df = _padroniza(df, ["AUTOR / PEDIDO", "PROCESSO", "SISTEMA", "DEMANDA", "CONCLUSÃO", "FATAL", "ELABORADO"])
    df["ELABORADO"] = df["ELABORADO"].astype("string").str.strip()
    df["CONCLUSÃO"] = parse_date(df["CONCLUSÃO"])
    df["FATAL"] = parse_date(df["FATAL"])
    df["cnj"] = cnj_digits(df["PROCESSO"])
    df["Tribunal"] = tribunal_from_cnj(df["cnj"])
    df["Cliente (base)"] = cliente_base(df["AUTOR / PEDIDO"])
    # dias entre CONCLUSÃO e FATAL (mesma conta da coluna DIAS, com sinal invertido)
    df["Antecedência (dias)"] = (df["FATAL"] - df["CONCLUSÃO"]).dt.days
    df["No dia do fatal"] = df["Antecedência (dias)"] == 0
    df["Após o fatal"] = df["Antecedência (dias)"] < 0
    df["Mês"] = df["CONCLUSÃO"].dt.to_period("M").dt.to_timestamp()
    df["DEMANDA"] = df["DEMANDA"].astype("string").str.strip()
    df["Tipo de peça"] = df["DEMANDA"].map(_tipo_peca)
    return df


def _tipo_peca(s):
    if not isinstance(s, str):
        return "Outros"
    n = _norm(s)
    regras = [
        ("renuncia", "Ciência / renúncia ao prazo"), ("emenda", "Emenda à inicial"),
        ("replica", "Réplica"), ("apelac", "Apelação"), ("contrarraz", "Contrarrazões"),
        ("embargos", "Embargos"), ("agravo", "Agravo"), ("cumprimento", "Cumprimento de sentença"),
        ("alvara", "Alvará"), ("procura", "Procuração"), ("ajg", "Gratuidade (AJG)"),
        ("gratuidade", "Gratuidade (AJG)"), ("extrato", "Juntada de documentos"),
        ("junta", "Juntada de documentos"), ("provas", "Especificação de provas"),
        ("sentenca", "Ciência de sentença"), ("recurso inominado", "Recurso inominado"),
        ("desist", "Desistência"), ("audiencia", "Audiência"), ("1414", "Suspensão (Tema 1414)"),
        ("suspens", "Suspensão (Tema 1414)"), ("migra", "Migração de sistema"),
        ("inversao", "Inversão do ônus da prova"), ("quesito", "Quesitos"),
        ("peticao simples", "Petição simples"), ("petisao", "Petição simples"),
    ]
    for chave, rotulo in regras:
        if chave in n:
            return rotulo
    return "Outros"


EXEC_DATAS = ["DISTRIB.", "SISBAJUD", "BLOQUEIO", "PED. ALVARÁ", "EXP. ALVARÁ"]
EXEC_VALORES = ["TOTAL", "HONORARIOS", "REPETIÇÃO", "MULTA 10%", "HON. 10%", "ALVARA"]


def prep_execucao(values) -> pd.DataFrame:
    df = build_frame(values, TABS["execucao"])
    df = df[df["CLIENTE"].notna()].copy()
    df = _padroniza(df, EXEC_DATAS + EXEC_VALORES + ["Tipo", "CLIENTE", "ORIGINARIO", "CUMPRIMENTO", "TRIBUNAL"])
    for c in EXEC_DATAS:
        df[c] = parse_date(df[c])
    for c in EXEC_VALORES:
        df[c] = parse_money(df[c])
    # coluna F da planilha: cumprimento de sentença ou acordo
    df["Tipo"] = df["Tipo"].astype("string").str.strip().str.capitalize().fillna("Não informado")
    df["cnj_orig"] = cnj_digits(df["ORIGINARIO"])
    df["cnj_cump"] = cnj_digits(df["CUMPRIMENTO"])
    df["Cliente (base)"] = cliente_base(df["CLIENTE"])
    pares = list(zip(EXEC_DATAS[:-1], EXEC_DATAS[1:]))
    for a, b in pares:
        df[f"{a} → {b}"] = (df[b] - df[a]).dt.days
    df["Distrib. → Alvará expedido"] = (df["EXP. ALVARÁ"] - df["DISTRIB."]).dt.days
    df["Etapa atual"] = df[EXEC_DATAS].apply(
        lambda r: next((c for c in reversed(EXEC_DATAS) if pd.notna(r[c])), "Não distribuído"), axis=1)

    # composição do crédito: TOTAL = HONORARIOS + REPETIÇÃO + MULTA 10% + HON. 10%
    partes = df[["HONORARIOS", "REPETIÇÃO", "MULTA 10%", "HON. 10%"]]
    df["Soma das parcelas"] = partes.sum(axis=1, min_count=1)
    df["Êxito do cliente"] = df[["REPETIÇÃO", "MULTA 10%"]].sum(axis=1, min_count=1)
    df["Sucumbência (execução)"] = df[["HONORARIOS", "HON. 10%"]].sum(axis=1, min_count=1)
    df["Alvará expedido"] = df["EXP. ALVARÁ"].notna()
    return df


def financeiro_execucao(exe: pd.DataFrame, reg_all: pd.DataFrame | None) -> pd.DataFrame:
    """Receita do escritório e repasse ao cliente em cada cumprimento, com os termos do Registro.

    Cada cumprimento é ligado ao processo originário pelo número CNJ. De lá vêm:
      % contratual = Contratuais / Valor da causa daquela ação;
      parcela fixa = Honorários Parc. daquela ação (célula vazia = R$ 0).
    Contratuais na execução = % contratual × êxito do cliente + parcela fixa, limitado ao êxito.
    Êxito do cliente = REPETIÇÃO + MULTA 10%. Sucumbência = HONORARIOS + HON. 10%.
    Sem vínculo com o Registro, os contratuais ficam em branco: nada é presumido.
    """
    df = exe.copy()
    df["% contratual"] = pd.NA
    df["Parcela fixa"] = pd.NA
    df["Vínculo com o Registro"] = False
    if reg_all is not None and len(reg_all):
        base = reg_all.dropna(subset=["cnj"]).drop_duplicates("cnj").set_index("cnj")
        ok = df["cnj_orig"].isin(base.index)
        df.loc[ok, "% contratual"] = df.loc[ok, "cnj_orig"].map(base["% contratual"])
        df.loc[ok, "Parcela fixa"] = df.loc[ok, "cnj_orig"].map(base["Honorários Parc."]).fillna(0)
        df["Vínculo com o Registro"] = ok
    df["% contratual"] = pd.to_numeric(df["% contratual"], errors="coerce")
    df["Parcela fixa"] = pd.to_numeric(df["Parcela fixa"], errors="coerce")
    exito = df["Êxito do cliente"]
    bruto = (exito * df["% contratual"] + df["Parcela fixa"]).where(exito > 0)
    # o desconto sai da parte do cliente no alvará: não pode passar do êxito dele
    df["Contratuais limitados ao êxito"] = (bruto > exito).fillna(False)
    df["Contratuais (execução)"] = bruto.where(~df["Contratuais limitados ao êxito"], exito)
    df["Receita do escritório"] = df[["Sucumbência (execução)", "Contratuais (execução)"]].sum(axis=1, min_count=1)
    df["Repasse ao cliente"] = exito - df["Contratuais (execução)"].fillna(0)
    return df


FASES_FIN = ["Não distribuído", "Aguardando sentença", "Sentença favorável", "Em execução",
             "Alvará expedido", "Improcedente / extinto"]


def fase_financeira(reg: pd.DataFrame, exe: pd.DataFrame) -> pd.Series:
    """Em que ponto do caminho até o dinheiro cada processo está."""
    em_exec = set(exe.loc[exe["DISTRIB."].notna(), "cnj_orig"].dropna())
    alvara = set(exe.loc[exe["EXP. ALVARÁ"].notna(), "cnj_orig"].dropna())

    def uma(r):
        if r["cnj"] in alvara:
            return "Alvará expedido"
        if r["cnj"] in em_exec:
            return "Em execução"
        if r["Resultado"] in ("Improcedente", "Extinção sem mérito"):
            return "Improcedente / extinto"
        if r["Resultado"] in ("Procedente", "Parcialmente procedente", "Acordo"):
            return "Sentença favorável"
        if pd.notna(r["Distribuição"]):
            return "Aguardando sentença"
        return "Não distribuído"
    return reg.apply(uma, axis=1)


def quality_report(reg, prz, exe) -> list[str]:
    """Inconsistências que distorcem os indicadores."""
    avisos = []
    for nome, df in (("Registro", reg), ("Prazos", prz), ("Execução", exe)):
        falt = df.attrs.get("colunas_ausentes") or []
        falt = [c for c in falt if c not in ("Honorários Parc.", "Tipo")]  # tratadas à parte
        if falt:
            avisos.append(f"{nome}: a planilha não tem a(s) coluna(s) {', '.join(falt)}. O painel trata como vazia "
                          "e os indicadores que dependem dela ficam zerados.")
    totais = dict(reg.attrs.get("totais", {}))
    # a linha de cima só serve de conferência se for o total geral: com filtro ativo na planilha
    # ela vira SUBTOTAL parcial. O total de Contratos (inteiros, sem ambiguidade) indica qual é o caso.
    tot_contr = totais.pop("Contratos", None)
    total_geral = tot_contr is not None and abs(reg["Contratos"].sum() - tot_contr) < 0.5
    for col, esperado in (totais.items() if total_geral else []):
        if esperado:
            lido = reg[col].sum()
            if abs(lido - esperado) > max(1.0, 0.005 * abs(esperado)):
                fmt = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                avisos.append(f"Registro: a soma de '{col}' lida pelo painel ({fmt(lido)}) não bate com o total "
                              f"da linha de cima da planilha ({fmt(esperado)}). Confira antes de usar esse número.")
    if "Soma das parcelas" in exe:
        dif = exe[(exe["TOTAL"].notna()) & ((exe["TOTAL"] - exe["Soma das parcelas"]).abs() > 0.05)]
        if len(dif):
            avisos.append(f"Execução: em {len(dif)} cumprimento(s) o TOTAL não bate com HONORARIOS + REPETIÇÃO + "
                          f"MULTA 10% + HON. 10% ({', '.join(dif['CLIENTE'].astype(str).head(4))}). "
                          "Os valores de receita dessas linhas saem das parcelas, não do TOTAL.")
    if reg.attrs.get("tem_parc"):
        # contagem dobrada: Contratuais (H) ainda com a parcela fixa embutida depois de criada a coluna I
        c = reg.dropna(subset=["Contratuais", "Valor da causa", "Honorários Parc."])
        c = c[c["Honorários Parc."] > 0]
        dobrado = c[(c["Contratuais"] - 0.30 * c["Valor da causa"] - c["Honorários Parc."]).abs() < 1]
        if len(dobrado):
            avisos.append(f"Registro: em {len(dobrado)} processos a coluna Contratuais parece já incluir a parcela "
                          "fixa (30% da causa + Honorários Parc.). Com a coluna nova, Contratuais deve ter só o "
                          "percentual; do contrário a parcela entra duas vezes: "
                          + ", ".join(dobrado["Cliente"].astype(str).head(5)) + ("…" if len(dobrado) > 5 else ""))
        vazio = reg["Honorários Parc."].isna() & reg["Distribuição"].notna()
        if vazio.any():
            avisos.append(f"Registro: {vazio.sum()} processos distribuídos sem valor em 'Honorários Parc.'. "
                          "O painel conta R$ 0 de parcela fixa neles; se for isso mesmo, preencha 0.")
    else:
        avisos.append("Registro: a coluna 'Honorários Parc.' ainda não existe na planilha. Sem ela, o painel "
                      "considera parcela fixa R$ 0 e os contratuais ficam só com o percentual.")
    sem_cnj = reg["cnj"].isna() & reg["Nº processo"].notna() & (reg["Rito (grupo)"] != "Administrativo")
    if sem_cnj.any():
        avisos.append(f"Registro: {sem_cnj.sum()} nº de processo fora do padrão CNJ.")
    orfaos = prz["cnj"].notna() & ~prz["cnj"].isin(set(reg["cnj"].dropna()) | set(exe["cnj_cump"].dropna()))
    if orfaos.any():
        avisos.append(f"Prazos: {orfaos.sum()} lançamentos com processo que não existe no Registro nem na Execução "
                      "(pode ser erro de digitação no número ou processo de outro núcleo).")
    inv = reg["Distribuição → Sentença"] < 0
    if inv.any():
        avisos.append(f"Registro: {inv.sum()} processos com sentença anterior à distribuição.")
    sem_dist = reg["Distribuição"].isna() & reg["Nº processo"].notna()
    if sem_dist.any():
        avisos.append(f"Registro: {sem_dist.sum()} processos com número mas sem data de distribuição.")
    sent_sem_data = reg["Tem sentença"] & reg["Data Sent."].isna()
    if sent_sem_data.any():
        avisos.append(f"Registro: {sent_sem_data.sum()} sentenças sem data.")
    uf_trib = reg.dropna(subset=["Tribunal", "UF"])
    div = uf_trib[uf_trib["Tribunal"].str[2:4] != uf_trib["UF"].str.upper().str.strip()]
    div = div[~div["Tribunal"].str.startswith("TRF") & (div["Tribunal"] != "TJDFT")]
    if len(div):
        avisos.append(f"Registro: {len(div)} processos em que a UF não bate com o tribunal do número CNJ.")
    return avisos
