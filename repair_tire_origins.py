import sqlite3
import os

db_path = os.path.join('backend', 'gestao_pneus.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    # Busca pneus na sucata que não tem filial_origem_id
    rows = conn.execute("""
        SELECT p.id, p.numero_fogo, p.filial_id
        FROM gp_pneus p 
        WHERE p.filial_origem_id IS NULL 
    """).fetchall()
    
    fixed_count = 0
    for p_id, n_fogo, f_id in rows:
        # Tenta descobrir a origem pelo histórico de movimentações
        mov = conn.execute("""
            SELECT filial_origem_id 
            FROM gp_movimentacoes 
            WHERE pneu_id = ? AND filial_origem_id IS NOT NULL AND filial_origem_id != ?
            ORDER BY criado_em DESC LIMIT 1
        """, (p_id, f_id)).fetchone()
        
        if mov:
            orig_id = mov[0]
            conn.execute("UPDATE gp_pneus SET filial_origem_id = ? WHERE id = ?", (orig_id, p_id))
            print(f"Fixed pneu {n_fogo}: origin set to {orig_id}")
            fixed_count += 1
            
    conn.commit()
    conn.close()
    print(f"Reparo concluído. {fixed_count} pneus atualizados.")
else:
    print(f"Banco não encontrado em {db_path}")
