import io
import hashlib
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from scipy import stats
from core import read_data, demo, train_model, forecast
from imports import upload_widget
from editor import run_editor
from auth import login_gate
from ui import apply_style, account_bar, navigation, plot_chart

st.set_page_config(page_title='DataScope — Analyse de données', page_icon='📊', layout='wide')
apply_style(st.session_state.get('display_theme', 'Light'))
username = login_gate(st)
account_bar(username)
st.markdown('<div class="hero"><span class="badge">Workspace analytique · Python</span><h1>DataScope Studio</h1><p>Explorez les données. Évaluez les hypothèses. Anticipez les tendances.</p></div>', unsafe_allow_html=True)
page = navigation()
with st.sidebar:
    st.header('📁 Espace de données')
    sep = st.selectbox('Séparateur texte', [',', ';', '\t', '|'])
    encoding = st.selectbox('Encodage texte', ['utf-8', 'utf-8-sig', 'latin-1'])
    try:
        up, imported, selection = upload_widget(st, 'Importer un fichier', 'source_upload', sep, encoding)
    except Exception as e:
        st.error(f'Import impossible : {e}')
        st.stop()
    st.caption('CSV · XLSX · TXT · TSV · PDF · HTML · JSON · Parquet — maximum 25 Mo.')
    st.info('Sans fichier : données synthétiques de démonstration. PDF : tableaux extractibles, sans OCR.')
    st.caption('Données en session · compte local authentifié')
try:
    source_id = hashlib.sha256(up.getvalue() + f'{sep}{encoding}{selection}'.encode()).hexdigest() if up else 'demo'
    if st.session_state.get('source_id') != source_id:
        st.session_state.df = imported if up else demo()
        st.session_state.source_id = source_id
        st.session_state.pop('trained', None)
        st.session_state.pop('join_preview', None)
    df = st.session_state.df
except Exception as e:
    st.error(f'Import impossible : {e}')
    st.stop()

def save_data(new):
    st.session_state.df = new.reset_index(drop=True)
    st.session_state.pop('trained', None)
    st.session_state.pop('join_preview', None)
    st.session_state.pop('code_result', None)
    st.rerun()

def download(data, name, label='Télécharger en CSV'):
    st.download_button(label, data.to_csv(index=False).encode('utf-8-sig'), name, 'text/csv')


a, b, c, d = st.columns(4)
a.metric('Lignes', f'{len(df):,}')
b.metric('Colonnes', len(df.columns))
c.metric('Cellules manquantes', int(df.isna().sum().sum()))
d.metric('Doublons', int(df.duplicated().sum()))
if df.empty or len(df.columns) == 0:
    st.warning('Le jeu de données est vide. Chargez un nouveau fichier.')
    st.stop()
nums = df.select_dtypes(include='number').columns.tolist()
cols = df.columns.tolist()
if page == 'Vue d’ensemble':
    st.subheader('Aperçu des données')
    st.dataframe(df.head(500), width="stretch")
    download(df, 'donnees.csv')
    st.subheader('Statistiques descriptives')
    st.dataframe(df.describe(include='all').T, width="stretch")
    quality = pd.DataFrame({'type': df.dtypes.astype(str), 'manquantes': df.isna().sum(), 'manquantes %': df.isna().mean()*100, 'valeurs distinctes': df.nunique()})
    st.subheader('Qualité des données')
    st.dataframe(quality, width="stretch")
    if nums:
        st.subheader('Valeurs atypiques potentielles (règle 1,5 × IQR)')
        out = {}
        for col in nums:
            q1, q3 = df[col].quantile([.25, .75]); iqr = q3-q1
            out[col] = int(((df[col] < q1-1.5*iqr) | (df[col] > q3+1.5*iqr)).sum())
        st.dataframe(pd.Series(out, name='observations signalées').to_frame())
        st.caption('Un signalement ne prouve pas une erreur : vérifier le contexte avant de supprimer.')
elif page == 'Préparation & jointures':
    st.subheader('Transformations persistantes dans la session')
    action = st.selectbox('Opération', ['Sélectionner les colonnes', 'Supprimer les doublons', 'Valeurs manquantes', 'Convertir un type', 'Renommer une colonne', 'Filtrer', 'Trier', 'Agrégation groupby', 'Tableau croisé pivot', 'Jointure', 'Concaténation'])
    try:
        if action == 'Sélectionner les colonnes':
            keep = st.multiselect('Colonnes à conserver', cols, default=cols)
            if st.button('Appliquer') and keep: save_data(df[keep])
        elif action == 'Supprimer les doublons':
            subset = st.multiselect('Clés (vide = toutes les colonnes)', cols)
            if st.button('Appliquer'): save_data(df.drop_duplicates(subset=subset or None))
        elif action == 'Valeurs manquantes':
            selected = st.multiselect('Colonnes', cols, default=cols)
            mode = st.selectbox('Méthode', ['Supprimer les lignes', 'Médiane (numérique)', 'Mode', 'Valeur constante'])
            value = st.text_input('Valeur constante', 'Inconnu') if mode == 'Valeur constante' else None
            st.warning('Pour la modélisation, préférez l’imputation intégrée au pipeline : une imputation sur tout le jeu avant le découpage peut biaiser l’évaluation.')
            if st.button('Appliquer') and selected:
                new = df.copy()
                if mode == 'Supprimer les lignes': new = new.dropna(subset=selected)
                else:
                    for col in selected:
                        if mode == 'Médiane (numérique)':
                            if col not in nums: continue
                            fill = new[col].median()
                        elif mode == 'Mode':
                            modes = new[col].mode()
                            if modes.empty: continue
                            fill = modes.iloc[0]
                        else: fill = float(value) if col in nums else value
                        new[col] = new[col].fillna(fill)
                save_data(new)
        elif action == 'Convertir un type':
            col = st.selectbox('Colonne', cols)
            kind = st.selectbox('Type', ['Numérique', 'Date', 'Texte'])
            if st.button('Appliquer'):
                new = df.copy()
                new[col] = pd.to_numeric(new[col], errors='coerce') if kind == 'Numérique' else pd.to_datetime(new[col], errors='coerce') if kind == 'Date' else new[col].astype('string')
                save_data(new)
        elif action == 'Renommer une colonne':
            col = st.selectbox('Colonne', cols); name = st.text_input('Nouveau nom')
            if st.button('Appliquer'):
                if not name.strip() or name in cols: raise ValueError('Choisir un nom non vide et unique.')
                save_data(df.rename(columns={col: name}))
        elif action == 'Filtrer':
            col = st.selectbox('Colonne', cols)
            if col in nums:
                low = st.number_input('Minimum', value=float(df[col].min()))
                high = st.number_input('Maximum', value=float(df[col].max()))
                mask = df[col].between(low, high)
            else:
                values = st.multiselect('Valeurs à conserver', df[col].dropna().unique().tolist())
                mask = df[col].isin(values)
            if st.button('Appliquer'): save_data(df[mask])
        elif action == 'Trier':
            selected = st.multiselect('Colonnes de tri', cols)
            ascending = st.checkbox('Croissant', True)
            if st.button('Appliquer') and selected: save_data(df.sort_values(selected, ascending=ascending))
        elif action in ['Agrégation groupby', 'Tableau croisé pivot']:
            keys = st.multiselect('Clés de regroupement', cols)
            value = st.selectbox('Mesure', nums) if nums else None
            agg = st.selectbox('Agrégation', ['sum', 'mean', 'median', 'count', 'min', 'max', 'std'])
            pivot = st.selectbox('Colonne de pivot', cols) if action == 'Tableau croisé pivot' else None
            if keys and value:
                result = df.pivot_table(index=keys, columns=pivot, values=value, aggfunc=agg).reset_index() if pivot else df.groupby(keys, dropna=False)[value].agg(agg).reset_index()
                st.dataframe(result); download(result, 'agregation.csv')
        else:
            other, right, _ = upload_widget(st, 'Deuxième fichier', 'join_upload', sep, encoding)
            if other:
                st.dataframe(right.head())
                if action == 'Jointure':
                    left_keys = st.multiselect('Clés à gauche', cols)
                    right_keys = st.multiselect('Clés à droite (même ordre)', right.columns.tolist())
                    how = st.selectbox('Type de jointure', ['left', 'inner', 'right', 'outer'])
                    validation = st.selectbox('Cardinalité attendue', ['one_to_one', 'many_to_one', 'one_to_many', 'many_to_many'])
                    st.caption('Les clés nulles peuvent se rejoindre ; une jointure plusieurs-à-plusieurs peut multiplier les lignes.')
                    if st.button('Prévisualiser la jointure'):
                        if not left_keys or len(left_keys) != len(right_keys): raise ValueError('Choisir le même nombre de clés de chaque côté.')
                        result = df.merge(right, left_on=left_keys, right_on=right_keys, how=how, validate=validation, suffixes=('', '_droite'), indicator=True)
                        st.session_state.join_preview = (source_id, result)
                    preview = st.session_state.get('join_preview')
                    if preview and preview[0] == source_id:
                        st.dataframe(preview[1].head(500)); st.write(f'{len(preview[1])} lignes après jointure')
                        download(preview[1], 'jointure.csv')
                        if st.button('Utiliser cette prévisualisation comme données actives'): save_data(preview[1])
                else:
                    if st.button('Concaténer les lignes'): save_data(pd.concat([df, right], ignore_index=True, sort=False))
    except Exception as e: st.error(f'Transformation impossible : {e}')
    st.dataframe(df.head(100), width="stretch")
    if st.button('Réinitialiser les données depuis la source'):
        st.session_state.pop('source_id', None); st.rerun()
elif page == 'Tableaux de bord':
    kind = st.selectbox('Visualisation', ['Histogramme', 'Boîte à moustaches', 'Nuage de points', 'Barres agrégées', 'Courbe', 'Corrélations', 'Matplotlib'])
    try:
        if kind == 'Corrélations':
            if len(nums) < 2: st.info('Deux colonnes numériques sont nécessaires.')
            else:
                method = st.selectbox('Méthode', ['pearson', 'spearman'])
                plot_chart(px.imshow(df[nums].corr(method=method), zmin=-1, zmax=1, color_continuous_scale='RdBu_r'), width="stretch")
                st.caption('Une corrélation ne démontre pas une causalité.')
        elif kind == 'Matplotlib':
            if nums:
                x = st.selectbox('Mesure', nums)
                fig, ax = plt.subplots(figsize=(10, 4));
                if st.session_state.get('display_theme') == 'Dark':
                    fig.set_facecolor('#152239'); ax.set_facecolor('#152239'); ax.tick_params(colors='#e7eefb')
                    ax.xaxis.label.set_color('#e7eefb'); ax.yaxis.label.set_color('#e7eefb'); ax.title.set_color('#e7eefb')
                ax.hist(df[x].dropna(), bins=30, color='#3874e8'); ax.set(xlabel=x, ylabel='Effectif', title=f'Distribution de {x}')
                st.pyplot(fig)
                buf = io.BytesIO(); fig.savefig(buf, format='png', bbox_inches='tight'); plt.close(fig)
                st.download_button('Exporter le graphique PNG', buf.getvalue(), 'graphique.png', 'image/png')
        else:
            x = st.selectbox('Axe X', cols)
            color = st.selectbox('Couleur', ['Aucune'] + cols); color = None if color == 'Aucune' else color
            if kind == 'Histogramme': fig = px.histogram(df, x=x, color=color)
            else:
                if not nums: raise ValueError('Une colonne numérique est nécessaire.')
                y = st.selectbox('Axe Y', nums)
                if kind == 'Boîte à moustaches': fig = px.box(df, x=x, y=y, color=color)
                elif kind == 'Nuage de points': fig = px.scatter(df, x=x, y=y, color=color, opacity=.65)
                elif kind == 'Courbe': fig = px.line(df.sort_values(x), x=x, y=y, color=color)
                else:
                    agg = st.selectbox('Agrégation', ['sum', 'mean', 'median', 'count'])
                    keys = list(dict.fromkeys([x] + ([color] if color else [])))
                    grouped = df.groupby(keys, dropna=False)[y].agg(agg).reset_index()
                    fig = px.bar(grouped, x=x, y=y, color=color)
            plot_chart(fig, width="stretch")
    except Exception as e: st.error(f'Graphique impossible : {e}')
elif page == 'Tests statistiques':
    st.warning('Analyses exploratoires : les hypothèses doivent être vérifiées. Une p-value ne mesure ni la causalité ni la taille d’effet. Si vous multipliez les tests, corrigez les comparaisons multiples.')
    test = st.selectbox('Test', ['Welch : deux moyennes', 'Mann–Whitney : deux distributions', 'ANOVA : plusieurs moyennes', 'Kruskal–Wallis : plusieurs groupes', 'Corrélation Pearson', 'Corrélation Spearman', 'Khi-deux : indépendance'])
    alpha = st.number_input('Seuil α', .001, .2, .05, .001)
    try:
        effect = None
        if test.startswith('Corrélation'):
            if len(nums) < 2: raise ValueError('Deux colonnes numériques nécessaires.')
            x = st.selectbox('Variable 1', nums); y = st.selectbox('Variable 2', [n for n in nums if n != x])
            pair = df[[x, y]].replace([np.inf, -np.inf], np.nan).dropna()
            if len(pair) < 3: raise ValueError('Au moins trois paires complètes nécessaires.')
            result = stats.pearsonr(pair[x], pair[y]) if test.endswith('Pearson') else stats.spearmanr(pair[x], pair[y])
            hypothesis = 'Absence de corrélation (linéaire pour Pearson, de rang pour Spearman).'
            st.caption('Pearson : relation linéaire et conditions d’inférence adaptées ; Spearman : association monotone. Observations indépendantes requises.')
            effect = ('Coefficient de corrélation', float(result.statistic))
        elif test.startswith('Khi'):
            x = st.selectbox('Variable catégorielle 1', cols); y = st.selectbox('Variable catégorielle 2', [n for n in cols if n != x])
            table = pd.crosstab(df[x], df[y]); st.dataframe(table)
            if min(table.shape) < 2: raise ValueError('Au moins deux modalités par variable.')
            result = stats.chi2_contingency(table)
            hypothesis = 'Les deux variables sont indépendantes.'
            if (result.expected_freq < 5).any(): st.warning('Certains effectifs attendus sont < 5 : approximation potentiellement peu fiable. Envisager Fisher pour un tableau 2 × 2.')
            effect = ('V de Cramér (non corrigé)', float(np.sqrt(result.statistic / (table.to_numpy().sum() * (min(table.shape)-1)))))
        else:
            if not nums: raise ValueError('Une mesure numérique nécessaire.')
            measure = st.selectbox('Mesure numérique', nums)
            group = st.selectbox('Colonne de groupe', [n for n in cols if n != measure])
            levels = st.multiselect('Groupes à comparer', df[group].dropna().unique().tolist())
            samples = [df.loc[df[group] == level, measure].replace([np.inf, -np.inf], np.nan).dropna().to_numpy() for level in levels]
            if any(len(s) < 2 for s in samples): raise ValueError('Deux observations minimum par groupe.')
            if test.startswith(('Welch', 'Mann')) and len(samples) != 2: raise ValueError('Sélectionnez exactement deux groupes.')
            if len(samples) < 2: raise ValueError('Sélectionnez au moins deux groupes.')
            st.dataframe(pd.DataFrame({'groupe': levels, 'n': [len(s) for s in samples], 'moyenne': [np.mean(s) for s in samples], 'médiane': [np.median(s) for s in samples]}))
            if test.startswith('Welch'):
                result = stats.ttest_ind(*samples, equal_var=False)
                hypothesis = 'Les moyennes des deux populations sont égales.'
                effect = ('Différence de moyennes (groupe 1 − groupe 2)', float(np.mean(samples[0])-np.mean(samples[1])))
                st.caption('Groupes indépendants ; normalité approximative des moyennes. Ne convient pas aux données appariées.')
            elif test.startswith('Mann'):
                result = stats.mannwhitneyu(*samples, alternative='two-sided'); hypothesis = 'Les deux distributions sont identiques.'
                st.caption('Groupes indépendants. Ne se réduit à un test de médianes que sous des hypothèses de forme supplémentaires.')
            elif test.startswith('ANOVA'):
                result = stats.f_oneway(*samples); hypothesis = 'Toutes les moyennes de population sont égales.'
                st.caption('Indépendance, normalité des résidus et homogénéité des variances requises.')
            else:
                result = stats.kruskal(*samples); hypothesis = 'Les distributions des groupes sont identiques.'
                st.caption('Groupes indépendants ; une interprétation en termes de position suppose des formes comparables.')
        if st.button('Calculer le test'):
            p = float(result.pvalue)
            if not np.isfinite(p): raise ValueError('Résultat indéfini : vérifier les données constantes ou dégénérées.')
            st.write('**Hypothèse nulle H₀ :**', hypothesis)
            st.json({'statistique': float(result.statistic), 'p_value': p, 'alpha': alpha})
            if effect: st.metric(effect[0], f'{effect[1]:.4g}')
            st.info('Rejet de H₀ au seuil choisi.' if p < alpha else 'H₀ non rejetée : cela ne prouve pas qu’elle est vraie.')
    except Exception as e: st.info(f'Configuration du test : {e}')
elif page == 'Prédictions':
    st.subheader('Régression et classification')
    st.warning('Sélectionnez uniquement des variables disponibles au moment de la prédiction. Excluez les identifiants, les variables calculées depuis la cible et les informations futures. Pour des données datées, utilisez le module temporel.')
    task = st.selectbox('Objectif', ['Régression', 'Classification'])
    target = st.selectbox('Cible', cols)
    features = st.multiselect('Variables explicatives', [c for c in cols if c != target])
    algorithm = st.selectbox('Modèle', ['Forêt aléatoire', 'Modèle linéaire'])
    size = st.slider('Part réservée au test', .1, .4, .2, .05)
    config = (task, target, tuple(features), algorithm, size)
    if st.button('Entraîner et évaluer', type='primary'):
        try:
            if not features: raise ValueError('Choisir au moins une variable explicative.')
            with st.spinner('Entraînement en cours…'):
                result = train_model(df, features, target, task, algorithm, size)
                st.session_state.trained = (config, result)
        except Exception as e: st.error(f'Entraînement impossible : {e}')
    trained = st.session_state.get('trained')
    if trained and trained[0] == config:
        result = trained[1]
        st.write('**Évaluation sur le jeu de test séparé (20 % par défaut)**')
        st.json(result['metrics']); st.json(result['baseline'])
        st.dataframe(result['results']); download(result['results'], 'evaluation.csv')
        if result['report'] is not None: st.dataframe(result['report'])
        else: plot_chart(px.scatter(result['results'], x='réel', y='prédit'), width="stretch")
        st.caption('Imputation et encodage ajustés sur l’entraînement uniquement. Le modèle est conservé en mémoire dans cette session ; ne pas réutiliser ce test pour optimiser indéfiniment le modèle.')
        try:
            new, incoming, _ = upload_widget(st, 'Nouvelles observations à prédire', 'predict_upload', sep, encoding)
        except Exception as e:
            st.error(f'Import impossible : {e}')
            new = None
        if new:
            try:
                missing = set(result['features']) - set(incoming.columns)
                if missing: raise ValueError(f'Colonnes absentes : {sorted(missing)}')
                X = incoming[result['features']].copy()
                for col in result['nums']: X[col] = pd.to_numeric(X[col], errors='coerce').replace([np.inf, -np.inf], np.nan)
                for col in result['cats']: X[col] = X[col].map(lambda v: str(v) if pd.notna(v) else np.nan)
                incoming['prediction'] = result['model'].predict(X)
                st.dataframe(incoming); download(incoming, 'predictions.csv')
            except Exception as e: st.error(f'Prédiction impossible : {e}')
elif page == 'Prévisions temporelles':
    st.subheader('Prévision autorégressive exploratoire')
    st.caption('Régression Ridge sur les valeurs retardées, comparaison à la dernière valeur connue, puis prévision récursive. Pas d’intervalle de confiance ni de garantie de performance future.')
    try:
        if not nums: raise ValueError('Une mesure numérique nécessaire.')
        date = st.selectbox('Colonne date', cols)
        value = st.selectbox('Mesure', [c for c in nums if c != date])
        freq_label = st.selectbox('Fréquence', ['Jour', 'Semaine', 'Mois'])
        frequency = {'Jour': 'D', 'Semaine': 'W', 'Mois': 'MS'}[freq_label]
        aggregation = st.selectbox('Agrégation par période', ['sum', 'mean'])
        horizon = st.number_input('Horizon en périodes', 1, 90, 14)
        lags = st.number_input('Nombre de retards', 1, 60, 7)
        if st.button('Évaluer et prévoir', type='primary'):
            series, future, metrics = forecast(df, date, value, frequency, aggregation, int(horizon), int(lags))
            st.json(metrics)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=series.index, y=series.values, name='Historique'))
            fig.add_trace(go.Scatter(x=future['date'], y=future['prévision'], name='Prévision', line={'dash': 'dash'}))
            plot_chart(fig, width="stretch")
            st.dataframe(future); download(future, 'previsions.csv')
            st.warning('Le test est chronologique, à un pas avec les retards réellement observés. Il ne mesure pas directement l’erreur récursive à tout l’horizon. La dernière période historique doit être complète.')
    except Exception as e: st.error(f'Prévision impossible : {e}')

elif page == 'Studio de code':
    st.subheader('⌨ Studio pandas')
    st.caption('Éditeur multiligne : sous-ensemble Python/pandas interprété, pas un terminal Python complet. Aucun import, accès fichier/réseau, boucle ou fonction utilisateur.')
    st.warning('Pas de quotas CPU/mémoire : réserver ce prototype à un usage local de confiance. Les opérations coûteuses peuvent bloquer la session.')
    examples = {
        'Aperçu': 'result = df.head(20)',
        'Statistiques': 'result = df.describe(include="all").T',
        'Manquantes': 'result = df.isna().sum()',
        'Dédoublonnage': 'result = df.drop_duplicates()',
        'Agrégation démonstration': 'result = df.groupby("segment")["ventes"].mean().reset_index()',
        'Filtre démonstration': 'result = df[df["budget"] > 1000].head(50)',
    }
    example = st.selectbox('Exemple de code', list(examples))
    code = st.text_area('Code pandas', value=examples[example], height=240, key='editor_'+example)
    left, right = st.columns(2)
    with left:
        execute = st.button('▶ Exécuter', type='primary')
    with right:
        st.download_button('Exporter le code Python', code.encode(), 'transformation.py', 'text/x-python')
    with st.expander('Méthodes autorisées et règles'):
        from editor import METHODS
        st.code(', '.join(sorted(METHODS)))
        st.write('Variable initiale : df. Résultat : result. Affectations simples, indexation, comparaisons, calculs arithmétiques et filtres & / | autorisés. Exemples métier valables uniquement avec les colonnes correspondantes.')
    if execute:
        try:
            result = run_editor(code, df)
            st.session_state.code_result = (source_id, code, result)
        except Exception as e:
            st.session_state.pop('code_result', None)
            st.error(f'Code non exécuté : {e}')
    saved = st.session_state.get('code_result')
    if saved and saved[0] == source_id and saved[1] == code:
        result = saved[2]
        st.success('Transformation terminée. Les données actives restent inchangées tant que vous ne cliquez pas sur Appliquer.')
        if isinstance(result, (pd.DataFrame, pd.Series)):
            st.dataframe(result, width='stretch')
            exported = result.to_frame() if isinstance(result, pd.Series) else result
            st.download_button('Exporter le résultat CSV', exported.to_csv(index=True).encode('utf-8-sig'), 'resultat_code.csv', 'text/csv')
            if isinstance(result, pd.DataFrame) and not result.empty and result.columns.is_unique:
                if st.button('Appliquer ce DataFrame aux données actives'): save_data(result)
        else: st.write(result)
