import os
import pandas as pd
import numpy as np

###############################################################################
# Função auxiliar para conversão segura de floats
###############################################################################
def safe_float_conversion(value, default=0.0):
    """
    Converte 'value' para float, retornando 'default' caso não seja possível.
    """
    try:
        return float(value)
    except:
        return default

###############################################################################
# Função auxiliar para divisão segura
###############################################################################
def safe_divide(numerator, denominator, default_value=0.0):
    """
    Divisão segura que evita ZeroDivisionError; se denominator==0, retorna default_value.
    """
    try:
        return numerator / denominator if denominator != 0 else default_value
    except:
        return default_value

###############################################################################
# Função para encontrar, dinamicamente, a linha do cabeçalho no arquivo .gds
###############################################################################
def find_header_line(gds_file):
    """
    Percorre o arquivo e retorna o índice (0-based) da linha em que se encontra
    a string 'Stage Number'. Supõe-se que essa linha seja a do cabeçalho.
    Caso não encontre, retorna None.
    """
    with open(gds_file, 'r', encoding='latin-1') as file:
        for i, line in enumerate(file):
            if "Stage Number" in line:
                return i
    return None  # Caso não encontre

###############################################################################
# Classe para agrupar e calcular metadados (parte 2)
###############################################################################
class METADADOS_PARTE2:
    """
    Armazena e calcula os metadados principais, com as correções:
      - ax_disp_c => primeiro valor do estágio de cisalhamento (ax_disp_Original)
      - h_init_c => h_init - ax_disp_c
      - height   => h_init - ax_disp_Original (alterado na DF)
      - Evitar zeros indevidos em fin_mass, fin_dry_mass, final_moisture
    """
    def __init__(self, df, metadados, init_dry_mass, v_0, vol_solid, v_w_f, h_init):
        """
        Parâmetros principais:
          - df: DataFrame completo, já renomeado
          - metadados: dict contendo w_0, w_f, init_mass etc.
          - init_dry_mass, v_0, vol_solid, v_w_f, h_init: calculados fora
        """
        self.df = df.copy()

        # ---------------------------------------------------------------------
        # 1) Ler do dicionário de metadados
        # ---------------------------------------------------------------------
        self.w_0            = safe_float_conversion(metadados.get('w_0', 0))
        self.w_f            = safe_float_conversion(metadados.get('w_f', 0))
        self.init_mass      = safe_float_conversion(metadados.get('init_mass', 0))
        self.final_moisture = safe_float_conversion(metadados.get('final_moisture', 0))
        self.Saturacao_c    = safe_float_conversion(metadados.get('Saturacao_c', 0))
        self.h_init         = safe_float_conversion(metadados.get('h_init', 1))
        self.d_init         = safe_float_conversion(metadados.get('d_init', 1))
        self.spec_grav      = safe_float_conversion(metadados.get('spec_grav', 1))

        # Finais de massa (se o usuário passou, não ficar travado em 0)
        self.fin_mass       = safe_float_conversion(metadados.get("fin_mass", 0))
        self.fin_dry_mass   = safe_float_conversion(metadados.get("fin_dry_mass", 0))

        # Estágios
        self.B                   = int(metadados.get("B", 1))
        self.Adensamento         = int(metadados.get("Adensamento", 1))
        self.CisalhamentoInicial = int(metadados.get("_cis_inicial", 1))
        self.CisalhamentoFinal   = int(metadados.get("_cis_final", 1))

        # ---------------------------------------------------------------------
        # 2) Atribuições passadas ao construtor
        # ---------------------------------------------------------------------
        self.init_dry_mass = init_dry_mass
        self.v_0           = v_0
        self.vol_solid     = vol_solid
        self.v_w_f         = v_w_f

        # ---------------------------------------------------------------------
        # 3) Calcular metadados iniciais
        # ---------------------------------------------------------------------
        self.init_dry_mass = safe_divide(self.init_mass, (1 + self.w_0), 0.0)  # redundante
        self.init_vol = self.h_init * ((self.d_init ** 2) * np.pi / 4)
        self.vol_solid = safe_divide(self.init_dry_mass * 1000, self.spec_grav, 0.0)
        self.init_void_ratio = safe_divide((self.init_vol - self.vol_solid), self.vol_solid, 0.0)
        self.void_ratio_f = self.spec_grav * self.w_f
        self.final_void_vol = self.vol_solid * self.void_ratio_f

        # init_sat => saturação inicial (aprox)
        if self.init_void_ratio != 0:
            self.init_sat = (self.w_0 * self.spec_grav / self.init_void_ratio)*100.0
        else:
            self.init_sat = 0.0

        # ---------------------------------------------------------------------
        # 4) Capturar primeiros valores do DF => back_vol_0, etc.
        # ---------------------------------------------------------------------
        if not self.df.empty:
            if 'back_vol_Original' in self.df.columns:
                self.back_vol_0 = self.df['back_vol_Original'].iloc[0]
            else:
                self.back_vol_0 = 0.0

            if 'back_press_Original' in self.df.columns:
                self.back_press_0 = self.df['back_press_Original'].iloc[0]
            else:
                self.back_press_0 = 0.0

            if 'rad_press_Original' in self.df.columns:
                self.rad_press_0 = self.df['rad_press_Original'].iloc[0]
            else:
                self.rad_press_0 = 0.0

            if 'pore_press_Original' in self.df.columns:
                self.pore_press_0 = self.df['pore_press_Original'].iloc[0]
            else:
                self.pore_press_0 = 0.0
        else:
            self.back_vol_0   = 0.0
            self.back_press_0 = 0.0
            self.rad_press_0  = 0.0
            self.pore_press_0 = 0.0

        # ---------------------------------------------------------------------
        # 5) ax_disp_s => primeiro valor do estágio de Adensamento
        # ---------------------------------------------------------------------
        ad_stage_data = self.df[self.df['stage_no'] == self.Adensamento].copy()
        if not ad_stage_data.empty:
            if 'ax_disp_Original' in ad_stage_data.columns:
                self.ax_disp_s = ad_stage_data['ax_disp_Original'].iloc[0]
            else:
                self.ax_disp_s = 0.0
        else:
            self.ax_disp_s = 0.0

        # ax_disp_0 => primeiro valor de ax_disp_Original de toda a coluna
        if not self.df.empty and 'ax_disp_Original' in self.df.columns:
            self.ax_disp_0 = self.df['ax_disp_Original'].iloc[0]
        else:
            self.ax_disp_0 = 0.0

        self.hs = self.ax_disp_s - self.ax_disp_0  # SE <0 => 0 ?

        # ---------------------------------------------------------------------
        # 6) ax_disp_c => primeiro valor do estágio de cisalhamento (CisalhamentoInicial)
        #    em ax_disp_Original 
        # ---------------------------------------------------------------------
        cis_data_for_disp = self.df[self.df['stage_no'] == self.CisalhamentoInicial].copy()
        if not cis_data_for_disp.empty and 'ax_disp_Original' in cis_data_for_disp.columns:
            self.ax_disp_c = cis_data_for_disp['ax_disp_Original'].iloc[0]
        else:
            self.ax_disp_c = 0.0

        # h_init_c => h_init - ax_disp_c
        self.h_init_c = self.h_init - self.ax_disp_c

        # ---------------------------------------------------------------------
        # 7) back_vol_c => se quisermos do adensamento (último valor)
        #    void_ratio_c => se quisermos do adensamento também
        # ---------------------------------------------------------------------
        if not ad_stage_data.empty:
            if 'back_vol' in ad_stage_data.columns:
                self.back_vol_c = ad_stage_data['back_vol'].iloc[-1]
            else:
                self.back_vol_c = 0.0

            # se existir 'void_ratio_A' ou 'void_ratio_B':
            if 'void_ratio_A' in ad_stage_data.columns:
                self.void_ratio_c = ad_stage_data['void_ratio_A'].iloc[-1]
            else:
                self.void_ratio_c = 0.0
        else:
            self.back_vol_c = 0.0
            self.void_ratio_c = 0.0

        # ---------------------------------------------------------------------
        # 8) capturar vol_change_c e vol_change_f_c do cisalhamento
        # ---------------------------------------------------------------------
        cis_stage_data = self.df[
            (self.df['stage_no'] >= self.CisalhamentoInicial) &
            (self.df['stage_no'] <= self.CisalhamentoFinal)
        ].copy()
        if not cis_stage_data.empty and 'back_vol' in cis_stage_data.columns:
            self.vol_change_c = cis_stage_data['back_vol'].iloc[0] - cis_stage_data['back_vol'].iloc[-1]
        else:
            self.vol_change_c = 0.0

        next_stage = self.CisalhamentoFinal + 1
        next_stage_data = self.df[self.df['stage_no'] == next_stage].copy()
        if not next_stage_data.empty and 'back_vol' in next_stage_data.columns:
            self.vol_change_f_c = (
                next_stage_data['back_vol'].iloc[0] - next_stage_data['back_vol'].iloc[-1]
            )
        else:
            self.vol_change_f_c = 0.0

        # ---------------------------------------------------------------------
        # 9) Cálculo diferenciado para metadados de consolidação (lado A e lado B)
        # ---------------------------------------------------------------------
        # Calcular vol_change_s utilizando hs, v_0 e h_init
        if self.hs < 0:
            vol_change_s = 0.0
        else:
            vol_change_s = 3.0 * self.v_0 * safe_divide(self.hs, self.h_init, 0.0)

        # Calcular cons_vol (utilizado para o lado A)
        cons_vol = self.v_0 - self.vol_change_f_c - vol_change_s

        # Agora, calcular os volumes de vazio pós consolidação para os lados A e B:
        cons_void_vol_A = cons_vol - self.vol_solid
        cons_void_vol_B = self.vol_solid * self.void_ratio_f

        # Calcular os índices pós consolidação para cada lado
        post_cons_void_A = safe_divide(cons_void_vol_A, self.vol_solid, 0.0)
        post_cons_void_B = safe_divide(cons_void_vol_B, self.vol_solid, 0.0)

        # Calcular as áreas consolidadas para cada lado
        consolidated_area_A = 1e-6 * safe_divide((self.v_0 - vol_change_s - self.vol_change_f_c), self.h_init_c, 0.0)
        consolidated_area_B = 1e-6 * safe_divide((cons_void_vol_B + self.vol_solid), self.h_init_c, 0.0)

        # Armazenar os novos metadados como atributos:
        self.cons_void_vol_A = cons_void_vol_A
        self.cons_void_vol_B = cons_void_vol_B
        self.post_cons_void_A = post_cons_void_A
        self.post_cons_void_B = post_cons_void_B
        self.consolidated_area_A = consolidated_area_A
        self.consolidated_area_B = consolidated_area_B

        # ---------------------------------------------------------------------
        # 10) Calcular parâmetros adicionais (unit weight, etc.)
        # ---------------------------------------------------------------------
        denom = (((self.d_init / 10) ** 2) * np.pi) / 4.0 * (self.h_init / 10.0)
        self.dry_unit_weight = safe_divide(self.init_dry_mass, denom, 0.0)
        self.D_saturation = (self.spec_grav * self.w_0 / self.d_init) * 100.0
        self.D_spec_grav = safe_divide(self.init_dry_mass,
            ((((self.d_init / 10) ** 2) * np.pi) / 4.0) * (self.h_init / 10.0),
            0.0
        )

        # pore_press_c => primeiro valor no estágio cisalhamento da coluna pore_press_Original
        cis_data_for_pore = self.df[self.df['stage_no'] == self.CisalhamentoInicial].copy()
        if not cis_data_for_pore.empty and 'pore_press_Original' in cis_data_for_pore.columns:
            self.pore_press_c = cis_data_for_pore['pore_press_Original'].iloc[0]
        else:
            self.pore_press_c = 0.0

        # Camb_p_A0, Camb_p_B0 => se quisermos do adensamento
        if not ad_stage_data.empty and 'camb_p_Original' in ad_stage_data.columns:
            self.camb_p_A0 = ad_stage_data['camb_p_Original'].iloc[-1]
            self.camb_p_B0 = ad_stage_data['camb_p_Original'].iloc[-1]
        else:
            self.camb_p_A0 = 0.0
            self.camb_p_B0 = 0.0

    def print_attributes(self):
        """
        Exibe todos os atributos calculados para inspeção/debug.
        """
        print("====================== DUMP DOS METADADOS ======================")
        for attr, value in vars(self).items():
            print(f"{attr} => {value}")
        print("===============================================================\n")

    def get_all_attributes(self):
        """
        Retorna todas as variáveis calculadas como dicionário.
        """
        return vars(self)


###############################################################################
# Classe exemplo para dados de Cisalhamento
###############################################################################
class CisalhamentoData:
    """
    Exemplo de classe para filtrar e checar dados do estágio de cisalhamento.
    """
    def __init__(self, df, metadados):
        cis_inicial = int(metadados.get("_cis_inicial", 8))
        cis_final   = int(metadados.get("_cis_final", 8))

        self.df_cisalhamento = df[
            (df['stage_no'] >= cis_inicial) & (df['stage_no'] <= cis_final)
        ].copy()

        if self.df_cisalhamento.empty:
            raise ValueError(
                f"Nenhum dado encontrado para o estágio de Cisalhamento {cis_inicial}–{cis_final}."
            )

        required_columns = [
            'ax_strain', 'dev_stress_A', 'dev_stress_B',
            'vol_strain_A','vol_strain_B', 'eff_camb_A', 'eff_camb_B',
            'du_kpa', 'void_ratio_A', 'void_ratio_B',
            'nqp_A', 'nqp_B', 'm_A', 'm_B'
        ]
        missing_cols = [col for col in required_columns if col not in self.df_cisalhamento.columns]
        if missing_cols:
            raise ValueError(
                f"Colunas faltantes no estágio cis {cis_inicial}–{cis_final}: {missing_cols}"
            )

        # Apenas para exemplificar
        self.ax_strain      = self.df_cisalhamento['ax_strain']
        self.dev_stress_A   = self.df_cisalhamento['dev_stress_A']
        self.dev_stress_B   = self.df_cisalhamento['dev_stress_B']
        self.vol_strain_A   = self.df_cisalhamento['vol_strain_A']
        self.vol_strain_B   = self.df_cisalhamento['vol_strain_B']
        self.eff_camb_A     = self.df_cisalhamento['eff_camb_A']
        self.eff_camb_B     = self.df_cisalhamento['eff_camb_B']
        self.du_kpa         = self.df_cisalhamento['du_kpa']
        self.void_ratio_A   = self.df_cisalhamento['void_ratio_A']
        self.void_ratio_B   = self.df_cisalhamento['void_ratio_B']
        self.nqp_A          = self.df_cisalhamento['nqp_A']
        self.nqp_B          = self.df_cisalhamento['nqp_B']
        self.m_A            = self.df_cisalhamento['m_A']
        self.m_B            = self.df_cisalhamento['m_B']

    def get_cisalhamento_data(self):
        """
        Retorna um dicionário com as colunas principais do estágio de cisalhamento.
        """
        return {
            "ax_strain":      self.ax_strain,
            "dev_stress_A":   self.dev_stress_A,
            "dev_stress_B":   self.dev_stress_B,
            "vol_strain_A":   self.vol_strain_A,
            "vol_strain_B":   self.vol_strain_B,
            "eff_camb_A":     self.eff_camb_A,
            "eff_camb_B":     self.eff_camb_B,
            "du_kpa":         self.du_kpa,
            "void_ratio_A":   self.void_ratio_A,
            "void_ratio_B":   self.void_ratio_B,
            "nqp_A":          self.nqp_A,
            "nqp_B":          self.nqp_B,
            "m_A":            self.m_A,
            "m_B":            self.m_B,
        }

###############################################################################
# Classe principal TableProcessor
###############################################################################
class TableProcessor:
    @staticmethod
    def process_table_data(db_manager, metadados, gds_file):
        """
        Faz a leitura do arquivo GDS, localiza o cabeçalho,
        ajusta as colunas e realiza os cálculos, retornando um dict
        com DataFrame final e a instância METADADOS_PARTE2.
        Inclui a mudança em 'height = h_init - ax_disp_Original'.
        Garante a criação e o preenchimento das colunas solicitadas.
        """
        try:
            # 1) Encontrar a linha do cabeçalho no .gds
            header_line = find_header_line(gds_file)
            if header_line is None:
                raise ValueError(
                    f"Cabeçalho com 'Stage Number' não encontrado no arquivo {gds_file}."
                )

            # 2) Ler CSV a partir dessa linha do cabeçalho
            df = pd.read_csv(
                gds_file,
                encoding='latin-1',
                skiprows=header_line,  # Pular as linhas até 'Stage Number'
                header=0               # A próxima linha é o nome das colunas
            )

            # Debug (opcional)
            print("DEBUG - COLUNAS LIDAS DO ARQUIVO:")
            print(df.columns.tolist())
            print("DEBUG - PRIMEIRAS LINHAS DO DATAFRAME LIDO:")
            print(df.head(5))

            # Remover espaços extras dos nomes de colunas
            df.rename(columns=lambda x: x.strip(), inplace=True)

            # Mapeamento de cabeçalhos para colunas "_Original"
            header_mapping = {
                "Stage Number":                 "stage_no",
                "Time since start of test (s)": "time_test_start",
                "Time since start of stage (s)": "time_stage_start",
                "Radial Pressure (kPa)":        "rad_press_Original",
                "Radial Volume (mm³)":          "rad_vol_Original",
                "Back Pressure (kPa)":          "back_press_Original",
                "Back Volume (mm³)":            "back_vol_Original",
                "Load Cell (kN)":               "load_cell_Original",
                "Pore Pressure (kPa)":          "pore_press_Original",
                "Axial Displacement (mm)":      "ax_disp_Original",
                "Axial Force (kN)":             "ax_force_Original",
                "Axial Strain (%)":             "ax_strain_Original",
                "Av Diameter Change (mm)":      "avg_diam_chg_Original",
                "Radial Strain (%)":            "rad_strain_Original",
                "Axial Stress (kPa)":           "ax_strain_Original_2",
                "Eff. Axial Stress (kPa)":      "eff_ax_stress_Original",
                "Eff. Radial Stress (kPa)":     "eff_rad_stress_Original",
                "Deviator Stress (kPa)":        "dev_stress_Original",
                "Total Stress Ratio":           "total_stress_rat_Original",
                "Eff. Stress Ratio":            "eff_stress_rat_Original",
                "Current Area (mm²)":           "cur_area_Original",
                "Shear Strain (%)":             "shear_strain_Original",
                "Cambridge p (kPa)":            "camb_p_Original",
                "Eff. Cambridge p' (kPa)":      "eff_camb_p_Original",
                "Max Shear Stress t (kPa)":     "max_shear_stress_Original",
                "Volume Change (mm³)":          "vol_change_Original",
                "B Value":                      "b_value_Original",
                "Mean Stress s/Eff. Axial Stress 2": "mean_stress_Original",
            }
            df.rename(columns=header_mapping, inplace=True)

            # 3) Checar colunas obrigatórias
            required_cols = [
                "stage_no",
                "time_test_start",
                "time_stage_start",
                "rad_press_Original",
                "rad_vol_Original",
                "back_press_Original",
                "back_vol_Original",
                "load_cell_Original",
                "pore_press_Original",
                "ax_disp_Original",
                "ax_force_Original",
            ]
            missing_cols = [c for c in required_cols if c not in df.columns]
            if missing_cols:
                raise ValueError(f"Colunas faltantes: {missing_cols}")

            # 4) Converter colunas-base para numérico (coerce)
            numeric_base = [
                "rad_press_Original", "rad_vol_Original", "back_press_Original",
                "back_vol_Original",  "load_cell_Original", "pore_press_Original",
                "ax_disp_Original",   "ax_force_Original"
            ]
            df[numeric_base] = df[numeric_base].apply(pd.to_numeric, errors='coerce')

            # 5) Ler metadados principais p/ cálculo inicial
            w_0       = safe_float_conversion(metadados.get('w_0', 0))
            w_f       = safe_float_conversion(metadados.get('w_f', 0))
            init_mass = safe_float_conversion(metadados.get('init_mass', 0))
            h_init    = safe_float_conversion(metadados.get('h_init', 1))
            d_init    = safe_float_conversion(metadados.get('d_init', 1))
            spec_grav = safe_float_conversion(metadados.get('spec_grav', 1))

            init_dry_mass = safe_divide(init_mass, (1 + w_0), 0.0)
            v_0           = h_init * (np.pi * (d_init ** 2) / 4.0)
            vol_solid     = safe_divide(init_dry_mass * 1000.0, spec_grav, 0.0)
            v_w_f         = w_f * init_dry_mass * 1000.0

            # 6) Colunas derivadas “base”
            df['ax_force'] = df['load_cell_Original']
            df['load']     = df['load_cell_Original']

            # (A) Volume radial
            df['rad_vol_delta']  = df['rad_vol_Original'].diff().fillna(0.0)
            df['rad_vol_cumsum'] = df['rad_vol_delta'].cumsum()
            df['rad_vol']        = df['rad_vol_cumsum']

            df['rad_press']  = df['rad_press_Original']
            df['back_press'] = df['back_press_Original']

            # (B) Volume back
            df['back_vol_delta']  = df['back_vol_Original'].diff().fillna(0.0)
            df['back_vol_cumsum'] = df['back_vol_delta'].cumsum()
            df['back_vol']        = df['back_vol_cumsum']

            # (C) Desloc. axial
            df['ax_disp_delta']  = df['ax_disp_Original'].diff().fillna(0.0)
            df['ax_disp_cumsum'] = df['ax_disp_delta'].cumsum()
            df['ax_disp']        = df['ax_disp_cumsum']

            # (D) height = h_init - ax_disp_Original (pedido)
            df['height'] = h_init - df['ax_disp_Original']

            # (E) vol_A e vol_B (iguais se for caso isotrópico)
            df['vol_A'] = v_0 - df['back_vol']
            df['vol_B'] = v_0 - df['back_vol']

            # (F) Área corrente lado A
            df['cur_area_A'] = (
                safe_divide(df['vol_A'], df['height'].replace(0, np.nan), 0.0)
            ) * 1e-6

            # 7) Instanciar METADADOS_PARTE2 e recalcular metadados
            metadados_parte2 = METADADOS_PARTE2(
                df=df,
                metadados=metadados,
                init_dry_mass=init_dry_mass,
                v_0=v_0,
                vol_solid=vol_solid,
                v_w_f=v_w_f,
                h_init=h_init
            )

            # -- A) Axial strain ajustado para cisalhamento --
            cis_stage = int(metadados_parte2.CisalhamentoInicial)
            def calc_ax_strain(row):
                # (ax_disp - ax_disp_c)/(h_init - ax_disp) se >= cis_inicial
                if row['stage_no'] >= cis_stage:
                    return safe_divide(
                        (row['ax_disp'] - metadados_parte2.ax_disp_c),
                        (h_init - row['ax_disp']),
                        0.0
                    )
                else:
                    return safe_divide(row['ax_disp'], h_init, 0.0)
            df['ax_strain'] = df.apply(calc_ax_strain, axis=1)

            # 8) Calcular vol_change_s e vol_change_f_c p/ consolidação
            #    (já vem em metadados_parte2, mas repetimos para colunas)
            ad_data = df[df['stage_no'] == metadados_parte2.Adensamento]
            if not ad_data.empty:
                back_vol_c = ad_data['back_vol'].iloc[-1]
            else:
                back_vol_c = 0.0

            if metadados_parte2.hs < 0:
                vol_change_s = 0.0
            else:
                vol_change_s = 3.0 * v_0 * safe_divide(metadados_parte2.hs, h_init, 0.0)

            cons_vol = v_0 - metadados_parte2.vol_change_f_c - vol_change_s
            cons_void_vol_A = cons_vol - vol_solid
            cons_void_vol_B = vol_solid * metadados_parte2.void_ratio_f

            # (A) Deformação volumétrica lado A
            def calc_vol_strain_A(row):
                # (back_vol_c - back_vol) / (cons_void_vol_A + vol_solid)
                return safe_divide(
                    (back_vol_c - row['back_vol']),
                    (cons_void_vol_A + vol_solid),
                    0.0
                )
            df['vol_strain_A'] = df.apply(calc_vol_strain_A, axis=1)

            # (B) Du (pore pressure excess) = (pore_press_Original - ppc inicial)
            df['du_kpa'] = df['pore_press_Original'] - metadados_parte2.pore_press_c

            # (C) Eff radial stress
            df['eff_rad_stress'] = df['rad_press_Original'] - df['pore_press_Original']

            # (D) Área lado A corrigida, dependendo de vol_strain_A e ax_strain
            def calc_cur_area_A(row):
                vs_ = row['vol_strain_A']
                as_ = row['ax_strain']
                return metadados_parte2.consolidated_area_A * safe_divide((1 - vs_), (1 - as_), 0.0)
            df['cur_area_A'] = df.apply(calc_cur_area_A, axis=1)

            # (E) dev_stress_A = load / cur_area_A
            df['dev_stress_A'] = df.apply(
                lambda r: safe_divide(r['load'], r['cur_area_A'], 0.0),
                axis=1
            )
            # Eixo axial efetivo lado A
            df['eff_ax_stress_A'] = df['dev_stress_A'] + df['eff_rad_stress']
            df['eff_camb_A'] = (df['eff_rad_stress']*2.0 + df['eff_ax_stress_A'])/3.0

            # (F) nqp_A = dev_stress_A / eff_camb_A
            df['nqp_A'] = df.apply(lambda r: safe_divide(r['dev_stress_A'], r['eff_camb_A'], 0.0), axis=1)
            # (G) m_A = arcsin( (3*nqp) / (6+nqp) ), em graus
            df['m_A'] = df['nqp_A'].apply(
                lambda val: np.degrees(np.arcsin(np.clip((3.0*val)/(6.0+val), -1.0, 1.0)))
            )

            # (H) void_ratio_A
            def calc_void_ratio_A(row):
                # (cons_void_vol_A - (back_vol_c - back_vol_Original)) / vol_solid
                return safe_divide(
                    (cons_void_vol_A - (back_vol_c - row['back_vol_Original'])),
                    vol_solid,
                    0.0
                )
            df['void_ratio_A'] = df.apply(calc_void_ratio_A, axis=1)

            # (I) su_A = dev_stress_A / 2
            df['su_A'] = df['dev_stress_A'] / 2.0

            # -- Lado B --
            def calc_vol_strain_B(row):
                return safe_divide(
                    (back_vol_c - row['back_vol']),
                    (metadados_parte2.cons_void_vol_B + vol_solid),
                    0.0
                )
            df['vol_strain_B'] = df.apply(calc_vol_strain_B, axis=1)

            def calc_cur_area_B(row):
                vs_b = row['vol_strain_B']
                as_  = row['ax_strain']
                return metadados_parte2.consolidated_area_B * safe_divide((1 - vs_b), (1 - as_), 0.0)
            df['cur_area_B'] = df.apply(calc_cur_area_B, axis=1)

            df['dev_stress_B'] = df.apply(
                lambda r: safe_divide(r['load'], r['cur_area_B'], 0.0),
                axis=1
            )
            df['eff_ax_stress_B'] = df['dev_stress_B'] + df['eff_rad_stress']
            df['eff_camb_B'] = (df['eff_rad_stress']*2.0 + df['eff_ax_stress_B'])/3.0
            df['nqp_B'] = df.apply(lambda r: safe_divide(r['dev_stress_B'], r['eff_camb_B'], 0.0), axis=1)
            df['m_B'] = df['nqp_B'].apply(
                lambda val: np.degrees(np.arcsin(np.clip((3.0*val)/(6.0+val), -1.0, 1.0)))
            )

            def calc_void_ratio_B(row):
                return safe_divide(
                    (metadados_parte2.cons_void_vol_B - (back_vol_c - row['back_vol_Original'])),
                    vol_solid,
                    0.0
                )
            df['void_ratio_B'] = df.apply(calc_void_ratio_B, axis=1)
            df['su_B'] = df['dev_stress_B'] / 2.0

            # -- Precisamos também de ax_stress, diameter_A, etc. --
            # a) ax_stress = load / cur_area_A (por convenção do lado A)
            df['ax_stress'] = safe_divide(df['load'], df['cur_area_A'].replace(0, np.nan), 0.0)

            # b) diameter_A e diameter_B (2 * sqrt( area * 1e6 / pi ))
            df['diameter_A'] = 2.0 * np.sqrt(df['cur_area_A'].clip(lower=0.0)*1e6 / np.pi)
            df['diameter_B'] = 2.0 * np.sqrt(df['cur_area_B'].clip(lower=0.0)*1e6 / np.pi)

            # c) rad_strain_A e rad_strain_B
            df['rad_strain_A'] = safe_divide((df['diameter_A'] - d_init), d_init, 0.0)*100.0
            df['rad_strain_B'] = safe_divide((df['diameter_B'] - d_init), d_init, 0.0)*100.0

            # d) shear_strain_A e shear_strain_B
            df['shear_strain_A'] = (2.0*(df['ax_strain'] - df['vol_strain_A']))/3.0
            df['shear_strain_B'] = (2.0*(df['ax_strain'] - df['vol_strain_B']))/3.0

            # e) max_shear_stress_A/B
            df['max_shear_stress_A'] = df['dev_stress_A']/2.0
            df['max_shear_stress_B'] = df['dev_stress_B']/2.0

            # f) avg_mean_stress = (ax_stress + rad_press) / 2
            df['avg_mean_stress'] = (df['ax_stress'] + df['rad_press'])/2.0

            # g) avg_eff_stress_A = (eff_ax_stress_A + eff_rad_stress)/2
            df['avg_eff_stress_A'] = (df['eff_ax_stress_A'] + df['eff_rad_stress'])/2.0
            df['avg_eff_stress_B'] = (df['eff_ax_stress_B'] + df['eff_rad_stress'])/2.0

            # h) b_val e excessPWP
            #    b_val não definido => np.nan
            df['b_val'] = np.nan
            df['excessPWP'] = df['pore_press_Original'] - df['back_press']

            # i) Por conveniência, "eff_stress_rat_A" e "eff_stress_rat_B"
            #    se quisermos igualar nqp_A / nqp_B
            df['eff_stress_rat_A'] = df['nqp_A']
            df['eff_stress_rat_B'] = df['nqp_B']

            # 9) Definir columns_to_save, incluindo TODAS as que você listou
            columns_to_save = [
                # Originais
                "stage_no","time_test_start","time_stage_start",
                "rad_press_Original","rad_vol_Original","back_press_Original",
                "back_vol_Original","load_cell_Original","pore_press_Original",
                "ax_disp_Original","ax_force_Original","ax_strain_Original",
                "avg_diam_chg_Original","rad_strain_Original","eff_ax_stress_Original",
                "eff_rad_stress_Original","dev_stress_Original","total_stress_rat_Original",
                "eff_stress_rat_Original","cur_area_Original","shear_strain_Original",
                "camb_p_Original","eff_camb_p_Original","max_shear_stress_Original",
                "vol_change_Original","b_value_Original","mean_stress_Original",

                # Novas (calculadas)
                "ax_strain","ax_force","rad_vol_delta","rad_vol","rad_press",
                "back_press","back_vol_delta","back_vol","ax_disp","ax_disp_delta",
                "cur_area_A","cur_area_B","diameter_A","diameter_B","rad_strain_A","rad_strain_B",
                "height","vol_A","vol_B","vol_strain_A","vol_strain_B","void_ratio_A","void_ratio_B",
                "load","ax_stress","eff_ax_stress_A","eff_ax_stress_B","eff_rad_stress","dev_stress_A",
                "dev_stress_B","eff_stress_rat_A","eff_stress_rat_B","shear_strain_A","shear_strain_B",
                "camb_p_A","camb_p_B","eff_camb_A","eff_camb_B","max_shear_stress_A","max_shear_stress_B",
                "avg_mean_stress","avg_eff_stress_A","avg_eff_stress_B","b_val","excessPWP","su_A","su_B",
                "nqp_B","nqp_A","m_A","m_B","du_kpa"
            ]

            # 10) Garante que as colunas existam
            for c in columns_to_save:
                if c not in df.columns:
                    df[c] = 0.0

            # 11) Limpa e finaliza df_to_save
            df_to_save = df[columns_to_save].copy()
            df_to_save = df_to_save.apply(pd.to_numeric, errors='coerce').fillna(0.0)

            # 12) Atualizar metadados com todos os atributos do METADADOS_PARTE2
            all_attrs = metadados_parte2.get_all_attributes()
            for attr, value in all_attrs.items():
                metadados[attr] = value

            # Debug: exibir dump do METADADOS_PARTE2 se quiser
            metadados_parte2.print_attributes()

            # Retorno final
            return {
                'df': df_to_save,
                'metadados_parte2': metadados_parte2
            }

        except Exception as e:
            print(f"Erro ao processar o arquivo '{gds_file}': {e}")
            return None

    @staticmethod
    def process_table_data_from_dataframe(db_manager, metadados, df):
        """
        Versão caso o DataFrame já esteja lido em 'df' (não precisamos
        abrir o arquivo). A lógica de cálculo é similar, aproveitando
        a classe METADADOS_PARTE2 para obter os valores corrigidos.
        Também define 'height = h_init - ax_disp_Original'.
        """
        try:
            # Copiamos o df para não sobrescrever
            df = df.copy()

            # 1) Ler do dicionário de metadados
            w_0       = safe_float_conversion(metadados.get('w_0', 0))
            w_f       = safe_float_conversion(metadados.get('w_f', 0))
            init_mass = safe_float_conversion(metadados.get('init_mass', 0))
            h_init    = safe_float_conversion(metadados.get('h_init', 1))
            d_init    = safe_float_conversion(metadados.get('d_init', 1))
            spec_grav = safe_float_conversion(metadados.get('spec_grav', 1))

            init_dry_mass = safe_divide(init_mass, (1 + w_0), 0.0)
            v_0           = h_init * (np.pi * (d_init ** 2)/4.0)
            vol_solid     = safe_divide(init_dry_mass*1000.0, spec_grav, 0.0)
            v_w_f         = w_f * init_dry_mass * 1000.0

            # 2) Verificar colunas mínimas
            needed_cols = [
                "rad_press_Original",
                "rad_vol_Original",
                "back_press_Original",
                "back_vol_Original",
                "load_cell_Original",
                "pore_press_Original",
                "ax_disp_Original",
                "ax_force_Original",
            ]
            for col in needed_cols:
                if col not in df.columns:
                    df[col] = 0.0
                else:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # 3) Ajustar colunas derivadas
            df['ax_force'] = df['load_cell_Original']
            df['load']     = df['load_cell_Original']

            df['rad_vol_delta']  = df['rad_vol_Original'].diff().fillna(0.0)
            df['rad_vol_cumsum'] = df['rad_vol_delta'].cumsum()
            df['rad_vol']        = df['rad_vol_cumsum']

            df['rad_press']  = df['rad_press_Original']
            df['back_press'] = df['back_press_Original']

            df['back_vol_delta']  = df['back_vol_Original'].diff().fillna(0.0)
            df['back_vol_cumsum'] = df['back_vol_delta'].cumsum()
            df['back_vol']        = df['back_vol_cumsum']

            df['ax_disp_delta']   = df['ax_disp_Original'].diff().fillna(0.0)
            df['ax_disp_cumsum']  = df['ax_disp_delta'].cumsum()
            df['ax_disp']         = df['ax_disp_cumsum']

            # height = h_init - ax_disp_Original (alterado)
            df['height'] = h_init - df['ax_disp_Original']

            df['vol_A'] = v_0 - df['back_vol']
            df['vol_B'] = v_0 - df['back_vol']

            df['cur_area_A'] = (
                safe_divide(df['vol_A'], df['height'].replace(0, np.nan), 0.0)
            ) * 1e-6

            # 4) Instanciar METADADOS_PARTE2
            cis_parte2 = METADADOS_PARTE2(
                df=df,
                metadados=metadados,
                init_dry_mass=init_dry_mass,
                v_0=v_0,
                vol_solid=vol_solid,
                v_w_f=v_w_f,
                h_init=h_init
            )

            # 5) Ajustar a deformação axial para cisalhamento
            cis_inicial = int(metadados.get("_cis_inicial", 8))

            def calc_ax_strain(row):
                if row['stage_no'] >= cis_inicial:
                    return safe_divide(
                        (row['ax_disp'] - cis_parte2.ax_disp_c),
                        (h_init - row['ax_disp']),
                        0.0
                    )
                else:
                    return safe_divide(row['ax_disp'], h_init, 0.0)

            df['ax_strain'] = df.apply(calc_ax_strain, axis=1)

            # ax_stress = load / cur_area_A
            df['ax_stress'] = safe_divide(df['load'], df['cur_area_A'].replace(0, np.nan), 0.0)

            def calc_vol_strain_A(row):
                if row['stage_no'] >= cis_inicial:
                    return safe_divide(
                        (cis_parte2.back_vol_c - row['back_vol']),
                        (cis_parte2.cons_void_vol_A + vol_solid),
                        0.0
                    )
                else:
                    return safe_divide(row['back_vol'], v_0, 0.0)
                
            def calc_vol_strain_B(row):
                if row['stage_no'] >= cis_inicial:
                    return safe_divide(
                        (cis_parte2.back_vol_c - row['back_vol']),
                        (cis_parte2.cons_void_vol_B + vol_solid),
                        0.0
                    )
                else:
                    return safe_divide(row['back_vol'], v_0, 0.0)                

            df['vol_strain_A'] = df.apply(calc_vol_strain_A, axis=1)
            df['vol_strain_B'] = df.apply(calc_vol_strain_B, axis=1)

            df['dev_stress_A'] = safe_divide(df['load'], df['cur_area_A'].replace(0, np.nan), 0.0)
            df['dev_stress_B'] = df['dev_stress_A']

            df['eff_rad_stress'] = df['rad_press_Original'] - df['pore_press_Original']

            df['camb_p_A'] = ((df['ax_stress'] - df['dev_stress_A'])*2 + df['ax_stress'])/3.0
            df['camb_p_B'] = ((df['ax_stress'] - df['dev_stress_B'])*2 + df['ax_stress'])/3.0

            df['su_A'] = df.apply(
                lambda row: 0.0 if abs(row['camb_p_A']) < 1e-12
                else (row['dev_stress_A']/2.0) / row['camb_p_A'],
                axis=1
            )
            df['su_B'] = df.apply(
                lambda row: 0.0 if abs(row['camb_p_B']) < 1e-12
                else (row['dev_stress_B']/2.0) / row['camb_p_B'],
                axis=1
            )

            df['void_ratio_A'] = safe_divide((df['vol_A'] - vol_solid), vol_solid, 0.0)
            df['void_ratio_B'] = safe_divide((df['vol_B'] - vol_solid), vol_solid, 0.0)

            df['eff_ax_stress_A'] = df['dev_stress_A'] + df['eff_rad_stress']
            df['eff_ax_stress_B'] = df['dev_stress_B'] + df['eff_rad_stress']

            df['eff_camb_A'] = (df['eff_rad_stress']*2.0 + df['eff_ax_stress_A'])/3.0
            df['eff_camb_B'] = (df['eff_rad_stress']*2.0 + df['eff_ax_stress_B'])/3.0

            df['nqp_A'] = safe_divide(df['dev_stress_A'], df['eff_camb_A'], 0.0)
            df['nqp_B'] = safe_divide(df['dev_stress_B'], df['eff_camb_B'], 0.0)

            df['m_A'] = df['nqp_A'].apply(
                lambda val: np.degrees(np.arcsin(np.clip((3.0*val)/(6.0+val), -1.0, 1.0)))
            )
            df['m_B'] = df['nqp_B'].apply(
                lambda val: np.degrees(np.arcsin(np.clip((3.0*val)/(6.0+val), -1.0, 1.0)))
            )

            cis_stage_data = df[df['stage_no'] == cis_inicial]
            if not cis_stage_data.empty and 'pore_press_Original' in cis_stage_data.columns:
                pore_press_cis_first = cis_stage_data['pore_press_Original'].iloc[0]
                df['du_kpa'] = df['pore_press_Original'] - pore_press_cis_first
            else:
                df['du_kpa'] = 0.0

            df['shear_strain_A'] = (
                2.0 * (df['ax_strain'] - df['vol_strain_A'])
            ) / 3.0

            df['shear_strain_B'] = (
                2.0 * (df['ax_strain'] - df['vol_strain_B'])
            ) / 3.0

            df['diameter_A'] = 2.0 * np.sqrt(df['cur_area_A'].clip(lower=0.0)*1e6 / np.pi)
            df['diameter_B'] = df['diameter_A']

            df['b_val'] = np.nan

            df['avg_eff_stress_A'] = (df['eff_ax_stress_A'] + df['eff_rad_stress'])/2.0
            df['avg_eff_stress_B'] = (df['eff_ax_stress_B'] + df['eff_rad_stress'])/2.0
            df['avg_mean_stress']  = (df['ax_stress'] + df['rad_press'])/2.0

            df['rad_strain_A'] = safe_divide((df['diameter_A'] - d_init), d_init, 0.0)*100.0
            df['rad_strain_B'] = df['rad_strain_A']

            df['max_shear_stress_A'] = df['dev_stress_A']/2.0
            df['max_shear_stress_B'] = df['dev_stress_B']/2.0
            df['excessPWP']          = df['pore_press_Original'] - df['back_press']

            columns_to_save = [
                'stage_no','time_test_start','time_stage_start','rad_press_Original',
                'rad_vol_Original','back_press_Original','back_vol_Original',
                'load_cell_Original','pore_press_Original','ax_disp_Original',
                'ax_force_Original','ax_strain_Original','avg_diam_chg_Original',
                'rad_strain_Original','ax_strain_Original_2','eff_ax_stress_Original',
                'eff_rad_stress_Original','dev_stress_Original','total_stress_rat_Original',
                'eff_stress_rat_Original','cur_area_Original','shear_strain_Original',
                'camb_p_Original','eff_camb_p_Original','max_shear_stress_Original',
                'vol_change_Original','b_value_Original','mean_stress_Original','ax_force',
                'load','rad_vol_delta','rad_vol','rad_press','back_press','back_vol_delta',
                'back_vol','ax_disp_delta','ax_disp','height','vol_A','vol_B','cur_area_A',
                'cur_area_B','eff_rad_stress','dev_stress_A','dev_stress_B','ax_stress',
                'ax_strain','vol_strain_A','vol_strain_B','void_ratio_B','void_ratio_A','eff_ax_stress_A',
                'eff_ax_stress_B','eff_stress_rat_A','eff_stress_rat_B','eff_camb_A',
                'eff_camb_B','camb_p_A','camb_p_B','max_shear_stress_A','max_shear_stress_B',
                'excessPWP','du_kpa','nqp_A','nqp_B','m_A','m_B','shear_strain_A','shear_strain_B','diameter_A',
                'diameter_B','b_val','avg_eff_stress_A','avg_eff_stress_B','avg_mean_stress',
                'rad_strain_A','rad_strain_B','su_A','su_B'
            ]
            for col in columns_to_save:
                if col not in df.columns:
                    df[col] = 0.0

            df_to_save = df[columns_to_save].copy()
            df_to_save = df_to_save.fillna(0.0)

            # 6) Atualizar metadados
            all_attrs = cis_parte2.get_all_attributes()
            for attr, value in all_attrs.items():
                metadados[attr] = value

            cis_parte2.print_attributes()

            return {
                'df': df_to_save,
                'metadados_parte2': cis_parte2
            }

        except Exception as e:
            print(f"Erro em process_table_data_from_dataframe: {e}")
            return None