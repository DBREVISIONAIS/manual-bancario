"""Leitura e tratamento das abas Registro, Prazos e Execução.

Só estas três abas são lidas. A planilha tem outras abas com dados sensíveis
que nunca devem entrar no app.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date

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
            df = df.replace({"": pd.NA})
            return df.dropna(how="all")
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
        df = xl.parse(title, header=None, dtype=str).fillna("")
        # datas do Excel vêm como 'AAAA-MM-DD 00:00:00'; converte para dd/mm/aaaa
        df = df.map(lambda v: re.sub(r"^(\d{4})-(\d{2})-(\d{2})( 00:00:00)?$", r"\3/\2/\1", v))
        # inteiros do Excel vêm como '3.0'; volta para '3'
        df = df.map(lambda v: v[:-2] if re.fullmatch(r"-?\d+\.0", v) else v)
        out[key] = df.values.tolist()
    return out


# ---------------------------------------------------------------- tratamento

def prep_registro(values, hoje: pd.Timestamp) -> pd.DataFrame:
    df = build_frame(values, TABS["registro"])
    df = df[df["Cliente"].notna()].copy()
    for c in ["Valor da causa", "Causa s/ danos", "Contratuais", "Sucumbenciais"]:
        df[c] = parse_money(df[c])
    for c in ["Assinatura", "Distribuição", "Data Sent.", "Trâns. Julgado"]:
        df[c] = parse_date(df[c])
    for c in ["Contratos", "Prazos"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["Nº processo"] = df["Nº processo"].astype("string").str.strip()
    df["cnj"] = cnj_digits(df["Nº processo"])
    df["Tribunal"] = tribunal_from_cnj(df["cnj"])
    df["Cliente (base)"] = cliente_base(df["Cliente"])
    df["Situação"] = df["Situação"].astype("string").str.strip().str.capitalize()
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
    for c in EXEC_DATAS:
        if c in df:
            df[c] = parse_date(df[c])
    for c in EXEC_VALORES:
        if c in df:
            df[c] = parse_money(df[c])
    df["cnj_orig"] = cnj_digits(df["ORIGINARIO"])
    df["cnj_cump"] = cnj_digits(df["CUMPRIMENTO"])
    df["Cliente (base)"] = cliente_base(df["CLIENTE"])
    pares = list(zip(EXEC_DATAS[:-1], EXEC_DATAS[1:]))
    for a, b in pares:
        df[f"{a} → {b}"] = (df[b] - df[a]).dt.days
    df["Distrib. → Alvará expedido"] = (df["EXP. ALVARÁ"] - df["DISTRIB."]).dt.days
    df["Etapa atual"] = df[EXEC_DATAS].apply(
        lambda r: next((c for c in reversed(EXEC_DATAS) if pd.notna(r[c])), "Não distribuído"), axis=1)
    return df


def quality_report(reg, prz, exe) -> list[str]:
    """Inconsistências que distorcem os indicadores."""
    avisos = []
    sem_cnj = reg["cnj"].isna() & reg["Nº processo"].notna()
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
