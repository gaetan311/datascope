import streamlit as st
import plotly.io as pio
import matplotlib.pyplot as plt
from auth import set_theme, clear_session


def apply_style(theme):
    dark = theme == 'Dark'
    colors = {'bg':'#0c1424' if dark else '#f3f6fc', 'panel':'#152239' if dark else '#ffffff', 'text':'#e7eefb' if dark else '#172640', 'muted':'#a8bad4' if dark else '#536882', 'border':'#2c405b' if dark else '#dce5f1', 'input':'#1a2c46' if dark else '#f6f8fc'}
    css = '''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root {--bg:BG;--panel:PANEL;--fg:TEXT;--muted:MUTED;--border:BORDER;--input:INPUT;}
html,body,[data-testid="stAppViewContainer"],.stApp {background:var(--bg);color:var(--fg);font-family:'Inter',sans-serif}
.block-container {max-width:1500px;padding-top:1.5rem}
[data-testid="stSidebar"],[data-testid="stHeader"] {background:var(--panel)}
h1,h2,h3,h4 {font-family:'Manrope','Inter',sans-serif!important;color:var(--fg)!important}
p,label,[data-testid="stMarkdownContainer"], [data-testid="stMetricValue"], [data-testid="stWidgetLabel"] {color:var(--fg)}
[data-testid="stCaptionContainer"] p {color:var(--muted)}
.hero {background:linear-gradient(115deg,#172a53,#14677a);border-radius:24px;padding:30px;margin:18px 0 24px;box-shadow:0 12px 34px #00000022}
.hero h1 {color:white!important;font-size:2.4rem;margin:0}.hero p {color:#d5e6f7;margin:10px 0 0}
.badge {font-size:12px;letter-spacing:2px;color:#80efd4;text-transform:uppercase}
[data-testid="stMetric"] {background:var(--panel);border:1px solid var(--border);padding:18px;border-radius:16px}
.st-key-header_card {background:var(--panel);border:1px solid var(--border);border-radius:22px;padding:20px;box-shadow:0 5px 20px #00000012;transition:box-shadow .2s,border-color .2s}
.st-key-header_card:hover {border-color:#3ba9ae;box-shadow:0 10px 32px #17667b25}
.st-key-header_card .stButton button {width:100%;min-height:72px;background:var(--input);color:var(--fg);border:1px solid var(--border);border-radius:16px;font-family:'Manrope',sans-serif;transition:transform .18s,box-shadow .18s,border-color .18s}
.st-key-header_card .stButton button:hover {transform:translateY(-4px);border-color:#2ab8ab;box-shadow:0 9px 20px #17667b30}
.st-key-header_card .stButton button:focus-visible {outline:3px solid #48c6b4;outline-offset:3px}
.st-key-header_card .stButton button[kind="primary"] {background:linear-gradient(120deg,#17667b,#217b88);color:white;border-color:#48b2ad}
.st-key-header_card button[kind="primary"] p {color:white}
input,textarea,[data-baseweb="select"]>div {background:var(--input)!important;color:var(--fg)!important;border-color:var(--border)!important}
[data-baseweb="popover"],[data-baseweb="menu"] {background:var(--panel)!important;color:var(--fg)!important}
[data-testid="stForm"],[data-testid="stExpander"] {border-color:var(--border)}
.stButton button,.stDownloadButton button {background:var(--panel);color:var(--fg);border-color:var(--border);border-radius:10px}
.stButton button[kind="primary"], [data-testid="stFormSubmitButton"] button {background:#17667b;color:white}
[data-testid="stFormSubmitButton"] button p {color:white}
pre,code {font-family:monospace!important}
@media(prefers-reduced-motion:reduce){.st-key-header_card,.st-key-header_card .stButton button{transition:none}.st-key-header_card .stButton button:hover{transform:none}}
@media(max-width:700px){.hero{padding:20px}.hero h1{font-size:1.8rem}.st-key-header_card{padding:12px}}
</style>'''
    for k,v in colors.items(): css = css.replace(k.upper(),v)
    st.markdown(css,unsafe_allow_html=True)



def theme_changed():
    set_theme(st.session_state.auth_user, st.session_state.display_theme)


def account_bar(username):
    with st.sidebar:
        st.subheader('👤 Mon compte')
        st.text(username)
        st.selectbox('Préférence d’affichage', ['Light','Dark'], key='display_theme', on_change=theme_changed)
        st.caption('Préférence enregistrée dans votre compte. Les tableaux natifs peuvent conserver certains styles Streamlit.')
        if st.button('Se déconnecter', key='logout'):
            clear_session(st); st.rerun()


def navigation():
    groups = {'Analyse':['Analyse descriptive','Analyse inférentielle','Préparation & jointures'], 'Tableaux de bord':['Tableaux de bord'], 'Prédiction':['Prédiction','Prévisions temporelles'], 'Studio code':['Studio de code']}
    icons = {'Analyse':'🔎','Tableaux de bord':'📊','Prédiction':'🔮','Studio code':'⌨'}
    st.session_state.setdefault('nav_group','Analyse')
    with st.container(key='header_card'):
        columns = st.columns(4)
        for col,(group,pages) in zip(columns,groups.items()):
            with col:
                if st.button(f'{icons[group]} {group}', key='nav_'+group, type='primary' if st.session_state.nav_group == group else 'secondary', width='stretch'):
                    st.session_state.nav_group = group
                    st.rerun()
        group = st.session_state.nav_group
        pages = groups[group]
        page = st.radio('Section', pages, horizontal=True, key='section_'+group, label_visibility='collapsed') if len(pages)>1 else pages[0]
    return {'Analyse descriptive':'Vue d’ensemble','Analyse inférentielle':'Tests statistiques','Prédiction':'Prédictions'}.get(page,page)


def plot_chart(fig, **kwargs):
    fig.update_layout(template='plotly_dark' if st.session_state.get('display_theme') == 'Dark' else 'plotly_white', font={'family':'Inter, sans-serif'})
    return st.plotly_chart(fig, **kwargs)
