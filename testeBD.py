import os
import sqlite3
import re
import pandas as pd
import traceback
import numpy as np

###############################################################################
# Exemplo de conversão segura para float
###############################################################################
def safe_float_conversion(value, default=0.0):
    """Faz cast seguro para float; caso falhe, retorna 'default'."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

###############################################################################
# Mapeamento de Metadados (Nome Legível -> Nome Abreviado/Coluna no BD)
# Observação: B, Adensamento, Cisalhamento => _B, _ad, _cis
###############################################################################
METADADOS_MAPPING = {
    # Contrato, Campanha, Amostra
    "Job reference:": "idcontrato",
    "Borehole:": "idcampanha",
    "Sample Name:": "idamostra",

    # B, Adensamento, Cisalhamento => underline
    "B": "_B",
    "Adensamento": "_ad",
    "Cisalhamento": "_cis",

    "Volume de umidade médio INICIAL": "w_0",
    "Volume de umidade médio FINAL": "w_f",
    "Initial Height (mm)": "h_init",
    "Initial Diameter (mm)": "d_init",
    "Ram Diameter": "ram_diam",
    "Specific Gravity (kN/m³):": "spec_grav",
    "Depth:": "depth",
    "Sample Date (dd/mm/yyyy):": "samp_date",
    "Description of Sample:": "tipo",
    "Initial mass (g):": "init_mass",
    "Initial dry mass (g):": "init_dry_mass",
    "Specific Gravity (ass/meas):": "spec_grav_assmeas",
    "Date Test Started:": "date_test_started",
    "Date Test Finished:": "date_test_finished",
    "Specimen Type (dis/undis):": "spec_type",
    "Top Drain Used (y/n):": "top_drain",
    "Base Drain Used (y/n):": "base_drain",
    "Side Drains Used (y/n):": "side_drains",
    "Final Mass:": "fin_mass",
    "Final Dry Mass:": "fin_dry_mass",
    "Machine No.:": "mach_no",
    "Pressure System:": "press_sys",
    "Cell No.:": "cell_no",
    "Ring No.:": "ring_no",
    "Job Location:": "job_loc",
    "Membrane Thickness (mm):": "mem_thick",
    "Test Number:": "test_number",
    "Technician Name:": "tech_name",
    "Sample Liquid Limit (%):": "liq_lim",
    "Sample Plastic Limit (%):": "plas_lim",
    "Average Water Content of Sample Trimmings (%):": "avg_wc_trim",
    "Additional Notes (info source or occurrence and size of large particles etc.):": "notes",
    "% by mass of Sample retained on No. 4 sieve (Gravel):": "mass_no4",
    "% by mass of Sample retained on No. 10 sieve (Coarse Sand):": "mass_no10",
    "% by mass of Sample retained on No. 40 sieve (Medium Sand):": "mass_no40",
    "% by mass of Sample retained on No. 200 sieve (Fine Sand):": "mass_no200",
    "% by mass of Sample Silt (0.074 to 0.005 mm):": "mass_silt",
    "% by mass of Sample Clay (smaller than 0.005 mm):": "mass_clay",
    "% by mass of Sample Colloids (smaller than 0.001 mm):": "mass_coll",
    "Trimming Procedure (turntable/cutting shoe/direct test/ring lined sampler):": "trim_proc",
    "Moisture Condition (natural moisture/inundated):": "moist_cond",
    "Axial Stress at Inundation (kPa):": "ax_stress_inund",
    "Description of Water Used:": "water_desc",
    "Test Method (A/B):": "test_meth",
    "Interpretation Procedure for Cv (1/2/Both):": "interp_cv",
    "All Departures from Outlined ASTM D2435/D2435M-11 Procedure:": "astm_dep",
    "Specify how the water content was obtained (cuttings/entire specimen):": "wc_obt",
    "Specify method for specimen saturation (dry method/wet method):": "sat_meth",
    "Specify method to determine post_consolidation specimen area (A/B/A and B):": "post_consol_area",
    "Specify failure criterion (max deviator stress/deviator stress at 15% strain/max eff. stress/other:": "fail_crit",
    "Load carried by filter paper strips (kN/mm):": "load_filt_paper",
    "Specimen perimeter covered by filter paper (mm):": "filt_paper_cov",
    "Young's modulus of membrane material (kPa):": "young_mod_mem",
    "Time of Test": "test_time",
    "Date of Test": "test_date",
    "Start of Repeated Data": "start_rep_data",
    "dry_unit_weight": "dry_unit_weight",
    "init_void_ratio": "init_void_ratio",
    "init_sat": "init_sat",
    "post_cons_void": "post_cons_void",
    "final_moisture": "final_moisture",
    "Saturacao_c": "Saturacao_c",
    "v_0": "v_0",
    "vol_solid": "vol_solid",
    "v_w_f": "v_w_f",
    "ax_disp_0": "ax_disp_0",
    "back_vol_0": "back_vol_0",
    "back_press_0": "back_press_0",
    "rad_press_0": "rad_press_0",
    "pore_press_0": "pore_press_0",
    "ax_disp_c": "ax_disp_c",
    "back_vol_c": "back_vol_c",
    "h_init_c": "h_init_c",
    "back_vol_f": "back_vol_f",
    "v_c_A": "v_c_A",
    "cons_void_vol": "cons_void_vol",
    "v_c_B": "v_c_B",
    "w_c_A": "w_c_A",
    "w_c_B": "w_c_B",
    "void_ratio_c": "void_ratio_c",
    "void_ratio_f": "void_ratio_f",
    "void_ratio_m": "void_ratio_m",
    "vol_change_c": "vol_change_c",
    "vol_change_f_c": "vol_change_f_c",
    "final_void_vol": "final_void_vol",
    "consolidated_area": "consolidated_area",
    "camb_p_A0": "camb_p_A0",
    "camb_p_B0": "camb_p_B0",
}

###############################################################################
# Mapeamento de Tipos de Ensaio
###############################################################################
TIPOENSAIO_MAP = {
    0: "UNKNOWN",
    1: "ADTIR_B",
    2: "ADTIR_B_I",
    3: "ADTIR_HP",
    4: "ADTIR_K0_B_I",
    5: "ADTIR_S",
    6: "CSL",
    7: "CSS",
    8: "CTER_IS",
    9: "CTER_IS_B",
    10: "CTER_IS_B_I",
    11: "CTIR",
    12: "CTIR_S",
    13: "CTIR_S_B",
    14: "CCTIR_S_B_I",
    15: "TER_IS",
    16: "TER_IS_B",
    17: "TIR_S",
    18: "TIR_S_B"
}

class DatabaseManager:
    _instance = None

    def __new__(cls, db_path="database.db"):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            try:
                cls._instance.conn = sqlite3.connect(db_path, timeout=30)
                cls._instance.conn.execute("PRAGMA foreign_keys = ON;")
                cls._instance.create_tables()
                cls._instance.populate_fixed_tables()
            except Exception as e:
                print(f"Erro ao inicializar o banco de dados: {e}")
                traceback.print_exc()
                cls._instance = None
        return cls._instance

    def create_tables(self):
        try:
            with self.conn:
                # Tabela Metadadostable (fixo)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS Metadadostable (
                        idmetadados INTEGER PRIMARY KEY AUTOINCREMENT,
                        metadados TEXT NOT NULL,
                        variavel TEXT NOT NULL,
                        UNIQUE(metadados, variavel)
                    )
                """)

                # Tabela TipoEnsaio (fixo)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS TipoEnsaio (
                        idtipoensaio INTEGER PRIMARY KEY,
                        tipo TEXT UNIQUE NOT NULL
                    )
                """)

                # Tabela Contrato
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS Contrato (
                        idcontrato TEXT PRIMARY KEY
                    )
                """)

                # Tabela Campanha
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS Campanha (
                        idcontrato TEXT NOT NULL,
                        idcampanha TEXT NOT NULL,
                        PRIMARY KEY (idcontrato, idcampanha),
                        FOREIGN KEY (idcontrato) REFERENCES Contrato(idcontrato)
                    )
                """)

                # Tabela Amostra
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS Amostra (
                        idcontrato TEXT NOT NULL,
                        idcampanha TEXT NOT NULL,
                        idamostra TEXT NOT NULL,
                        PRIMARY KEY (idcontrato, idcampanha, idamostra),
                        FOREIGN KEY (idcontrato, idcampanha)
                            REFERENCES Campanha(idcontrato, idcampanha)
                    )
                """)

                # Tabela Ensaio
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS Ensaio (
                        idensaio INTEGER PRIMARY KEY AUTOINCREMENT,
                        idcontrato TEXT NOT NULL,
                        idcampanha TEXT NOT NULL,
                        idamostra TEXT NOT NULL,
                        idtipoensaio INTEGER NOT NULL,
                        FOREIGN KEY (idcontrato, idcampanha, idamostra)
                            REFERENCES Amostra(idcontrato, idcampanha, idamostra),
                        FOREIGN KEY (idtipoensaio) REFERENCES TipoEnsaio(idtipoensaio)
                    )
                """)

                # Tabela CP
                # Correção 1: cp e repeticao => TEXT
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS Cp (
                        idnome INTEGER PRIMARY KEY AUTOINCREMENT,
                        idcontrato TEXT NOT NULL,
                        idcampanha TEXT NOT NULL,
                        idamostra TEXT NOT NULL,
                        idtipoensaio INTEGER NOT NULL,
                        idensaio INTEGER NOT NULL,
                        sequencial TEXT,
                        cp TEXT,
                        repeticao TEXT,
                        filename TEXT UNIQUE NOT NULL,
                        status TEXT,
                        FOREIGN KEY (idcontrato) REFERENCES Contrato(idcontrato),
                        FOREIGN KEY (idcontrato, idcampanha) REFERENCES Campanha(idcontrato, idcampanha),
                        FOREIGN KEY (idcontrato, idcampanha, idamostra)
                            REFERENCES Amostra(idcontrato, idcampanha, idamostra),
                        FOREIGN KEY (idtipoensaio) REFERENCES TipoEnsaio(idtipoensaio),
                        FOREIGN KEY (idensaio) REFERENCES Ensaio(idensaio)
                    )
                """)

                # Tabela MetadadosArquivo
                # Correção 2: remover colunas B, Adensamento, Cisalhamento sem underline
                # Mantemos apenas _B, _ad, _cis
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS MetadadosArquivo (
                        idnome INTEGER PRIMARY KEY,
                        _B TEXT,
                        _ad TEXT,
                        _cis TEXT,
                        w_0 REAL,
                        w_f REAL,
                        h_init REAL,
                        d_init REAL,
                        ram_diam REAL,
                        spec_grav REAL,
                        idcontrato TEXT,
                        idcampanha TEXT,
                        idamostra TEXT,
                        depth REAL,
                        samp_date TEXT,
                        tipo TEXT,
                        init_mass REAL,
                        init_dry_mass REAL,
                        spec_grav_assmeas REAL,
                        date_test_started TEXT,
                        date_test_finished TEXT,
                        spec_type TEXT,
                        top_drain TEXT,
                        base_drain TEXT,
                        side_drains TEXT,
                        fin_mass REAL,
                        fin_dry_mass REAL,
                        mach_no TEXT,
                        press_sys TEXT,
                        cell_no TEXT,
                        ring_no TEXT,
                        job_loc TEXT,
                        mem_thick REAL,
                        sequencial TEXT,
                        tech_name TEXT,
                        liq_lim REAL,
                        plas_lim REAL,
                        avg_wc_trim REAL,
                        notes TEXT,
                        mass_no4 REAL,
                        mass_no10 REAL,
                        mass_no40 REAL,
                        mass_no200 REAL,
                        mass_silt REAL,
                        mass_clay REAL,
                        mass_coll REAL,
                        trim_proc TEXT,
                        moist_cond TEXT,
                        ax_stress_inund REAL,
                        water_desc TEXT,
                        test_meth TEXT,
                        interp_cv TEXT,
                        astm_dep TEXT,
                        wc_obt TEXT,
                        sat_meth TEXT,
                        post_consol_area TEXT,
                        fail_crit TEXT,
                        load_filt_paper REAL,
                        filt_paper_cov REAL,
                        young_mod_mem REAL,
                        test_time TEXT,
                        test_date TEXT,
                        start_rep_data TEXT,
                        dry_unit_weight REAL,
                        init_void_ratio REAL,
                        init_sat REAL,
                        post_cons_void REAL,
                        final_moisture REAL,
                        Saturacao_c REAL,
                        v_0 REAL,
                        vol_solid REAL,
                        v_w_f REAL,
                        ax_disp_0 REAL,
                        back_vol_0 REAL,
                        back_press_0 REAL,
                        rad_press_0 REAL,
                        pore_press_0 REAL,
                        ax_disp_c REAL,
                        back_vol_c REAL,
                        h_init_c REAL,
                        back_vol_f REAL,
                        v_c_A REAL,
                        cons_void_vol REAL,
                        v_c_B REAL,
                        w_c_A REAL,
                        w_c_B REAL,
                        void_ratio_c REAL,
                        void_ratio_f REAL,
                        void_ratio_m REAL,
                        vol_change_c REAL,
                        vol_change_f_c REAL,
                        final_void_vol REAL,
                        consolidated_area REAL,
                        camb_p_A0 REAL,
                        camb_p_B0 REAL,
                        FOREIGN KEY (idnome) REFERENCES Cp(idnome)
                    )
                """)

                # Tabela EnsaiosTriaxiais
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS EnsaiosTriaxiais (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        idnome INTEGER NOT NULL,
                        stage_no REAL,
                        time_test_start REAL,
                        time_stage_start REAL,
                        rad_press_Original REAL,
                        rad_vol_Original REAL,
                        back_press_Original REAL,
                        back_vol_Original REAL,
                        load_cell_Original REAL,
                        pore_press_Original REAL,
                        ax_disp_Original REAL,
                        ax_force_Original REAL,
                        ax_strain_Original REAL,
                        avg_diam_chg_Original REAL,
                        rad_strain_Original REAL,
                        ax_strain_Original_2 REAL,
                        eff_ax_stress_Original REAL,
                        eff_rad_stress_Original REAL,
                        dev_stress_Original REAL,
                        total_stress_rat_Original REAL,
                        eff_stress_rat_Original REAL,
                        cur_area_Original REAL,
                        shear_strain_Original REAL,
                        camb_p_Original REAL,
                        eff_camb_p_Original REAL,
                        max_shear_stress_Original REAL,
                        vol_change_Original REAL,
                        b_value_Original REAL,
                        mean_stress_Original REAL,
                        ax_force REAL,
                        load REAL,
                        rad_vol_delta REAL,
                        rad_vol REAL,
                        rad_press REAL,
                        back_press REAL,
                        back_vol_delta REAL,
                        back_vol REAL,
                        ax_disp_delta REAL,
                        ax_disp REAL,
                        height REAL,
                        vol_A REAL,
                        vol_B REAL,
                        cur_area_A REAL,
                        cur_area_B REAL,
                        eff_rad_stress REAL,
                        dev_stress_A REAL,
                        dev_stress_B REAL,
                        ax_stress REAL,
                        ax_strain REAL,
                        vol_strain REAL,
                        void_ratio_B REAL,
                        void_ratio_A REAL,
                        eff_ax_stress_A REAL,
                        eff_ax_stress_B REAL,
                        eff_stress_rat_A REAL,
                        eff_stress_rat_B REAL,
                        eff_camb_A REAL,
                        eff_camb_B REAL,
                        camb_p_A REAL,
                        camb_p_B REAL,
                        max_shear_stress_A REAL,
                        max_shear_stress_B REAL,
                        excessPWP REAL,
                        du_kpa REAL,
                        nqp_A REAL,
                        nqp_B REAL,
                        m_A REAL,
                        m_B REAL,
                        shear_strain REAL,
                        diameter_A REAL,
                        diameter_B REAL,
                        b_val REAL,
                        avg_eff_stress_A REAL,
                        avg_eff_stress_B REAL,
                        avg_mean_stress REAL,
                        rad_strain_A REAL,
                        rad_strain_B REAL,
                        FOREIGN KEY (idnome) REFERENCES Cp(idnome)
                    )
                """)

                # usuarios
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
                        login TEXT UNIQUE NOT NULL,
                        senha TEXT NOT NULL
                    )
                """)

                # GranulometriaA
                # Correção 3: idensaio como PK + FOREIGN KEY
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS GranulometriaA (
                        idensaio INTEGER PRIMARY KEY,
                        FOREIGN KEY (idensaio) REFERENCES Ensaio(idensaio)
                    )
                """)

                # GranulometriaCP
                # Correção 4: idnome como PK + FOREIGN KEY
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS GranulometriaCP (
                        idnome INTEGER PRIMARY KEY,
                        FOREIGN KEY (idnome) REFERENCES Cp(idnome)
                    )
                """)

        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")
            traceback.print_exc()

    def get_data_for_file(self, filename):
        """
        Recupera os dados necessários para plotagem com base no filename.
        Busca na tabela EnsaiosTriaxiais e retorna como DataFrame.
        """
        try:
            cursor = self.conn.execute("""
                SELECT idnome FROM Cp WHERE filename = ?
            """, (filename,))
            row = cursor.fetchone()
            
            if not row:
                print(f"Arquivo '{filename}' não encontrado na tabela 'Cp'.")
                return None

            idnome = row[0]
            
            # Recuperar os dados de EnsaiosTriaxiais relacionados ao idnome
            query = """
                SELECT * FROM EnsaiosTriaxiais WHERE idnome = ?
            """
            df = pd.read_sql_query(query, self.conn, params=(idnome,))
            
            if df.empty:
                print(f"Nenhum dado encontrado para o arquivo '{filename}' (idnome={idnome}).")
                return None

            return df

        except Exception as e:
            print(f"Erro ao recuperar dados para '{filename}': {e}")
            traceback.print_exc()
            return None

    def delete_user(self, login):
        """
        Exclui um usuário com base no login fornecido.
        
        Args:
            login (str): O nome de login do usuário a ser excluído.
        """
        try:
            with self.conn:
                cursor = self.conn.execute("DELETE FROM usuarios WHERE login = ?", (login,))
                if cursor.rowcount == 0:
                    print(f"Usuário '{login}' não encontrado.")
                else:
                    print(f"Usuário '{login}' excluído com sucesso.")
        except Exception as e:
            print(f"Erro ao excluir o usuário '{login}': {e}")
            traceback.print_exc()

    def get_all_users(self):
        """
        Retorna uma lista com todos os usuários cadastrados.
        
        Returns:
            list: Lista de nomes de usuários.
        """
        try:
            cursor = self.conn.execute("SELECT login FROM usuarios")
            users = [row[0] for row in cursor.fetchall()]
            return users
        except Exception as e:
            print(f"Erro ao obter todos os usuários: {e}")
            traceback.print_exc()
            return []

    def get_all_metadados_for_idnome(self, idnome):
        """
        Retorna um dicionário com todos os metadados para o idnome fornecido.
        """
        try:
            cursor = self.conn.execute("SELECT * FROM MetadadosArquivo WHERE idnome = ?", (idnome,))
            row = cursor.fetchone()
            if not row:
                return {}
            
            columns = [description[0] for description in cursor.description]
            metadados = dict(zip(columns, row))
            return metadados
        
        except Exception as e:
            print(f"Erro ao obter metadados para idnome={idnome}: {e}")
            traceback.print_exc()
            return {}

    def populate_fixed_tables(self):
        """Popula Metadadostable e TipoEnsaio."""
        try:
            cur = self.conn.cursor()
            for legivel, abreviado in METADADOS_MAPPING.items():
                cur.execute("""
                    INSERT OR IGNORE INTO Metadadostable (metadados, variavel)
                    VALUES (?, ?)
                """, (legivel, abreviado))

            for tipo_num, tipo_str in TIPOENSAIO_MAP.items():
                cur.execute("""
                    INSERT OR REPLACE INTO TipoEnsaio (idtipoensaio, tipo)
                    VALUES (?, ?)
                """, (tipo_num, tipo_str))

            self.conn.commit()
            print("Tabelas fixas populadas com sucesso.")
        except Exception as e:
            print(f"Erro ao popular tabelas fixas: {e}")
            traceback.print_exc()

    def get_data_for_files(self, filenames):
        """
        Recebe uma lista de filenames e retorna uma lista de dicionários com os dados de EnsaiosTriaxiais
        e 'NomeCompleto' (nome do arquivo).

        Args:
            filenames (list): Lista de strings com os nomes dos arquivos.

        Returns:
            list: Lista de dicionários, cada dicionário contém os campos de EnsaiosTriaxiais e 'NomeCompleto'.
        """
        try:
            if not filenames:
                return []

            placeholders = ','.join(['?'] * len(filenames))
            query = f"""
                SELECT EnsaiosTriaxiais.*, Cp.filename AS NomeCompleto
                FROM EnsaiosTriaxiais
                JOIN Cp ON EnsaiosTriaxiais.idnome = Cp.idnome
                WHERE Cp.filename IN ({placeholders})
            """
            cursor = self.conn.execute(query, tuple(filenames))
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            data = [dict(zip(columns, row)) for row in rows]
            return data
        except Exception as e:
            print(f"Erro ao obter dados para múltiplos arquivos: {e}")
            traceback.print_exc()
            return []
        
    def get_metadados_map(self):
        return METADADOS_MAPPING

    def get_status_individual(self, filename):
        """
        Retorna o status individual de um arquivo específico a partir da tabela Cp.
        
        Args:
            filename (str): O nome do arquivo para o qual obter o status.
        
        Returns:
            str: O status do arquivo ("Aprovado", "Refugado", etc.) ou None se não encontrado.
        """
        try:
            cursor = self.conn.execute("SELECT status FROM Cp WHERE filename = ?", (filename,))
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            print(f"Erro ao obter status_individual para filename '{filename}': {e}")
            traceback.print_exc()
            return None

    def get_fixed_metadados(self, filename):
        """Retorna {NomeLegivel: ""} para cada metadado do Metadadostable."""
        try:
            c = self.conn.execute("SELECT metadados, variavel FROM Metadadostable")
            base = {}
            for row in c.fetchall():
                base[row[0]] = ""
            return base
        except Exception as e:
            print(f"Erro ao obter metadados fixos: {e}")
            traceback.print_exc()
            return {}

    def get_existing_filenames(self):
        try:
            c = self.conn.execute("SELECT filename FROM Cp")
            r = [row[0] for row in c.fetchall()]
            print(f"Arquivos existentes em Cp: {len(r)}")
            return r
        except Exception as e:
            print(f"Erro ao obter nomes de arquivos existentes: {e}")
            traceback.print_exc()
            return []

    def get_metadata_for_file(self, filename):
        """
        Retorna {NomeLegivel: Valor} consultando MetadadosArquivo,
        invertendo METADADOS_MAPPING p/ repor o nome legível.
        """
        try:
            c = self.conn.execute("""
                SELECT * FROM MetadadosArquivo
                WHERE idnome=(SELECT idnome FROM Cp WHERE filename=?)
            """, (filename,))
            row = c.fetchone()
            if not row:
                print(f"Nenhum metadado em MetadadosArquivo para '{filename}'.")
                return {}

            columns = [desc[0] for desc in c.description]
            inv_map = {abv: leg for leg, abv in METADADOS_MAPPING.items()}

            result = {}
            for idx, col_name in enumerate(columns):
                if idx == 0:  # pular idnome
                    continue
                value = row[idx]
                if col_name in inv_map:
                    result[inv_map[col_name]] = value
                else:
                    result[col_name] = value
            return result

        except Exception as e:
            print(f"Erro em get_metadata_for_file p/ '{filename}': {e}")
            traceback.print_exc()
            return {}


    def get_arquivos_by_status_individual(self, status):
        try:
            c = self.conn.execute("SELECT filename FROM Cp WHERE status=?", (status,))
            return [row[0] for row in c.fetchall()]
        except Exception as e:
            print(f"Erro ao obter arquivos por status={status}: {e}")
            traceback.print_exc()
            return []

    def get_amostras(self):
        try:
            c = self.conn.execute("SELECT idamostra FROM Amostra")
            amostras = list({row[0] for row in c.fetchall()})
            #print(f"Amostras: {len(amostras)}")
            return amostras
        except Exception as e:
            print(f"Erro get_amostras: {e}")
            traceback.print_exc()
            return []

    def get_ensaios_by_amostra(self, amostra, exclude_status='Refugado',
                               tipo_ensaio=None, status_individual=None):
        try:
            if tipo_ensaio and status_individual:
                c = self.conn.execute("""
                    SELECT filename FROM Cp
                     WHERE idamostra=? 
                       AND idtipoensaio=(SELECT idtipoensaio FROM TipoEnsaio WHERE tipo=?)
                       AND status=?
                """, (amostra, tipo_ensaio, status_individual))
            elif status_individual:
                c = self.conn.execute("""
                    SELECT filename FROM Cp
                     WHERE idamostra=? AND status=?
                """, (amostra, status_individual))
            else:
                c = self.conn.execute("""
                    SELECT filename FROM Cp
                     WHERE idamostra=? AND status!=?
                """, (amostra, exclude_status))
            return [row[0] for row in c.fetchall()]
        except Exception as e:
            print(f"Erro get_ensaios_by_amostra: {e}")
            traceback.print_exc()
            return []

    def update_status_cp(self, filename, novo_status):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE Cp
                SET status = ?
                WHERE filename = ?
            """, (novo_status, filename))
            if cursor.rowcount == 0:
                raise ValueError(f"Arquivo '{filename}' não encontrado na tabela Cp.")
            self.conn.commit()
            #logging.info(f"Status do arquivo '{filename}' atualizado para '{novo_status}'.")
        except Exception as e:
            #logging.error(f"Erro ao atualizar status do arquivo '{filename}': {e}")
            traceback.print_exc()
            raise e


    def get_idnome_by_filename(self, filename):
        """
        Retorna o idnome correspondente ao filename fornecido.
        """
        try:
            cursor = self.conn.execute("SELECT idnome FROM Cp WHERE filename = ?", (filename,))
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            print(f"Erro ao obter idnome para filename '{filename}': {e}")
            traceback.print_exc()
            return None

    def get_tipo_ensaio_id(self, tipo_num):
        try:
            c = self.conn.execute("SELECT idtipoensaio FROM TipoEnsaio WHERE idtipoensaio=?", (tipo_num,))
            r = c.fetchone()
            return r[0] if r else None
        except Exception as e:
            print(f"Erro get_tipo_ensaio_id p/ {tipo_num}: {e}")
            traceback.print_exc()
            return None

    def add_user(self, login, senha):
        try:
            with self.conn:
                self.conn.execute("INSERT INTO usuarios (login, senha) VALUES (?,?)", (login, senha))
            print(f"Usuário '{login}' adicionado.")
        except sqlite3.IntegrityError:
            print(f"Usuário '{login}' já existe.")
        except Exception as e:
            print(f"Erro add_user: {e}")
            traceback.print_exc()

    def authenticate_user(self, login, senha):
        try:
            c = self.conn.execute("SELECT * FROM usuarios WHERE login=? AND senha=?", (login, senha))
            return (c.fetchone() is not None)
        except Exception as e:
            print(f"Erro authenticate_user: {e}")
            traceback.print_exc()
            return False

    def close(self):
        if self.conn:
            self.conn.close()
            print("Conexão fechada.")
            self.conn = None

    # Correção 3: GranulometriaA => PK = idensaio
    # Precisamos usar INSERT OR REPLACE se for 1:1
    def save_granulometriaA(self, idensaio, list_of_rows):
        if not list_of_rows:
            return
        cursor = self.conn.cursor()
        for row in list_of_rows:
            cursor.execute("""
                INSERT OR REPLACE INTO GranulometriaA (idensaio)
                VALUES (?)
            """, (idensaio,))
        print(f"Salvos {len(list_of_rows)} registros em GranulometriaA p/ idensaio={idensaio}.")

    # Correção 4: GranulometriaCP => PK = idnome
    # idem 1:1 => INSERT OR REPLACE
    def save_granulometriaCP(self, idnome, list_of_rows):
        if not list_of_rows:
            return
        cursor = self.conn.cursor()
        for row in list_of_rows:
            cursor.execute("""
                INSERT OR REPLACE INTO GranulometriaCP (idnome)
                VALUES (?)
            """, (idnome,))
        print(f"Salvos {len(list_of_rows)} registros em GranulometriaCP p/ idnome={idnome}.")

    def is_tipo_ensaio_valid(self, idtipoensaio):
        """
        Verifica se o idtipoensaio existe na tabela TipoEnsaio.
        Retorna True se existir, False caso contrário.
        """
        try:
            cursor = self.conn.execute("SELECT 1 FROM TipoEnsaio WHERE idtipoensaio = ?", (idtipoensaio,))
            return cursor.fetchone() is not None
        except Exception as e:
            #logging.error(f"Erro ao verificar TipoEnsaio {idtipoensaio}: {e}")
            traceback.print_exc()
            return False
    ##########################################################################
    # save_to_database
    ##########################################################################
    def save_to_database(self, metadados, df_to_save, filename):
        try:
            cursor = self.conn.cursor()

            # Funções auxiliares para conversão segura
            def safe_str(value):
                """Converte o valor para string, retornando uma string vazia se for None."""
                if isinstance(value, bytes):
                    try:
                        return value.decode('utf-8').strip()
                    except UnicodeDecodeError:
                        return ""
                return str(value).strip() if value is not None else ""

            def convert_numpy_types(value):
                """Converte tipos NumPy para tipos nativos do Python."""
                if isinstance(value, (np.float64, np.float32)):
                    return float(value)
                elif isinstance(value, (np.int64, np.int32)):
                    return int(value)
                elif isinstance(value, bytes):
                    try:
                        return value.decode('utf-8').strip()
                    except UnicodeDecodeError:
                        return ""
                else:
                    return value

            # Extrair campos necessários
            idcontrato = metadados.get("idcontrato", "")
            idcampanha = metadados.get("idcampanha", "")
            idamostra  = metadados.get("idamostra", "")

            # Obter 'idtipoensaio' como inteiro
            idtipoensaio = metadados.get("idtipoensaio", 0)  # Já é int

            # Obter 'sequencial', 'cp' e 'repeticao' como strings usando a função auxiliar
            sequencial = safe_str(metadados.get("sequencial", ""))
            cp_str = safe_str(metadados.get("cp", ""))
            rep_str = safe_str(metadados.get("repeticao", ""))

            # Convertendo valores NumPy e bytes no dicionário metadados
            for key in metadados:
                metadados[key] = convert_numpy_types(metadados[key])

            #logging.info(f"Processando arquivo '{filename}'...")
            #logging.debug(f"metadados = {metadados}")

            # Validação dos campos obrigatórios
            if not idcontrato:
                raise ValueError("idcontrato está vazio.")
            if not idcampanha:
                raise ValueError("idcampanha está vazio.")
            if not idamostra:
                raise ValueError("idamostra está vazio.")
            if not sequencial:
                raise ValueError("sequencial está vazio.")
            if not cp_str:
                raise ValueError("cp está vazio.")
            if not rep_str:
                raise ValueError("repeticao está vazio.")

            tipo_num = idtipoensaio if idtipoensaio else 0

            # Verificar se 'idtipoensaio' existe na tabela TipoEnsaio
            if not self.is_tipo_ensaio_valid(tipo_num):
                tipo_num = 0  # Definir como 'UNKNOWN' se não for válido
                if not self.is_tipo_ensaio_valid(tipo_num):
                    raise ValueError("TipoEnsaio inválido e 'UNKNOWN' não encontrado.")

            # Inserir Contrato/Campanha/Amostra
            cursor.execute("INSERT OR IGNORE INTO Contrato (idcontrato) VALUES (?)", (idcontrato,))
            cursor.execute("""
                INSERT OR IGNORE INTO Campanha (idcontrato, idcampanha)
                VALUES (?,?)
            """, (idcontrato, idcampanha))
            cursor.execute("""
                INSERT OR IGNORE INTO Amostra (idcontrato, idcampanha, idamostra)
                VALUES (?,?,?)
            """, (idcontrato, idcampanha, idamostra))

            # Criar Ensaio
            cursor.execute("""
                INSERT INTO Ensaio (idcontrato, idcampanha, idamostra, idtipoensaio)
                VALUES (?,?,?,?)
            """, (idcontrato, idcampanha, idamostra, tipo_num))
            idensaio = cursor.lastrowid
            #logging.info(f"Ensaio criado: idensaio={idensaio}.")

            # Criar Cp
            cursor.execute("""
                INSERT INTO Cp (
                    idcontrato, idcampanha, idamostra, idtipoensaio, idensaio,
                    sequencial, cp, repeticao, filename, status
                ) VALUES (?,?,?,?,?,?,?,?,?,'NV')
            """, (idcontrato, idcampanha, idamostra, tipo_num,
                idensaio, sequencial, cp_str, rep_str, filename))
            idnome = cursor.lastrowid
            #logging.info(f"Cp criado: idnome={idnome}.\n")

            # Inserir MetadadosArquivo
            metadados_columns = [
                "_B","_ad","_cis",
                "w_0","w_f","h_init","d_init","ram_diam","spec_grav",
                "idcontrato","idcampanha","idamostra","depth","samp_date","tipo",
                "init_mass","init_dry_mass","spec_grav_assmeas","date_test_started","date_test_finished",
                "spec_type","top_drain","base_drain","side_drains","fin_mass","fin_dry_mass",
                "mach_no","press_sys","cell_no","ring_no","job_loc","mem_thick","sequencial","tech_name",
                "liq_lim","plas_lim","avg_wc_trim","notes","mass_no4","mass_no10","mass_no40","mass_no200",
                "mass_silt","mass_clay","mass_coll","trim_proc","moist_cond","ax_stress_inund","water_desc",
                "test_meth","interp_cv","astm_dep","wc_obt","sat_meth","post_consol_area","fail_crit",
                "load_filt_paper","filt_paper_cov","young_mod_mem","test_time","test_date","start_rep_data",
                "dry_unit_weight","init_void_ratio","init_sat","post_cons_void","final_moisture","Saturacao_c",
                "v_0","vol_solid","v_w_f","ax_disp_0","back_vol_0","back_press_0","rad_press_0","pore_press_0",
                "ax_disp_c","back_vol_c","h_init_c","back_vol_f","v_c_A","cons_void_vol","v_c_B","w_c_A","w_c_B",
                "void_ratio_c","void_ratio_f","void_ratio_m","vol_change_c","vol_change_f_c","final_void_vol",
                "consolidated_area","camb_p_A0","camb_p_B0"
            ]

            # Montar dicionário para MetadadosArquivo
            metadados_db = {}
            for legivel, abv in METADADOS_MAPPING.items():
                val = metadados.get(abv, None)
                metadados_db[abv] = val

            # Inserir MetadadosArquivo
            col_join = ", ".join(["idnome"] + metadados_columns)
            placeholders = ", ".join(["?"] * (1 + len(metadados_columns)))
            vals = [idnome]
            for col in metadados_columns:
                vals.append(metadados_db.get(col, None))

            cursor.execute(f"""
                INSERT INTO MetadadosArquivo ({col_join})
                VALUES ({placeholders})
            """, vals)
            #logging.info(f"MetadadosArquivo inserido para idnome={idnome}.\n")

            # Inserir dados de EnsaiosTriaxiais
            inserted_rows = 0
            ensaios_columns = df_to_save.columns.tolist()
            ensaios_columns_with_id = ["idnome"] + ensaios_columns
            placeholders2 = ", ".join(["?"] * len(ensaios_columns_with_id))
            col_str = ", ".join(ensaios_columns_with_id)

            for _, row_data in df_to_save.iterrows():
                row_list = list(row_data.values)
                # Converter possíveis tipos NumPy dentro do DataFrame
                row_list = [convert_numpy_types(val) for val in row_list]
                insert_data = [idnome] + row_list
                cursor.execute(f"""
                    INSERT INTO EnsaiosTriaxiais ({col_str})
                    VALUES ({placeholders2})
                """, insert_data)
                inserted_rows += 1

            #logging.info(f"Inseridos {inserted_rows} registros em EnsaiosTriaxiais p/ '{filename}'.")

            # Salvar Granulometria se existirem
            if "granA_data" in metadados:
                self.save_granulometriaA(idensaio, metadados["granA_data"])
            if "granCP_data" in metadados:
                self.save_granulometriaCP(idnome, metadados["granCP_data"])

            self.conn.commit()
            #logging.info("Salvo no banco de dados com sucesso.\n")

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: Cp.filename" in str(e):
                #logging.error(f"Erro ao salvar no banco: {str(e)}")
                traceback.print_exc()
            else:
                #logging.error(f"Erro ao salvar no banco: {str(e)}")
                traceback.print_exc()
        except Exception as e:
            #logging.error(f"Erro ao salvar no banco: {str(e)}")
            traceback.print_exc()
