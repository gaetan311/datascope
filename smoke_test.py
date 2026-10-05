import numpy as np
from core import demo, read_data, train_model, forecast

df = demo()
loaded = read_data(df.to_csv(index=False).encode(), 'demo.csv')
assert len(loaded) == 365
joined = df.merge(df[['client_id']].drop_duplicates(), on='client_id', validate='many_to_one')
assert len(joined) == len(df)
for task, target in [('Régression', 'ventes'), ('Classification', 'objectif_atteint')]:
    for algorithm in ['Forêt aléatoire', 'Modèle linéaire']:
        result = train_model(df, ['budget', 'segment'], target, task, algorithm)
        assert all(np.isfinite(v) for v in result['metrics'].values())
        print(task, algorithm, result['metrics'])
series, future, metrics = forecast(df, 'date', 'ventes', 'D', 'sum', 14, 7)
assert len(future) == 14 and future['prévision'].notna().all()
print('Prévision', metrics)
print('Tous les tests métier ont réussi.')
