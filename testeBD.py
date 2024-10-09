# testeBD.py

import sqlite3
import pandas as pd

def quote_identifier(s):
    return '"' + s.replace('"', '""') + '"'

class DatabaseManager:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS TipoEnsaio (
                    id_tipo INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT UNIQUE
                )
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS Amostra (
                    id_amostra INTEGER PRIMARY KEY AUTOINCREMENT,
                    amostra TEXT UNIQUE
                )
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS Ensaio (
                    id_ensaio INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_tipo INTEGER,
                    id_amostra INTEGER,
                    id_metadados INTEGER,
                    NomeCompleto TEXT,
                    ensaio TEXT,
                    FOREIGN KEY (id_tipo) REFERENCES TipoEnsaio(id_tipo),
                    FOREIGN KEY (id_amostra) REFERENCES Amostra(id_amostra),
                    FOREIGN KEY (id_metadados) REFERENCES Metadados(id_metadados),
                    UNIQUE (id_amostra, ensaio)
                )
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS EnsaiosTriaxiais (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_ensaio INTEGER,
                    id_amostra INTEGER,
                    id_tipo INTEGER,
                    NomeCompleto TEXT,
                    FOREIGN KEY (id_ensaio) REFERENCES Ensaio(id_ensaio),
                    FOREIGN KEY (id_amostra) REFERENCES Amostra(id_amostra),
                    FOREIGN KEY (id_tipo) REFERENCES TipoEnsaio(id_tipo)
                )
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS Metadados (
                    id_metadados INTEGER PRIMARY KEY AUTOINCREMENT,
                    metadados TEXT,
                    valor_metadados TEXT,
                    NomeCompleto TEXT,
                    UNIQUE (NomeCompleto, metadados)
                )
            """)

    def insert_metadados(self, nome_completo, metadados):
        with self.conn:
            for key, value in metadados.items():
                if key:
                    value = value if value else 'N/A'
                    try:
                        self.conn.execute("INSERT INTO Metadados (metadados, valor_metadados, NomeCompleto) VALUES (?, ?, ?)", 
                                          (key, value, nome_completo))
                    except sqlite3.IntegrityError:
                        continue
            cursor = self.conn.execute("SELECT id_metadados FROM Metadados WHERE NomeCompleto = ?", (nome_completo,))
            return cursor.fetchone()[0]

    def insert_tipo_ensaio(self, tipo):
        tipo_formatado = '_'.join(tipo.split('_')[:2])
        with self.conn:
            cursor = self.conn.execute("INSERT OR IGNORE INTO TipoEnsaio (tipo) VALUES (?)", (tipo_formatado,))
            return cursor.lastrowid if cursor.lastrowid != 0 else self.get_tipo_id(tipo_formatado)

    def insert_amostra(self, amostra):
        with self.conn:
            cursor = self.conn.execute("INSERT OR IGNORE INTO Amostra (amostra) VALUES (?)", (amostra,))
            return cursor.lastrowid if cursor.lastrowid != 0 else self.get_amostra_id(amostra)

    def insert_ensaio(self, id_tipo, id_amostra, id_metadados, nome_completo):
        ensaio = nome_completo.split('_')[-1].split('.')[0]
        with self.conn:
            try:
                cursor = self.conn.execute("INSERT INTO Ensaio (id_tipo, id_amostra, id_metadados, NomeCompleto, ensaio) VALUES (?, ?, ?, ?, ?)", 
                                           (id_tipo, id_amostra, id_metadados, nome_completo, ensaio))
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                print(f"Ensaio '{ensaio}' já existe para a amostra '{id_amostra}'.")
                return None

    def insert_ensaios_triaxiais(self, id_ensaio, id_amostra, id_tipo, nome_completo, data):
        with self.conn:
            existing_columns = self.get_existing_columns('EnsaiosTriaxiais')
            new_columns = [col for col in data.keys() if col not in existing_columns]
            for col in new_columns:
                col_quoted = quote_identifier(col)
                self.conn.execute(f"ALTER TABLE EnsaiosTriaxiais ADD COLUMN {col_quoted} TEXT")

            for i in range(len(data['stage_no'])):
                row_data = {key: (data[key][i] if data[key][i] is not None else 0) for key in data.keys()}
                placeholders = ", ".join(["?"] * len(row_data))
                columns = ", ".join([quote_identifier(key) for key in row_data.keys()])
                self.conn.execute(
                    f"INSERT INTO EnsaiosTriaxiais (id_ensaio, id_amostra, id_tipo, NomeCompleto, {columns}) "
                    f"VALUES (?, ?, ?, ?, {placeholders})",
                    (id_ensaio, id_amostra, id_tipo, nome_completo, *row_data.values())
                )

    def get_existing_columns(self, table_name):
        cursor = self.conn.execute(f"PRAGMA table_info({table_name})")
        return [col[1] for col in cursor.fetchall()]

    def get_tipo_id(self, tipo):
        cursor = self.conn.execute("SELECT id_tipo FROM TipoEnsaio WHERE tipo = ?", (tipo,))
        return cursor.fetchone()[0]

    def get_amostra_id(self, amostra):
        cursor = self.conn.execute("SELECT id_amostra FROM Amostra WHERE amostra = ?", (amostra,))
        return cursor.fetchone()[0]

    def close(self):
        self.conn.close()

def safe_float_conversion(value):
    try:
        if isinstance(value, str):
            return float(value.strip()) if value.strip() else 0
        return float(value) if value is not None else 0
    except ValueError:
        return 0

def process_file_for_db(df, nome_completo, metadados):
    db_manager = DatabaseManager('C:/Users/lgv_v/Documents/LUIZ/Laboratorio_Geotecnia.db')

    id_metadados = db_manager.insert_metadados(nome_completo, metadados)
    
    tipo = '_'.join(nome_completo.split('_')[:2])
    amostra = nome_completo.split('_')[2]
    
    id_tipo = db_manager.insert_tipo_ensaio(tipo)
    id_amostra = db_manager.insert_amostra(amostra)

    id_ensaio = db_manager.insert_ensaio(id_tipo, id_amostra, id_metadados, nome_completo)
    
    if id_ensaio:
        for col in df.columns:
            df[col] = df[col].apply(safe_float_conversion)
        db_manager.insert_ensaios_triaxiais(id_ensaio, id_amostra, id_tipo, nome_completo, df.to_dict(orient='list'))

    db_manager.close()

if __name__ == "__main__":
    db_manager = DatabaseManager('C:/Users/lgv_v/Documents/LUIZ/Laboratorio_Geotecnia.db')
    db_manager.close()
