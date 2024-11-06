# testeBD.py

import sqlite3
import os
import logging
import pandas as pd

# Configuração de logging para registrar em arquivo e exibir apenas warnings e erros no console
logging.basicConfig(
    filename='database_manager.log',          # Arquivo de log
    filemode='a',                             # Modo de anexação
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO                        # Nível mínimo de log
)

# Configurar o handler para o console para exibir apenas warnings e superiores
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

def quote_identifier(s):
    """Função para escapar identificadores SQL."""
    return '"' + s.replace('"', '""') + '"'

def safe_float_conversion(value):
    try:
        if isinstance(value, str):
            return float(value.strip()) if value.strip() else 0.0
        return float(value) if value is not None else 0.0
    except (ValueError, TypeError):
        return 0.0

class DatabaseManager:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
        logging.info("Conectado ao banco de dados e tabelas criadas (se não existirem).")

    def create_tables(self):
        with self.conn:
            # Tabela TipoEnsaio
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS TipoEnsaio (
                    id_tipo INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT UNIQUE
                )
            """)
            logging.info("Tabela 'TipoEnsaio' verificada/criada.")

            # Tabela Amostra
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS Amostra (
                    id_amostra INTEGER PRIMARY KEY AUTOINCREMENT,
                    amostra TEXT UNIQUE,
                    statusAmostra TEXT DEFAULT 'NV'  
                )
            """)
            logging.info("Tabela 'Amostra' verificada/criada.")

            # Tabela Ensaio
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS Ensaio (
                    id_ensaio INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_tipo INTEGER,
                    id_amostra INTEGER,
                    NomeCompleto TEXT UNIQUE,
                    ensaio TEXT,
                    statusIndividual TEXT DEFAULT 'NV', 
                    FOREIGN KEY (id_tipo) REFERENCES TipoEnsaio(id_tipo),
                    FOREIGN KEY (id_amostra) REFERENCES Amostra(id_amostra),
                    FOREIGN KEY (statusAmostra) REFERENCES Amostra(statusAmostra)
                )
            """)
            logging.info("Tabela 'Ensaio' verificada/criada.")

            # Tabela EnsaiosTriaxiais
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
            logging.info("Tabela 'EnsaiosTriaxiais' verificada/criada.")

            # Tabela Metadados
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS Metadados (
                    id_metadados INTEGER PRIMARY KEY AUTOINCREMENT,
                    metadados TEXT UNIQUE
                )
            """)
            logging.info("Tabela 'Metadados' verificada/criada.")

            # Tabela MetadadosArquivo
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS MetadadosArquivo (
                    id_metadados_arquivo INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_metadados INTEGER,
                    valor_metadados TEXT,
                    NomeCompleto TEXT,
                    FOREIGN KEY (id_metadados) REFERENCES Metadados(id_metadados)
                )
            """)
            logging.info("Tabela 'MetadadosArquivo' verificada/criada.")

    def insert_metadados_fixos(self, metadados_fixos):
        with self.conn:
            for metadado in metadados_fixos:
                self.conn.execute("INSERT OR IGNORE INTO Metadados (metadados) VALUES (?)", (metadado,))
        logging.info("Metadados fixos inseridos com sucesso.")

    def get_metadados_id(self, metadado):
        cursor = self.conn.execute("SELECT id_metadados FROM Metadados WHERE metadados = ?", (metadado,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            raise ValueError(f"Metadado '{metadado}' não encontrado na tabela Metadados.")

    def insert_metadados_arquivo(self, nome_completo, metadados):
        with self.conn:
            for metadado_nome, valor in metadados.items():
                try:
                    id_metadados = self.get_metadados_id(metadado_nome)
                    self.conn.execute("""
                        INSERT INTO MetadadosArquivo (id_metadados, valor_metadados, NomeCompleto)
                        VALUES (?, ?, ?)
                    """, (id_metadados, valor, nome_completo))
                except ValueError as ve:
                    logging.warning(ve)
                    continue  # Ignorar metadados que não estão na tabela Metadados
        logging.info(f"Metadados para o arquivo '{nome_completo}' inseridos com sucesso.")

    def insert_tipo_ensaio(self, tipo):
        with self.conn:
            self.conn.execute("INSERT OR IGNORE INTO TipoEnsaio (tipo) VALUES (?)", (tipo,))
            cursor = self.conn.execute("SELECT id_tipo FROM TipoEnsaio WHERE tipo = ?", (tipo,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                logging.error(f"Falha ao obter id_tipo para TipoEnsaio '{tipo}'.")
                return None

    def insert_amostra(self, amostra):
        with self.conn:
            self.conn.execute("INSERT OR IGNORE INTO Amostra (amostra) VALUES (?)", (amostra,))
            cursor = self.conn.execute("SELECT id_amostra FROM Amostra WHERE amostra = ?", (amostra,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                logging.error(f"Falha ao obter id_amostra para Amostra '{amostra}'.")
                return None

    def insert_ensaio(self, id_tipo, id_amostra, nome_completo, ensaio):
        with self.conn:
            try:
                cursor = self.conn.execute("""
                    INSERT INTO Ensaio (id_tipo, id_amostra, NomeCompleto, ensaio)
                    VALUES (?, ?, ?, ?)
                """, (id_tipo, id_amostra, nome_completo, ensaio))
                logging.info(f"Ensaio '{nome_completo}' inserido com sucesso.")
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                cursor = self.conn.execute("SELECT id_ensaio FROM Ensaio WHERE NomeCompleto = ?", (nome_completo,))
                result = cursor.fetchone()
                if result:
                    id_ensaio = result[0]
                    logging.info(f"Ensaio '{nome_completo}' já existe. ID: {id_ensaio}.")
                    return id_ensaio
                else:
                    logging.error(f"Ensaio '{nome_completo}' já existe, mas não foi possível recuperar id_ensaio.")
                    return None

    def get_existing_columns(self, table_name):
        cursor = self.conn.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        logging.info(f"Colunas existentes na tabela '{table_name}': {columns}")
        return columns

    def insert_ensaios_triaxiais(self, id_ensaio, id_amostra, id_tipo, nome_completo, data):
        with self.conn:
            # Lista de colunas desejadas na ordem correta e com nomes corrigidos (sem '_calculada')
            required_columns = [
                'stage_no', 'time_test_start', 'time_stage_start', 'rad_press_Original', 'rad_vol_Original',
                'back_press_Original', 'back_vol_Original', 'load_cell_Original', 'pore_press_Original',
                'ax_disp_Original', 'ax_force_Original', 'ax_strain_Original', 'avg_diam_chg_Original',
                'rad_strain_Original', 'ax_strain_Original_2', 'eff_ax_stress_Original', 'eff_rad_stress_Original',
                'dev_stress_Original', 'total_stress_rat_Original', 'eff_stress_rat_Original',
                'cur_area_Original', 'shear_strain_Original', 'camb_p_Original', 'eff_camb_p_Original',
                'max_shear_stress_Original', 'vol_change_Original', 'b_value_Original', 'mean_stress_Original',
                'ax_force', 'load', 'rad_vol_delta', 'rad_vol', 'rad_press', 'back_press',
                'back_vol_delta', 'back_vol', 'ax_disp_delta', 'ax_disp', 'height', 'vol_A', 'vol_B',
                'cur_area_A', 'cur_area_B', 'eff_rad_stress', 'dev_stress_A', 'dev_stress_B',
                'ax_stress', 'ax_strain', 'vol_strain', 'void_ratio_B',
                'void_ratio_A', 'eff_ax_stress_A', 'eff_ax_stress_B', 'eff_stress_rat_A',
                'eff_stress_rat_B', 'eff_camb_A', 'eff_camb_B',
                'camb_p_A', 'camb_p_B', 'max_shear_stress_A',
                'max_shear_stress_B', 'excessPWP', 'du_kpa_A', 'du_kpa_B', 'nqp_A', 'nqp_B',
                'm_A', 'm_B', 'shear_strain', 'diameter_A', 'diameter_B',
                'b_val', 'avg_eff_stress_A', 'avg_eff_stress_B', 'avg_mean_stress',
                'rad_strain_A', 'rad_strain_B'
            ]

            # Filtrar apenas as colunas desejadas presentes no DataFrame
            filtered_data = {col: data[col] for col in required_columns if col in data}

            # Verificar e adicionar colunas faltantes como REAL
            existing_columns = self.get_existing_columns('EnsaiosTriaxiais')
            new_columns = [col for col in required_columns if col not in existing_columns]
            for col in new_columns:
                col_quoted = quote_identifier(col)
                self.conn.execute(f"ALTER TABLE EnsaiosTriaxiais ADD COLUMN {col_quoted} REAL")
                logging.info(f"Coluna '{col}' adicionada à tabela 'EnsaiosTriaxiais'.")

            # Verificar se todas as colunas desejadas estão no DataFrame
            missing_columns = set(required_columns) - set(filtered_data.keys())
            if missing_columns:
                logging.warning(f"As seguintes colunas estão faltando no DataFrame e serão preenchidas com 0.0: {missing_columns}")
                for col in missing_columns:
                    filtered_data[col] = [0.0] * len(data['stage_no'])
            else:
                logging.info("Todas as colunas necessárias estão presentes no DataFrame.")

            # Inserir cada registro
            for i in range(len(data['stage_no'])):
                row_data = {key: (filtered_data[key][i] if filtered_data[key][i] is not None else 0.0) for key in required_columns}
                placeholders = ", ".join(["?"] * len(required_columns))
                columns = ", ".join([quote_identifier(key) for key in required_columns])
                self.conn.execute(
                    f"INSERT INTO EnsaiosTriaxiais (id_ensaio, id_amostra, id_tipo, NomeCompleto, {columns}) "
                    f"VALUES (?, ?, ?, ?, {placeholders})",
                    (id_ensaio, id_amostra, id_tipo, nome_completo, *row_data.values())
                )
        logging.info(f"Dados EnsaiosTriaxiais para '{nome_completo}' inseridos com sucesso.")

    def close(self):
        self.conn.close()

def process_file_for_db(df, nome_completo, metadados):
    db_manager = DatabaseManager('C:/Users/lgv_v/Documents/LUIZ/Laboratorio_Geotecnia.db')

    metadados_fixos = {
        "B",
        "Adensamento",
        "Cisalhamento",
        "Base Drain Used (y/n):",
        "Side Drains Used (y/n):",
        "% by mass of Sample retained on No. 40 sieve (Medium Sand):",
        "Specify method to determine post_consolidation specimen area (A/B/A and B):",
        "Specify failure criterion (max deviator stress/deviator stress at 15% strain/max eff. stress/other:",
        "Time of Test",
        "Date of Test",
        "Start of Repeated Data",
        "h_init",
        "d_init",
        "ram_diam",
        "spec_grav",
        "job_ref",
        "borehole",
        "samp_name",
        "depth",
        "samp_date",
        "samp_desc",
        "init_mass",
        "init_dry_mass",
        "spec_grav_am",
        "test_start",
        "test_end",
        "spec_type",
        "top_drain",
        "base_drain",
        "fin_mass",
        "fin_dry_mass",
        "mach_no",
        "press_sys",
        "cell_no",
        "ring_no",
        "job_loc",
        "mem_thick",
        "test_no",
        "tech_name",
        "liq_lim",
        "plas_lim",
        "avg_wc_trim",
        "notes",
        "mass_no4",
        "mass_no10",
        "mass_no40",
        "mass_no200",
        "mass_silt",
        "mass_clay",
        "mass_coll",
        "trim_proc",
        "moist_cond",
        "ax_stress_inund",
        "water_desc",
        "test_meth",
        "interp_cv",
        "astm_dep",
        "wc_obt",
        "sat_meth",
        "load_filt_paper",
        "filt_paper_cov",
        "young_mod_mem",
        "w_0",
        "w_f"
    }
    db_manager.insert_metadados_fixos(metadados_fixos)

    db_manager.insert_metadados_arquivo(nome_completo, metadados)

    base_nome = os.path.basename(nome_completo)
    nome_partes = os.path.splitext(base_nome)[0].split('_')

    if len(nome_partes) >= 4:
        tipo = '_'.join(nome_partes[0:2])  # Junta os dois primeiros elementos
        amostra = nome_partes[2]           # Terceiro elemento
        ensaio = nome_partes[3]            # Quarto elemento
    elif len(nome_partes) == 3:
        tipo = nome_partes[0]              # Primeiro elemento
        amostra = nome_partes[1]           # Segundo elemento
        ensaio = nome_partes[2]            # Terceiro elemento
    else:
        tipo = 'Desconhecido'
        amostra = 'Desconhecida'
        ensaio = 'Desconhecido'

    id_tipo = db_manager.insert_tipo_ensaio(tipo)
    id_amostra = db_manager.insert_amostra(amostra)

    id_ensaio = db_manager.insert_ensaio(id_tipo, id_amostra, nome_completo, ensaio)

    if id_ensaio:
        df = df.copy()
        for col in df.columns:
            df[col] = df[col].apply(safe_float_conversion)

        # Definir a lista completa de colunas a serem salvas no banco de dados (sem '_calculada')
        required_columns = [
            'stage_no', 'time_test_start', 'time_stage_start', 'rad_press_Original', 'rad_vol_Original',
            'back_press_Original', 'back_vol_Original', 'load_cell_Original', 'pore_press_Original',
            'ax_disp_Original', 'ax_force_Original', 'ax_strain_Original', 'avg_diam_chg_Original',
            'rad_strain_Original', 'ax_strain_Original_2', 'eff_ax_stress_Original', 'eff_rad_stress_Original',
            'dev_stress_Original', 'total_stress_rat_Original', 'eff_stress_rat_Original',
            'cur_area_Original', 'shear_strain_Original', 'camb_p_Original', 'eff_camb_p_Original',
            'max_shear_stress_Original', 'vol_change_Original', 'b_value_Original', 'mean_stress_Original',
            'ax_force', 'load', 'rad_vol_delta', 'rad_vol', 'rad_press', 'back_press',
            'back_vol_delta', 'back_vol', 'ax_disp_delta', 'ax_disp', 'height', 'vol_A', 'vol_B',
            'cur_area_A', 'cur_area_B', 'eff_rad_stress', 'dev_stress_A', 'dev_stress_B',
            'ax_stress', 'ax_strain', 'vol_strain', 'void_ratio_B',
            'void_ratio_A', 'eff_ax_stress_A', 'eff_ax_stress_B', 'eff_stress_rat_A',
            'eff_stress_rat_B', 'eff_camb_A', 'eff_camb_B',
            'camb_p_A', 'camb_p_B', 'max_shear_stress_A',
            'max_shear_stress_B', 'excessPWP', 'du_kpa_A', 'du_kpa_B', 'nqp_A', 'nqp_B',
            'm_A', 'm_B', 'shear_strain', 'diameter_A', 'diameter_B',
            'b_val', 'avg_eff_stress_A', 'avg_eff_stress_B', 'avg_mean_stress',
            'rad_strain_A', 'rad_strain_B'
        ]
        present_columns = set(df.columns)
        missing_columns = set(required_columns) - present_columns
        if missing_columns:
            logging.warning(f"As seguintes colunas estão faltando no DataFrame e serão preenchidas com 0.0: {missing_columns}")
            for col in missing_columns:
                df[col] = 0.0
        else:
            logging.info("Todas as colunas necessárias estão presentes no DataFrame.")

        db_manager.insert_ensaios_triaxiais(id_ensaio, id_amostra, id_tipo, nome_completo, df.to_dict(orient='list'))

    db_manager.close()

if __name__ == "__main__":
    db_manager = DatabaseManager('C:/Users/lgv_v/Documents/LUIZ/Laboratorio_Geotecnia.db')
    db_manager.close()
