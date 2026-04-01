import re

with open("routers/pneus.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update _apply_filters
new_apply = """def _apply_filters(
    df: pd.DataFrame,
    filial: Optional[str] = None,
    marca: Optional[str] = None,
    fornecedor: Optional[str] = None,
    eixo: Optional[str] = None,
    medida: Optional[str] = None,
    estado_pneu: Optional[str] = None,
    ano: Optional[str] = None,
) -> pd.DataFrame:
    df = df.copy()
    if filial:
        df = df[df["filial"] == filial]
    if marca:
        df = df[df["marca"] == marca]
    if fornecedor:
        df = df[df["fornecedor"] == fornecedor]
    if eixo:
        df = df[df["eixo"] == eixo]
    if medida:
        df = df[df["medida"] == medida]
    if estado_pneu:
        df = df[df["estado_pneu"] == estado_pneu]
    if ano:
        try:
            df = df[df["ano"] == float(ano)]
        except:
            pass
    return df"""

code = re.sub(r'def _apply_filters\(.*?return df', new_apply, code, flags=re.DOTALL)

# 2. Update get_filtros
def update_get_filtros(match):
    return match.group(0).replace('"meses": _clean_series(df["mes"]),', '"meses": _clean_series(df["mes"]),\n        "anos": _clean_series(df["ano"]),')
code = re.sub(r'return \{.*?"estados_pneu".*?\}', update_get_filtros, code, flags=re.DOTALL)

# 3. Inject ano into endpoint signatures
endpoints = ['get_kpis', 'get_tabela', 'por_filial', 'por_marca', 'por_fornecedor', 'por_eixo', 'por_medida', 'por_estado', 'por_tipo', 'timeline', 'top_caros', 'por_placa']

for ep in endpoints:
    # find definition
    pat = r'(def ' + ep + r'\()(.*?)(:\n.*?)df = _apply_filters\((.*?)\)'
    
    def repl(m):
        args = m.group(2)
        if 'ano:' not in args:
            if args.strip() == '':
                args = 'ano: Optional[str] = Query(default=None)'
            else:
                if not args.strip().endswith(','):
                    args = args + ','
                args = args + '\n    ano: Optional[str] = Query(default=None),'
        
        apply_args = m.group(4)
        if 'ano=' not in apply_args:
            apply_args = apply_args + ', ano=ano'
            
        return 'def ' + ep + '(' + args + m.group(3) + 'df = _apply_filters(' + apply_args + ')'
    
    code = re.sub(pat, repl, code, flags=re.DOTALL)

# some endpoints like por_estado, timeline have no _apply_filters currently if they were returning earlier.
# let's manually add _apply_filters to timeline
timeline_pat = r'(def timeline\()(.*?\):.*?)(df = get_pneus_df\(\)\n    if df\.empty:\n        return \[\])'
timeline_repl = r'def timeline(ano: Optional[str] = Query(default=None), filial: Optional[str] = Query(default=None), marca: Optional[str] = Query(default=None), fornecedor: Optional[str] = Query(default=None)):\n    df = get_pneus_df()\n    if df.empty:\n        return []\n    df = _apply_filters(df, ano=ano, filial=filial, marca=marca, fornecedor=fornecedor)'
code = re.sub(timeline_pat, timeline_repl, code, flags=re.DOTALL)

por_estado_pat = r'(def por_estado\()(.*?\):.*?)(df = get_pneus_df\(\)\n    if df\.empty:\n        return \[\])'
por_estado_repl = r'def por_estado(ano: Optional[str] = Query(default=None), filial: Optional[str] = Query(default=None), marca: Optional[str] = Query(default=None), fornecedor: Optional[str] = Query(default=None)):\n    df = get_pneus_df()\n    if df.empty:\n        return []\n    df = _apply_filters(df, ano=ano, filial=filial, marca=marca, fornecedor=fornecedor)'
code = re.sub(por_estado_pat, por_estado_repl, code, flags=re.DOTALL)


with open("routers/pneus.py", "w", encoding="utf-8") as f:
    f.write(code)

print('Updated pneus.py')
