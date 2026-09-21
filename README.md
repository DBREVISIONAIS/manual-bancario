# Núcleo Bancário: manual e painel

App Streamlit com o manual do Núcleo Bancário (script de vendas e procedimento interno) e o painel analítico das abas Registro, Prazos e Execução.

## Estrutura
auth.py             tela de login (senha em Secrets, bloqueio após 5 tentativas)
brand.py            logo e cores do escritório
assets/logo.png     logo da barra lateral
app.py              entrada, senha, carga dos dados, filtros e menu
data.py             leitura das 3 abas, limpeza, colunas derivadas e checagens de qualidade
views/dash.py       páginas do painel
views/manual.py     páginas do manual
manual_content.py   texto do manual (editar aqui para atualizar)

## Conexão com a planilha (conta de serviço, sem link público)
1. Google Cloud Console: crie um projeto, ative Google Sheets API e Google Drive API.
2. Crie uma conta de serviço e gere uma chave JSON.
3. Na planilha, compartilhe como Leitor com o e-mail da conta de serviço.
4. Copie .streamlit/secrets.toml.example (inclui SENHA_ACESSO, obrigatória) para Settings > Secrets do Streamlit Cloud e preencha com o JSON.
5. Ajuste [sheet.tabs] se os nomes das abas forem diferentes.

Alternativa sem conta de serviço: planilha auxiliar pública (ver abaixo). Sem nenhuma das duas, o app pede o .xlsx exportado da planilha (Arquivo > Fazer download > .xlsx).

## Deploy
Repositório privado no GitHub, app no Streamlit Cloud com Main file = app.py. Após mudar módulos, Reboot (não Rerun).

## Rodar local
pip install -r requirements.txt
streamlit run app.py

## Alternativa: planilha auxiliar com link público
Crie uma planilha nova só com três abas (Registro, Prazos, Execução), cada uma com
=IMPORTRANGE("ID_DA_PLANILHA_PRINCIPAL"; "Registro!A:Z") (ajuste nome da aba e intervalo) e autorize o acesso na primeira vez.
Compartilhe a auxiliar como "Qualquer pessoa com o link: Leitor" e coloque só o ID dela nos Secrets:

SENHA_ACESSO = "..."
[sheet]
id = "ID_DA_PLANILHA_AUXILIAR"

Nunca coloque aqui o ID da planilha principal: o link público expõe todas as abas.
