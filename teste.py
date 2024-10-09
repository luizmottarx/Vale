import os
import pandas as pd
import numpy as np
from testeBD import process_file_for_db, safe_float_conversion

class FileProcessor:
    def __init__(self, directory):
        self.directory = directory

    def process_gds_file(self, gds_file):
        try:
            with open(gds_file, 'r', encoding='latin-1') as file:
                lines = file.readlines()

            metadados = {}
            for line in lines[:57]:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    key, value = parts[0].strip().strip('"'), parts[1].strip().strip('"')
                    metadados[key] = safe_float_conversion(value)

            return metadados

        except Exception as e:
            print(f"Erro ao processar o arquivo '{gds_file}': {e}")
            return None

class StageProcessor:
    @staticmethod
    def process_stage_data(metadados):
        try:
            metadados_valores = {
                "B": metadados.get("_B", 5.0),
                "Adensamento": metadados.get("_ad", 7.0),
                "Cisalhamento": metadados.get("_cis", 8.0),
                "w_0": metadados.get("Volume de agua medio inicial", 0.1375),
                "w_f": metadados.get("Volume de agua medio final", 0.2222),
                "h_init": metadados.get("Initial Height (mm)", 1),
                "d_init": metadados.get("Initial Diameter (mm)", 1),
                "spec_grav": metadados.get("Specific Gravity (kN/m³):", 1),
                "final_moisture": metadados.get("Sample Liquid Limit (%)", 0),
                "Saturacao_c": metadados.get("Moisture Condition (natural moisture/inundated):", 1),
                "fin_mass": metadados.get("Final Mass:", 0),
                "fin_dry_mass": metadados.get("Final Dry Mass:", 0),
                "init_mass": metadados.get("Initial mass (g):", 0)
            }
            return metadados_valores

        except Exception as e:
            print(f"Erro ao processar o estágio dos dados: {e}")
            return None

class METADADOS_PARTE2:
    def __init__(self, df, metadados):
        def safe_divide(numerator, denominator, default_value=0):
            return numerator / denominator if denominator != 0 else default_value

        self.w_0 = metadados.get('w_0', 0)
        self.init_mass = metadados.get('init_mass', 0)
        self.init_dry_mass = safe_divide(self.init_mass, (1 + self.w_0))
        self.h_init = metadados.get('h_init', 1)
        self.d_init = metadados.get('d_init', 1)
        self.spec_grav = metadados.get('spec_grav', 1)
        self.v_0 = self.h_init * np.pi * (self.d_init ** 2) / 4
        self.vol_solid = safe_divide(self.init_dry_mass * 1000, self.spec_grav)
        self.final_moisture = metadados.get('final_moisture', 0)
        self.Saturacao_c = metadados.get('Saturacao_c', 1)
        self.w_f = metadados.get('w_f', 0.2222)
        self.v_w_f = self.w_f * self.init_dry_mass * 1000
        self.B = metadados.get("B", 5.0)
        self.Adensamento = metadados.get("Adensamento", 7.0)
        self.Cisalhamento = metadados.get("Cisalhamento", 8.0)
        self.fin_mass = metadados.get("fin_mass", 0)
        self.fin_dry_mass = metadados.get("fin_dry_mass", 0)

        ad_stage_data = df[df['stage_no'] == int(self.Adensamento)]
        cis_stage_data = df[df['stage_no'] == int(self.Cisalhamento)]
        b_stage_data = df[df['stage_no'] == int(self.B)]

        self.ax_disp_0 = 0
        self.back_vol_0 = 0
        self.back_press_0 = df['back_press_Original'].iloc[0] if not df.empty else 0
        self.rad_press_0 = df['rad_press_Original'].iloc[0] if not df.empty else 0
        self.pore_press_0 = df['pore_press_Original'].iloc[0] if not df.empty else 0

        self.ax_disp_c = ad_stage_data['ax_disp_Original'].iloc[-1] if not ad_stage_data.empty else 0
        self.back_vol_c = ad_stage_data['back_vol_Original'].iloc[-1] if not ad_stage_data.empty else 0
        self.h_init_c = ad_stage_data['height'].iloc[-1] if 'height' in ad_stage_data.columns and not ad_stage_data.empty else self.h_init
        self.void_ratio_c = ad_stage_data['void_ratio_B'].iloc[-1] if 'void_ratio_B' in ad_stage_data.columns and not ad_stage_data.empty else 0

        self.back_vol_f = df['back_vol_Original'].iloc[-1] if not df.empty else 0

        self.void_ratio_f = safe_divide(self.spec_grav * self.final_moisture, self.Saturacao_c) if self.final_moisture and self.spec_grav else 0
        self.void_ratio_i = df['void_ratio_B'].iloc[0] if 'void_ratio_B' in df.columns and not df.empty else 0
        self.void_ratio_sat = b_stage_data['void_ratio_B'].iloc[-1] if 'void_ratio_B' in b_stage_data.columns and not b_stage_data.empty else 0
        self.void_ratio_m = 0

        self.v_c_A = self.v_0 - self.back_vol_c
        self.v_c_B = (self.back_vol_c - self.back_vol_f) + self.v_w_f + self.vol_solid

        self.w_c_A = safe_divide(self.v_c_A, self.init_dry_mass) if self.init_dry_mass else 0
        self.w_c_B = safe_divide(self.v_c_B, self.init_dry_mass) if self.init_dry_mass else 0

        self.saturacao_c = 1

        if not cis_stage_data.empty and 'back_vol_Original' in cis_stage_data.columns:
            self.vol_change_c = cis_stage_data['back_vol_Original'].iloc[0] - cis_stage_data['back_vol_Original'].iloc[-1]
        else:
            self.vol_change_c = 0

        self.vol_change_f_c = 0

        self.final_void_vol = self.vol_solid * self.void_ratio_f
        self.cons_void_vol = self.vol_change_f_c + self.vol_change_c + self.final_void_vol
        self.consolidated_area = safe_divide(self.cons_void_vol + self.vol_solid, self.h_init_c) if self.h_init_c else 0

        self.camb_p_A = ad_stage_data['camp_p_A'].iloc[-1] if 'camp_p_A' in ad_stage_data.columns and not ad_stage_data.empty else 0
        self.camb_p_B = ad_stage_data['camp_p_B'].iloc[-1] if 'camp_p_B' in ad_stage_data.columns and not ad_stage_data.empty else 0

class TableProcessor:
    @staticmethod
    def process_table_data(metadados, gds_file):
        try:
            df = pd.read_csv(gds_file, encoding='latin-1', skiprows=57)
            df = df.rename(columns=lambda x: x.strip())
            original_headers = df.columns.tolist()

            header_mapping = {
                original_headers[0]: 'stage_no',
                original_headers[1]: 'time_test_start',
                original_headers[2]: 'time_stage_start',
                original_headers[3]: 'rad_press_Original',
                original_headers[4]: 'rad_vol_Original',
                original_headers[5]: 'back_press_Original',
                original_headers[6]: 'back_vol_Original',
                original_headers[7]: 'load_cell_Original',
                original_headers[8]: 'pore_press_Original',
                original_headers[9]: 'ax_disp_Original',
                original_headers[10]: 'ax_force_Original',
                original_headers[11]: 'ax_strain_Original',
                original_headers[12]: 'avg_diam_chg_Original',
                original_headers[13]: 'rad_strain_Original',
                original_headers[14]: 'ax_strain_Original_2',
                original_headers[15]: 'eff_ax_stress_Original',
                original_headers[16]: 'eff_rad_stress_Original',
                original_headers[17]: 'dev_stress_Original',
                original_headers[18]: 'total_stress_rat_Original',
                original_headers[19]: 'eff_stress_rat_Original',
                original_headers[20]: 'cur_area_Original',
                original_headers[21]: 'shear_strain_Original',
                original_headers[22]: 'camp_p_Original',
                original_headers[23]: 'eff_camb_p_Original',
                original_headers[24]: 'max_shear_stress_Original',
                original_headers[25]: 'vol_change_Original',
                original_headers[26]: 'b_value_Original',
                original_headers[27]: 'mean_stress_Original'
            }

            df.rename(columns=header_mapping, inplace=True)

            required_columns = [
                'stage_no', 'time_test_start', 'time_stage_start',
                'rad_press_Original', 'rad_vol_Original',
                'back_press_Original', 'back_vol_Original',
                'load_cell_Original', 'pore_press_Original',
                'ax_disp_Original', 'ax_force_Original'
            ]

            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing columns: {missing_columns}")

            numeric_columns = [
                'rad_press_Original', 'back_vol_Original', 'load_cell_Original',
                'pore_press_Original', 'ax_disp_Original', 'ax_force_Original',
            ]
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')

            metadados_parte2 = METADADOS_PARTE2(df, metadados)

    # Cálculos Triaxiais

            df['ax_force'] = np.where(df['time_test_start'] == 0, 0, df['load_cell_Original'])
            df['rad_vol_delta'] = np.where(df['time_test_start'] == 0, 0, df['rad_vol_Original'].diff().fillna(0))
            df['rad_vol'] = np.where(df['time_test_start'] == 0, 0, df['rad_vol_delta'].cumsum())
            df['rad_press'] = df['rad_press_Original']
            df['back_press'] = df['back_press_Original']
            df['back_vol_delta'] = np.where(df['time_test_start'] == 0, 0, df['back_vol_Original'].diff().fillna(0))
            df['back_vol'] = np.where(df['time_test_start'] == 0, 0, df['back_vol_delta'].cumsum())
            df['ax_disp_delta'] = np.where(df['time_test_start'] == 0, 0, df['ax_disp_Original'].diff().fillna(0))
            df['ax_disp'] = np.where(df['time_test_start'] == 0, 0, df['ax_disp_delta'].cumsum())
            df['height'] = metadados_parte2.h_init - df['ax_disp']
            df['vol_A'] = np.where(df['stage_no'] < int(metadados.get('Cisalhamento', 0)),
                                metadados_parte2.v_0 - df['back_vol'],
                                metadados_parte2.v_c_A - df['back_vol'])
            df['vol_B'] = np.where(df['stage_no'] < int(metadados.get('Cisalhamento', 0)),
                                metadados_parte2.v_0 - df['back_vol'],
                                metadados_parte2.v_c_B - (df['back_vol'] - metadados_parte2.back_vol_c))
            df['cur_area_A'] = df['vol_A'] / df['height']
            df['cur_area_B'] = df['vol_B'] / df['height']
            df['diameter_A'] = 2 * np.sqrt(df['cur_area_A'] / np.pi)
            df['diameter_B'] = 2 * np.sqrt(df['cur_area_B'] / np.pi)
            df['rad_strain_A'] = (df['diameter_A'] - metadados_parte2.d_init) / metadados_parte2.d_init
            df['rad_strain_B'] = (df['diameter_B'] - metadados_parte2.d_init) / metadados_parte2.d_init
            df['eff_rad_stress'] = df['rad_press'] - df['pore_press_Original']
            df['dev_stress_A'] = np.where(df['cur_area_A'] != 0, df['ax_force'] / (df['cur_area_A'] / 100000), 0)
            df['dev_stress_B'] = np.where(df['cur_area_B'] != 0, df['ax_force'] / (df['cur_area_B'] / 100000), 0)
            df['eff_ax_stress_A'] = df['dev_stress_A'] + df['eff_rad_stress']
            df['eff_ax_stress_B'] = df['dev_stress_B'] + df['eff_rad_stress']
            df['eff_stress_rat_A'] = np.where(df['eff_rad_stress'] != 0, df['eff_ax_stress_A'] / df['eff_rad_stress'], 0)
            df['eff_stress_rat_B'] = np.where(df['eff_rad_stress'] != 0, df['eff_ax_stress_B'] / df['eff_rad_stress'], 0)
            df['ax_strain'] = np.where(df['stage_no'] < int(metadados.get('Cisalhamento', 0)),
                                    df['ax_disp_delta'] / metadados_parte2.h_init,
                                    (-metadados_parte2.ax_disp_c + df['ax_disp_delta']) / (metadados_parte2.h_init - df['ax_disp_delta']))
            df['vol_strain'] = np.where(df['stage_no'] < int(metadados.get('Cisalhamento', 0)),
                                        df['back_vol'] / metadados_parte2.v_0,
                                        (-df['back_vol'] + metadados_parte2.back_vol_c) / metadados_parte2.v_c_B)
            df['ax_stress'] = np.where(df['stage_no'] < int(metadados.get('Cisalhamento', 0)),
                                    metadados_parte2.h_init_c / metadados_parte2.h_init,
                                    (metadados_parte2.h_init_c - metadados_parte2.h_init) / metadados_parte2.h_init)
            df['eff_stress_A'] = df['dev_stress_A'] + df['eff_rad_stress']
            df['eff_stress_B'] = df['dev_stress_B'] + df['eff_rad_stress']
            df['shear_strain'] = (df['ax_strain'] - df['vol_strain']) * 2 / 3
            df['camb_p_A'] = ((df['ax_stress'] - df['dev_stress_A']) * 2 + df['ax_stress']) / 3
            df['camb_p_B'] = ((df['ax_stress'] - df['dev_stress_B']) * 2 + df['ax_stress']) / 3
            df['eff_camb_p_A'] = (df['eff_rad_stress'] * 2 + df['eff_stress_A']) / 3
            df['eff_camb_p_B'] = (df['eff_rad_stress'] * 2 + df['eff_stress_B']) / 3
            df['max_shear_stress_A'] = df['dev_stress_A'] / 2
            df['max_shear_stress_B'] = df['dev_stress_B'] / 2
            df['avg_mean_stress'] = (df['ax_stress'] + df['rad_press']) / 2
            df['avg_eff_stress_A'] = (df['eff_stress_A'] + df['eff_rad_stress']) / 2
            df['avg_eff_stress_B'] = (df['eff_stress_B'] + df['eff_rad_stress']) / 2
            df['b_val'] = np.where(df['stage_no'] == 7,
                                (metadados_parte2.rad_press_0 - df['rad_press']) / (metadados_parte2.pore_press_0 - df['pore_press_Original']), "-")
            df['excess_PWP'] = df['pore_press_Original'] - df['back_press']
            df['su_A'] = df['max_shear_stress_A'] / df['camb_p_A']
            df['su_B'] = df['max_shear_stress_B'] / df['camb_p_B']
            df['q_p_A'] = df['dev_stress_A'] / df['eff_camb_p_A']
            df['q_p_B'] = df['dev_stress_B'] / df['eff_camb_p_B']
            df['o_m_A'] = np.degrees(np.arcsin(3 * df['q_p_A'] / (6 + df['q_p_A'])))
            df['o_m_B'] = np.degrees(np.arcsin(3 * df['q_p_B'] / (6 + df['q_p_B'])))

            process_file_for_db(df, os.path.basename(gds_file), metadados)
            print(f"Dados processados e salvos no banco de dados para o arquivo: {os.path.basename(gds_file)}")

        except Exception as e:
            print(f"Erro ao processar o arquivo '{gds_file}': {e}")

if __name__ == "__main__":
    directory = r'C:\Users\lgv_v\Documents\LUIZ-Teste'
    arquivos = os.listdir(directory)
    for arquivo in arquivos:
        if arquivo.endswith('.gds'):
            metadados = FileProcessor(directory).process_gds_file(os.path.join(directory, arquivo))
            if metadados:
                metadados_valores = StageProcessor.process_stage_data(metadados)
                if metadados_valores:
                    TableProcessor.process_table_data(metadados_valores, os.path.join(directory, arquivo))

#testeBD

import sqlite3
import pandas as pd

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

    def check_if_nome_completo_exists(self, nome_completo):
        with self.conn:
            cursor = self.conn.execute("SELECT id FROM EnsaiosTriaxiais WHERE NomeCompleto = ?", (nome_completo,))
            return cursor.fetchone() is not None

    def insert_metadados(self, nome_completo, metadados):
        with self.conn:
            for key, value in metadados.items():
                if key and value:
                    value = value if value else 'N/A'  # Substituindo None por 'N/A'
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
                self.conn.execute(f"ALTER TABLE EnsaiosTriaxiais ADD COLUMN {col} TEXT")

            for i in range(len(data['stage_no'])):
                row_data = {key: (value[i] if value[i] is not None else 0) for key, value in data.items()}  # Substituindo None por 0
                placeholders = ", ".join(["?"] * len(row_data))
                columns = ", ".join(row_data.keys())
                self.conn.execute(f"INSERT INTO EnsaiosTriaxiais (id_ensaio, id_amostra, id_tipo, NomeCompleto, {columns}) VALUES (?, ?, ?, ?, {placeholders})", 
                                  (id_ensaio, id_amostra, id_tipo, nome_completo, *row_data.values()))

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
            return float(value.strip()) if value.strip() else 0  # Substituindo None por 0
        return float(value) if value is not None else 0  # Substituindo None por 0
    except ValueError:
        return 0  # Substituindo None por 0

def safe_div(x, y):
    try:
        return x / y if y else 0  # Substituindo divisões por 0 por 0
    except ZeroDivisionError:
        return 0  # Substituindo divisões por 0 por 0

def process_file_for_db(df, nome_completo, metadados):
    db_manager = DatabaseManager('C:/Users/lgv_v/Documents/LUIZ/Laboratorio_Geotecnia.db')

    id_metadados = db_manager.insert_metadados(nome_completo, metadados)
    
    tipo = '_'.join(nome_completo.split('_')[:2])  # Pega o tipo até o segundo hífen, por exemplo, 'TIR_S'
    amostra = nome_completo.split('_')[2]
    
    id_tipo = db_manager.insert_tipo_ensaio(tipo)
    id_amostra = db_manager.insert_amostra(amostra)

    id_ensaio = db_manager.insert_ensaio(id_tipo, id_amostra, id_metadados, nome_completo)
    
    if id_ensaio:
        for col in df.columns:
            df[col] = df[col].apply(safe_float_conversion)  # Converte valores None para 0
        db_manager.insert_ensaios_triaxiais(id_ensaio, id_amostra, id_tipo, nome_completo, df.to_dict(orient='list'))

    db_manager.close()

if __name__ == "__main__":
    db_manager = DatabaseManager('C:/Users/lgv_v/Documents/LUIZ/Laboratorio_Geotecnia.db')
    db_manager.close()
