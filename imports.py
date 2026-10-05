import io
from pathlib import Path
import pandas as pd
import streamlit as st

EXTENSIONS = ['csv', 'xlsx', 'txt', 'tsv', 'pdf', 'html', 'htm', 'json', 'parquet']

def normalize(df):
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [' / '.join(map(str, c)) for c in df.columns]
    seen = {}; names = []
    for i, c in enumerate(df.columns):
        base = str(c).strip() or f'colonne_{i+1}'
        count = seen.get(base, 0); seen[base] = count + 1
        candidate = base if count == 0 else f'{base}_{count+1}'
        while candidate in names: candidate += '_'
        names.append(candidate)
    df.columns = names
    return df


def load_tables(content, name, sep=',', encoding='utf-8', text_mode='Délimité'):
    if len(content) > 25 * 1024 * 1024:
        raise ValueError('Limite de cette interface : 25 Mo par fichier.')
    ext = Path(name).suffix.lower()
    stream = io.BytesIO(content)
    if ext == '.xlsx':
        tables = pd.read_excel(stream, sheet_name=None)
    elif ext in ['.html', '.htm']:
        tables = {f'Tableau {i+1}': d for i, d in enumerate(pd.read_html(io.StringIO(content.decode(encoding))))}
    elif ext == '.pdf':
        import pdfplumber
        tables = {}
        with pdfplumber.open(stream) as pdf:
            if len(pdf.pages) > 100: raise ValueError('Maximum 100 pages par PDF.')
            for p, page in enumerate(pdf.pages):
                for i, rows in enumerate(page.extract_tables()):
                    if len(rows) > 1:
                        tables[f'Page {p+1} · Tableau {i+1}'] = pd.DataFrame(rows[1:], columns=rows[0])
        if not tables: raise ValueError('Aucun tableau détecté. PDF scanné ou mise en page non reconnue : OCR/préparation externe nécessaire.')
    elif ext == '.json': tables = {'Données': pd.read_json(stream)}
    elif ext == '.parquet': tables = {'Données': pd.read_parquet(stream)}
    elif ext == '.txt' and text_mode == 'Texte libre':
        tables = {'Lignes de texte': pd.DataFrame({'texte': content.decode(encoding).splitlines()})}
    elif ext in ['.csv', '.txt', '.tsv']:
        tables = {'Données': pd.read_csv(stream, sep='\t' if ext == '.tsv' else sep, encoding=encoding)}
    else: raise ValueError('Extension non prise en charge.')
    return {k: normalize(v) for k, v in tables.items()}


def upload_widget(st, label, key, sep, encoding):
    uploaded = st.file_uploader(label, type=EXTENSIONS, key=key, max_upload_size=25)
    if not uploaded: return None, None, None
    mode = st.selectbox('Lecture du TXT', ['Délimité', 'Texte libre'], key=key+'_mode') if uploaded.name.lower().endswith('.txt') else 'Délimité'
    tables = load_tables(uploaded.getvalue(), uploaded.name, sep, encoding, mode)
    selected = st.selectbox('Feuille / tableau', list(tables), key=key+'_table')
    return uploaded, tables[selected], selected + mode
