"""Interpréteur d'un sous-ensemble pandas, sans exec/eval/import ni accès système.
Ce n'est pas un bac à sable de sécurité avec quotas CPU/mémoire.
"""
import ast
import operator
import pandas as pd
from pandas.core.groupby.generic import DataFrameGroupBy, SeriesGroupBy

METHODS = {'head', 'tail', 'describe', 'dropna', 'fillna', 'drop_duplicates', 'sort_values', 'groupby', 'sum', 'mean', 'median', 'count', 'min', 'max', 'std', 'reset_index', 'rename', 'astype', 'round', 'value_counts', 'nunique', 'isna', 'notna', 'corr', 'pivot_table', 'copy', 'abs', 'between', 'isin'}
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.BitAnd: operator.and_, ast.BitOr: operator.or_}
CMP = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Gt: operator.gt, ast.GtE: operator.ge, ast.Lt: operator.lt, ast.LtE: operator.le}
TYPES = (pd.DataFrame, pd.Series, DataFrameGroupBy, SeriesGroupBy)

def run_editor(code, df):
    if len(code) > 12000: raise ValueError('Code limité à 12 000 caractères.')
    env = {'df': df.copy()}
    def value(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (str, int, float, bool, type(None))): return n.value
        if isinstance(n, ast.Name) and n.id in env: return env[n.id]
        if isinstance(n, (ast.List, ast.Tuple)): return [value(x) for x in n.elts]
        if isinstance(n, ast.Dict): return {value(k): value(v) for k, v in zip(n.keys, n.values)}
        if isinstance(n, ast.Slice): return slice(value(n.lower) if n.lower else None, value(n.upper) if n.upper else None, value(n.step) if n.step else None)
        if isinstance(n, ast.Subscript):
            obj = value(n.value)
            if not isinstance(obj, TYPES): raise ValueError('Indexation réservée aux objets pandas.')
            return obj[value(n.slice)]
        if isinstance(n, ast.Attribute) and n.attr in {'T', 'shape', 'columns', 'dtypes'}:
            obj = value(n.value)
            if not isinstance(obj, (pd.DataFrame, pd.Series)): raise ValueError('Attribut non autorisé.')
            return getattr(obj, n.attr)
        if isinstance(n, ast.BinOp) and type(n.op) in OPS: return OPS[type(n.op)](value(n.left), value(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.Invert)): return -value(n.operand) if isinstance(n.op, ast.USub) else ~value(n.operand)
        if isinstance(n, ast.Compare) and len(n.ops) == 1 and type(n.ops[0]) in CMP: return CMP[type(n.ops[0])](value(n.left), value(n.comparators[0]))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in METHODS:
            obj = value(n.func.value)
            if not isinstance(obj, TYPES): raise ValueError('Appels réservés aux objets pandas.')
            kwargs = {}
            for k in n.keywords:
                if k.arg is None or k.arg.startswith('_'): raise ValueError('Argument interdit.')
                kwargs[k.arg] = value(k.value)
            return getattr(obj, n.func.attr)(*[value(a) for a in n.args], **kwargs)
        raise ValueError(f'Syntaxe non prise en charge : {type(n).__name__}. Imports, fonctions, boucles et accès système interdits.')
    tree = ast.parse(code)
    if len(list(ast.walk(tree))) > 600: raise ValueError('Expression trop complexe.')
    last = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name.startswith('_'): raise ValueError('Nom interdit.')
            last = value(node.value); env[name] = last
        elif isinstance(node, ast.Expr): last = value(node.value)
        else: raise ValueError('Seules les affectations simples et expressions sont acceptées.')
    return env.get('result', last)
