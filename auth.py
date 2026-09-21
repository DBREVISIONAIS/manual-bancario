"""Tela de acesso por senha única (definida em Secrets, nunca no código)."""
import hmac
import time

import streamlit as st

from brand import AZUL, DOURADO, LOGO_B64

MAX_TENTATIVAS = 5
BLOQUEIO_SEG = 300
CHAVES_SENHA = ("SENHA_ACESSO", "app_password", "password")


def _senha_configurada():
    try:
        for k in CHAVES_SENHA:
            if st.secrets.get(k):
                return str(st.secrets[k])
    except Exception:  # noqa: BLE001  (sem secrets.toml)
        pass
    return None


def _css_login():
    st.markdown(f"""
    <style>
    header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {{display:none;}}
    .stApp {{background:{AZUL};}}
    .block-container {{max-width:440px; padding-top:12vh;}}
    .login-topo {{text-align:center; padding-bottom:1.2rem; border-bottom:3px solid {DOURADO}; margin-bottom:1.6rem;}}
    .login-topo img {{width:210px;}}
    .login-topo h1 a {{display:none;}}
    .login-topo h1 {{color:#FFFFFF; text-align:center; padding:0; font-size:1.45rem; font-weight:600; margin:1.1rem 0 .2rem;}}
    .login-topo p {{color:#B9CBE0; margin:0; font-size:.95rem;}}
    .stApp label p {{color:#E8EEF6 !important;}}
    .stButton button {{background:#FFFFFF; color:{AZUL}; border:0; font-weight:600;}}
    .stButton button:hover {{background:{DOURADO}; color:{AZUL};}}
    .login-rodape {{text-align:center; color:#8FA6C2; font-size:.8rem; margin-top:2rem;}}
    </style>
    """, unsafe_allow_html=True)


def _cabecalho():
    st.markdown(f"""
    <div class="login-topo">
      <img src="data:image/png;base64,{LOGO_B64}" alt="Dutra Bitencourt">
      <h1>Núcleo Bancário</h1>
      <p>Manual e painel de gestão</p>
    </div>
    """, unsafe_allow_html=True)


def exigir_login() -> None:
    """Interrompe o app até a senha correta ser informada."""
    if st.session_state.get("autenticado"):
        return

    _css_login()
    _cabecalho()
    senha = _senha_configurada()

    if not senha:
        st.error("Senha de acesso não configurada. Defina SENHA_ACESSO em Settings > Secrets.")
        st.stop()

    bloqueado_ate = st.session_state.get("bloqueado_ate", 0)
    if time.time() < bloqueado_ate:
        falta = int((bloqueado_ate - time.time()) / 60) + 1
        st.error(f"Acesso bloqueado após {MAX_TENTATIVAS} tentativas. Tente de novo em {falta} min.")
        st.stop()

    with st.form("login", border=False):
        tentativa = st.text_input("Senha de acesso", type="password", placeholder="Digite a senha do escritório")
        entrar = st.form_submit_button("Entrar", use_container_width=True)

    if entrar:
        if tentativa and hmac.compare_digest(tentativa, senha):
            st.session_state.autenticado = True
            st.session_state.pop("tentativas", None)
            st.rerun()
        n = st.session_state.get("tentativas", 0) + 1
        st.session_state.tentativas = n
        if n >= MAX_TENTATIVAS:
            st.session_state.bloqueado_ate = time.time() + BLOQUEIO_SEG
            st.session_state.tentativas = 0
            st.rerun()
        resta = MAX_TENTATIVAS - n
        st.error(f"Senha incorreta. {'Resta 1 tentativa' if resta == 1 else f'Restam {resta} tentativas'}.")

    st.markdown('<div class="login-rodape">Uso restrito à equipe Dutra Bitencourt.</div>', unsafe_allow_html=True)
    st.stop()


def botao_sair():
    if st.button("Sair", icon=":material/logout:", width="stretch"):
        for k in ("autenticado", "tentativas", "bloqueado_ate"):
            st.session_state.pop(k, None)
        st.rerun()
