import sqlite3
import os

db_path = os.path.join('backend', 'gestao_pneus.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    # Marcar todos que estão no estoque como 'recebimento pendente' para teste visual
    conn.execute("UPDATE gp_pneus SET recebido = 0 WHERE status = 'estoque'")
    conn.commit()
    conn.close()
    print("Database updated: All stock tires set to pending receipt.")
else:
    print(f"Database not found at {db_path}")
