import io
import pandas as pd
from core import demo
from imports import load_tables
from editor import run_editor
from streamlit.testing.v1 import AppTest

df = demo()
assert len(run_editor('result = df[df["budget"] > 1000].head(5)',df)) == 5
assert len(run_editor('result = df.groupby("segment")["ventes"].mean().reset_index()',df)) == 3
for code in ['import os', 'result = df.to_csv("bad.csv")', 'result = df.__class__', 'result = open("secret")']:
    try: run_editor(code,df)
    except ValueError: pass
    else: raise AssertionError('Code interdit accepté')
for ext in ['csv','txt','tsv','html','json','xlsx','parquet']:
    sample = df.head(5).drop(columns='date')
    if ext in ['csv','txt','tsv']: data = sample.to_csv(index=False,sep='\t' if ext == 'tsv' else ',').encode()
    elif ext == 'html': data = sample.to_html(index=False).encode()
    elif ext == 'json': data = sample.to_json().encode()
    else:
        buf=io.BytesIO()
        if ext=='xlsx': sample.to_excel(buf,index=False)
        else: sample.to_parquet(buf,index=False)
        data=buf.getvalue()
    assert len(next(iter(load_tables(data,'sample.'+ext).values()))) == 5
    print('Import OK',ext)
# PDF créé pour vérifier la détection des tableaux à bordures.
import matplotlib.pyplot as plt
buf=io.BytesIO(); fig, ax=plt.subplots(); ax.axis('off')
ax.table(cellText=[['A','1'],['B','2']], colLabels=['groupe','valeur'],loc='center')
fig.savefig(buf,format='pdf');plt.close(fig)
assert len(next(iter(load_tables(buf.getvalue(),'sample.pdf').values())))==2
print('Import OK pdf')
print('Tests import et interpréteur réussis. Interface authentifiée : python test_v3.py')
