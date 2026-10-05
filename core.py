import io
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, f1_score, classification_report


def read_data(content, name, sep=',', encoding='utf-8', sheet=0):
    if name.lower().endswith('.xlsx'):
        df = pd.read_excel(io.BytesIO(content), sheet_name=sheet)
    else:
        df = pd.read_csv(io.BytesIO(content), sep=sep, encoding=encoding)
    df.columns = df.columns.map(str)
    if not df.columns.is_unique:
        raise ValueError('Les noms de colonnes doivent être uniques.')
    return df


def demo():
    rng = np.random.default_rng(42)
    n = 365
    budget = rng.uniform(100, 2000, n)
    segment = rng.choice(['Particuliers', 'Entreprises', 'Associations'], n)
    sales = 1500 + budget * 3 + 400 * (segment == 'Entreprises') + rng.normal(0, 350, n)
    return pd.DataFrame({'date': pd.date_range('2025-01-01', periods=n), 'client_id': rng.integers(1, 51, n), 'segment': segment, 'budget': budget.round(2), 'ventes': sales.round(2), 'objectif_atteint': np.where(sales > 4500, 'Oui', 'Non')})


def train_model(df, features, target, task, algorithm, test_size=.2):
    data = df[features + [target]].dropna(subset=[target]).copy()
    if len(data) < 20:
        raise ValueError('Il faut au moins 20 lignes avec une cible renseignée.')
    X, y = data[features].copy(), data[target]
    nums = X.select_dtypes(include='number').columns.tolist()
    cats = [c for c in features if c not in nums]
    X[nums] = X[nums].replace([np.inf, -np.inf], np.nan)
    for c in cats:
        X[c] = X[c].map(lambda v: str(v) if pd.notna(v) else np.nan)
    if task == 'Classification':
        y = y.astype(str)
        if y.nunique() < 2 or y.value_counts().min() < 2:
            raise ValueError('Au moins deux classes et deux observations par classe sont nécessaires.')
    else:
        y = pd.to_numeric(y, errors='raise')
        if not np.isfinite(y).all():
            raise ValueError('La cible doit contenir uniquement des valeurs numériques finies.')
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y if task == 'Classification' else None)
    transforms = []
    if nums:
        transforms.append(('num', Pipeline([('impute', SimpleImputer(strategy='median', keep_empty_features=True)), ('scale', StandardScaler())]), nums))
    if cats:
        transforms.append(('cat', Pipeline([('impute', SimpleImputer(strategy='most_frequent', keep_empty_features=True)), ('encode', OneHotEncoder(handle_unknown='ignore'))]), cats))
    if task == 'Régression':
        estimator = RandomForestRegressor(n_estimators=150, min_samples_leaf=2, random_state=42, n_jobs=-1) if algorithm == 'Forêt aléatoire' else LinearRegression()
    else:
        estimator = RandomForestClassifier(n_estimators=150, min_samples_leaf=2, random_state=42, n_jobs=-1) if algorithm == 'Forêt aléatoire' else LogisticRegression(max_iter=2000)
    model = Pipeline([('prep', ColumnTransformer(transforms)), ('model', estimator)])
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    if task == 'Régression':
        metrics = {'MAE': mean_absolute_error(yte, pred), 'RMSE': np.sqrt(mean_squared_error(yte, pred)), 'R²': r2_score(yte, pred)}
        baseline = {'MAE référence (moyenne entraînement)': mean_absolute_error(yte, np.repeat(ytr.mean(), len(yte)))}
        report = None
    else:
        metrics = {'Exactitude': accuracy_score(yte, pred), 'F1 pondéré': f1_score(yte, pred, average='weighted', zero_division=0)}
        baseline = {'Exactitude référence (classe majoritaire)': accuracy_score(yte, np.repeat(ytr.mode().iloc[0], len(yte)))}
        report = pd.DataFrame(classification_report(yte, pred, output_dict=True, zero_division=0)).T
    return {'model': model, 'features': features, 'nums': nums, 'cats': cats, 'metrics': metrics, 'baseline': baseline, 'report': report, 'results': pd.DataFrame({'réel': yte, 'prédit': pred}), 'task': task, 'target': target}


def forecast(df, date, value, frequency, aggregation, horizon, lags):
    d = df[[date, value]].copy()
    d[date] = pd.to_datetime(d[date], errors='coerce')
    d[value] = pd.to_numeric(d[value], errors='coerce').replace([np.inf, -np.inf], np.nan)
    d = d.dropna().set_index(date).sort_index()
    series = getattr(d[value].resample(frequency), aggregation)()
    if aggregation == 'sum':
        series = d[value].resample(frequency).sum(min_count=1)
    if series.isna().any():
        raise ValueError('Périodes manquantes : préparez une série régulière sans valeurs manquantes.')
    values = series.to_numpy()
    if len(values) < max(30, 3 * lags + 10):
        raise ValueError('Historique trop court pour ce nombre de retards.')
    X = np.array([values[i-lags:i] for i in range(lags, len(values))])
    y = values[lags:]
    cut = int(len(y) * .8)
    model = Ridge(alpha=1.0).fit(X[:cut], y[:cut])
    pred = model.predict(X[cut:])
    metrics = {'MAE test chronologique (un pas)': mean_absolute_error(y[cut:], pred), 'MAE naïve (dernière valeur)': mean_absolute_error(y[cut:], X[cut:, -1])}
    model.fit(X, y)
    history = list(values)
    future = []
    for _ in range(horizon):
        p = float(model.predict(np.array(history[-lags:]).reshape(1, -1))[0])
        future.append(p)
        history.append(p)
    dates = pd.date_range(series.index[-1], periods=horizon + 1, freq=frequency)[1:]
    return series, pd.DataFrame({'date': dates, 'prévision': future}), metrics
