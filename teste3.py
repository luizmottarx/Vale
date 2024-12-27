# teste3.py

import os
import pandas as pd
import numpy as np
from testeBD import safe_float_conversion

def safe_divide(numerator, denominator, default_value=0.0):
    try:
        return numerator / denominator if denominator != 0 else default_value
    except:
        return default_value

class METADADOS_PARTE2:
    def __init__(self, df, metadados, init_dry_mass, v_0, vol_solid, v_w_f, h_init):
        def safe_div(numerator, denominator, default_value=0):
            try:
                return numerator / denominator if denominator != 0 else default_value
            except ZeroDivisionError:
                return default_value

        # Aqui utilizamos os metadados já mapeados:
        self.w_0 = safe_float_conversion(metadados.get('w_0', 0))
        self.w_f = safe_float_conversion(metadados.get('w_f', 0))
        self.init_mass = safe_float_conversion(metadados.get('init_mass', 0))
        self.h_init = safe_float_conversion(metadados.get('h_init', 1))
        self.d_init = safe_float_conversion(metadados.get('d_init', 1))
        self.spec_grav = safe_float_conversion(metadados.get('spec_grav', 1))
        self.final_moisture = safe_float_conversion(metadados.get('final_moisture', 0))
        self.Saturacao_c = safe_float_conversion(metadados.get('Saturacao_c', 1))
        self.B = int(metadados.get("B", 5))
        self.Adensamento = int(metadados.get("Adensamento", 7))
        self.Cisalhamento = int(metadados.get("Cisalhamento", 8))
        self.fin_mass = safe_float_conversion(metadados.get("fin_mass", 0))
        self.fin_dry_mass = safe_float_conversion(metadados.get("fin_dry_mass", 0))

        self.init_dry_mass = init_dry_mass
        self.v_0 = v_0
        self.vol_solid = vol_solid
        self.v_w_f = v_w_f

        denominator = ((((self.d_init / 10) ** 2) * np.pi) / 4) * (self.h_init / 10)
        self.dry_unit_weight = self.init_dry_mass / denominator if denominator != 0 else 0

        self.init_void_ratio = (self.v_0 - self.vol_solid) / self.vol_solid if self.vol_solid != 0 else 0

        self.init_sat = 0
        if self.init_void_ratio != 0:
            self.init_sat = (self.spec_grav * self.init_dry_mass / self.init_void_ratio) * 100

        self.ax_disp_0 = 0
        self.back_vol_0 = 0
        self.back_press_0 = df['back_press_Original'].iloc[0] if not df.empty else 0
        self.rad_press_0 = df['rad_press_Original'].iloc[0] if not df.empty else 0
        self.pore_press_0 = df['pore_press_Original'].iloc[0] if not df.empty else 0

        ad_stage_data = df[df['stage_no'] == self.Adensamento].copy()
        cis_stage_data = df[df['stage_no'] == self.Cisalhamento].copy()
        b_stage_data = df[df['stage_no'] == self.B].copy()

        if ad_stage_data.empty:
            raise ValueError(f"Nenhum dado encontrado para o estágio de Adensamento ({self.Adensamento}).")

        if b_stage_data.empty:
            raise ValueError(f"Nenhum dado encontrado para o estágio B ({self.B}).")

        if 'back_vol' in b_stage_data.columns and not b_stage_data['back_vol'].empty:
            self.back_vol_0 = b_stage_data['back_vol'].iloc[0]
        else:
            self.back_vol_0 = 0

        if 'ax_disp' in ad_stage_data.columns and not ad_stage_data['ax_disp'].empty:
            self.ax_disp_c = ad_stage_data['ax_disp'].iloc[-1]
        else:
            self.ax_disp_c = 0

        if 'back_vol' in ad_stage_data.columns and not ad_stage_data['back_vol'].empty:
            self.back_vol_c = ad_stage_data['back_vol'].iloc[-1]
        else:
            self.back_vol_c = 0

        if 'height' in ad_stage_data.columns and not ad_stage_data['height'].empty:
            self.h_init_c = ad_stage_data['height'].iloc[-1]
        else:
            self.h_init_c = 0

        if 'back_vol' in df.columns and not df['back_vol'].empty:
            self.back_vol_f = df['back_vol'].iloc[-1]
        else:
            self.back_vol_f = 0

        self.v_c_A = self.v_0 - self.back_vol_c
        self.cons_void_vol = self.v_w_f + (self.back_vol_c - self.back_vol_f)
        self.v_c_B = self.cons_void_vol + self.vol_solid

        self.w_c_A = safe_divide(self.v_c_A, self.init_dry_mass)
        self.w_c_B = safe_divide(self.v_c_B, self.init_dry_mass)

        if 'void_ratio_B' in ad_stage_data.columns and not ad_stage_data['void_ratio_B'].empty:
            self.void_ratio_c = ad_stage_data['void_ratio_B'].iloc[-1]
        else:
            self.void_ratio_c = 0

        self.void_ratio_f = safe_divide(self.spec_grav * self.w_f, self.Saturacao_c)

        self.saturacao_c = 1
        self.void_ratio_m = 0

        if not cis_stage_data.empty and 'back_vol' in cis_stage_data.columns and not cis_stage_data['back_vol'].empty:
            self.vol_change_c = cis_stage_data['back_vol'].iloc[0] - cis_stage_data['back_vol'].iloc[-1]
        else:
            self.vol_change_c = 0

        next_stage = self.Cisalhamento + 1
        next_stage_data = df[df['stage_no'] == next_stage].copy()
        if not next_stage_data.empty and 'back_vol' in next_stage_data.columns and not next_stage_data['back_vol'].empty:
            self.vol_change_f_c = next_stage_data['back_vol'].iloc[0] - next_stage_data['back_vol'].iloc[-1]
        else:
            self.vol_change_f_c = 0

        self.final_void_vol = self.vol_solid * self.void_ratio_f
        self.post_cons_void = safe_divide(self.cons_void_vol, self.vol_solid)
        self.consolidated_area = safe_divide(self.cons_void_vol + self.vol_solid, self.h_init_c) * 0.000001

        if 'camb_p_Original' in ad_stage_data.columns and not ad_stage_data['camb_p_Original'].empty:
            self.camb_p_A0 = ad_stage_data['camb_p_Original'].iloc[-1]
            self.camb_p_B0 = ad_stage_data['camb_p_Original'].iloc[-1]
        else:
            self.camb_p_A0 = 0
            self.camb_p_B0 = 0

    def print_attributes(self):
        print("========================== VALORES CALCULADOS ==========================")
        for attr, value in vars(self).items():
            print(f"{attr}: {value}")
        print("==========================================================================\n")

class CisalhamentoData:
    def __init__(self, df, metadados):
        self.Cisalhamento_stage = int(metadados.get("Cisalhamento", 8))
        self.df_cisalhamento = df[df['stage_no'] == self.Cisalhamento_stage].copy()

        if self.df_cisalhamento.empty:
            raise ValueError(f"Nenhum dado encontrado para o estágio de Cisalhamento ({self.Cisalhamento_stage}).")

        required_columns = [
            'ax_strain', 'dev_stress_A', 'dev_stress_B',
            'vol_strain', 'eff_camb_A', 'eff_camb_B',
            'du_kpa', 'void_ratio_A', 'void_ratio_B',
            'nqp_A', 'nqp_B', 'm_A', 'm_B'
        ]
        missing_columns = [col for col in required_columns if col not in self.df_cisalhamento.columns]
        if missing_columns:
            raise ValueError(f"Colunas faltantes no estágio de Cisalhamento ({self.Cisalhamento_stage}): {missing_columns}")

        self.ax_strain = self.df_cisalhamento['ax_strain']
        self.dev_stress_A = self.df_cisalhamento['dev_stress_A']
        self.dev_stress_B = self.df_cisalhamento['dev_stress_B']
        self.vol_strain = self.df_cisalhamento['vol_strain']
        self.eff_camb_A = self.df_cisalhamento['eff_camb_A']
        self.eff_camb_B = self.df_cisalhamento['eff_camb_B']
        self.du_kpa = self.df_cisalhamento['du_kpa']
        self.void_ratio_A = self.df_cisalhamento['void_ratio_A']
        self.void_ratio_B = self.df_cisalhamento['void_ratio_B']
        self.nqp_A = self.df_cisalhamento['nqp_A']
        self.nqp_B = self.df_cisalhamento['nqp_B']
        self.m_A = self.df_cisalhamento['m_A']
        self.m_B = self.df_cisalhamento['m_B']

    def get_cisalhamento_data(self):
        return {
            "ax_strain": self.ax_strain,
            "dev_stress_A": self.dev_stress_A,
            "dev_stress_B": self.dev_stress_B,
            "vol_strain": self.vol_strain,
            "eff_camb_A": self.eff_camb_A,
            "eff_camb_B": self.eff_camb_B,
            "du_kpa": self.du_kpa,
            "void_ratio_A": self.void_ratio_A,
            "void_ratio_B": self.void_ratio_B,
            "nqp_A": self.nqp_A,
            "nqp_B": self.nqp_B,
            "m_A": self.m_A,
            "m_B": self.m_B
        }

class TableProcessor:
    @staticmethod
    def process_table_data(db_manager, metadados, gds_file):
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
                original_headers[22]: 'camb_p_Original',
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
                raise ValueError(f"Colunas faltantes: {missing_columns}")

            numeric_columns = [
                'rad_press_Original', 'rad_vol_Original', 'back_press_Original',
                'back_vol_Original', 'load_cell_Original', 'pore_press_Original',
                'ax_disp_Original', 'ax_force_Original'
            ]
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')

            w_0 = safe_float_conversion(metadados.get('w_0', 0))
            w_f = safe_float_conversion(metadados.get('w_f', 0))
            init_mass = safe_float_conversion(metadados.get('init_mass', 0))
            h_init = safe_float_conversion(metadados.get('h_init', 1))
            d_init = safe_float_conversion(metadados.get('d_init', 1))
            spec_grav = safe_float_conversion(metadados.get('spec_grav', 1))
            final_moisture = safe_float_conversion(metadados.get('final_moisture', 0))
            Saturacao_c = safe_float_conversion(metadados.get('Saturacao_c', 1))
            B_stage = int(metadados.get("B", 5))
            Adensamento_stage = int(metadados.get("Adensamento", 7))
            Cisalhamento_stage = int(metadados.get("Cisalhamento", 8))
            fin_mass = safe_float_conversion(metadados.get("fin_mass", 0))
            fin_dry_mass = safe_float_conversion(metadados.get("fin_dry_mass", 0))

            init_dry_mass = init_mass / (1 + w_0) if (1 + w_0) != 0 else 0
            v_0 = h_init * np.pi * (d_init ** 2) / 4
            vol_solid = init_dry_mass * 1000 / spec_grav if spec_grav != 0 else 0
            v_w_f = w_f * init_dry_mass * 1000

            df['ax_force'] = df['load_cell_Original']
            df['load'] = df['load_cell_Original']

            df['rad_vol_delta'] = df['rad_vol_Original'].diff().fillna(0)
            df['rad_vol_cumsum'] = df['rad_vol_delta'].cumsum()
            df['rad_vol'] = df['rad_vol_cumsum']

            df['rad_press'] = df['rad_press_Original']
            df['back_press'] = df['back_press_Original']

            df['back_vol_delta'] = df['back_vol_Original'].diff().fillna(0)
            df['back_vol_cumsum'] = df['back_vol_delta'].cumsum()
            df['back_vol'] = df['back_vol_cumsum']

            df['ax_disp_delta'] = df['ax_disp_Original'].diff().fillna(0)
            df['ax_disp_cumsum'] = df['ax_disp_delta'].cumsum()
            df['ax_disp'] = df['ax_disp_cumsum']

            df['height'] = h_init - df['ax_disp']

            df['vol_A'] = v_0 - df['back_vol']
            df['vol_B'] = v_0 - df['back_vol']

            df['cur_area_A'] = (df['vol_A'] / df['height'].replace(0, np.nan)) * 1e-6

            metadados_parte2 = METADADOS_PARTE2(df, metadados, init_dry_mass, v_0, vol_solid, v_w_f, h_init)

            df['ax_strain'] = np.where(
                df['stage_no'] < Cisalhamento_stage,
                df['ax_disp'] / h_init,
                (df['ax_disp'] - metadados_parte2.ax_disp_c) / (h_init - df['ax_disp']).replace(0, np.nan)
            )
            df['ax_strain'] = df['ax_strain'] * 100

            df['ax_stress'] = df['ax_force'] / df['cur_area_A'].replace(0, np.nan)

            df['vol_strain'] = np.where(
                df['stage_no'] < Cisalhamento_stage,
                df['back_vol'] / v_0,
                (metadados_parte2.back_vol_c - df['back_vol']) / (metadados_parte2.cons_void_vol + vol_solid)
            )
            df['vol_strain'] = df['vol_strain'] * 100

            df['vol_A'] = np.where(
                df['stage_no'] < Cisalhamento_stage,
                v_0 - df['back_vol'],
                metadados_parte2.v_c_A - df['back_vol']
            )
            df['vol_B'] = np.where(
                df['stage_no'] < Cisalhamento_stage,
                v_0 - df['back_vol'],
                metadados_parte2.cons_void_vol + vol_solid - (df['back_vol'] - metadados_parte2.back_vol_c)
            )

            df['cur_area_B'] = np.where(
                df['stage_no'] < Cisalhamento_stage,
                (df['vol_B'] / df['height'].replace(0, np.nan)) * 1e-6,
                metadados_parte2.consolidated_area * (
                    (1 - (df['vol_strain'] / 100)) / (1 - (df['ax_strain'] / 100)).replace(0, np.nan)
                )
            )

            df['eff_rad_stress'] = df['rad_press_Original'] - df['pore_press_Original']
            df['dev_stress_A'] = df['load'] / df['cur_area_A'].replace(0, np.nan)
            df['dev_stress_B'] = df['load'] / df['cur_area_B'].replace(0, np.nan)

            df['su_A'] = df['dev_stress_A'] / 2
            df['su_B'] = df['dev_stress_B'] / 2

            df['void_ratio_B'] = (metadados_parte2.cons_void_vol - (metadados_parte2.back_vol_c - df['back_vol'])) / vol_solid if vol_solid != 0 else 0
            df['void_ratio_A'] = (df['vol_A'] - vol_solid) / vol_solid if vol_solid != 0 else 0

            df['eff_ax_stress_A'] = df['dev_stress_A'] + df['eff_rad_stress']
            df['eff_ax_stress_B'] = df['dev_stress_B'] + df['eff_rad_stress']

            df['eff_stress_rat_A'] = df['eff_ax_stress_A'] / df['eff_rad_stress'].replace(0, np.nan)
            df['eff_stress_rat_B'] = df['eff_ax_stress_B'] / df['eff_rad_stress'].replace(0, np.nan)

            df['eff_camb_A'] = (df['eff_rad_stress'] * 2 + df['eff_ax_stress_A']) / 3
            df['eff_camb_B'] = (df['eff_rad_stress'] * 2 + df['eff_ax_stress_B']) / 3

            df['camb_p_A'] = ((df['ax_stress'] - df['dev_stress_A']) * 2 + df['ax_stress']) / 3
            df['camb_p_B'] = ((df['ax_stress'] - df['dev_stress_B']) * 2 + df['ax_stress']) / 3

            df['max_shear_stress_A'] = df['dev_stress_A'] / 2
            df['max_shear_stress_B'] = df['dev_stress_B'] / 2

            df['excessPWP'] = df['pore_press_Original'] - df['back_press']

            cis_stage_data = df[df['stage_no'] == Cisalhamento_stage]
            pore_press_cis_first_value = cis_stage_data['pore_press_Original'].iloc[0] if not cis_stage_data.empty else np.nan
            df['du_kpa'] = df['pore_press_Original'] - pore_press_cis_first_value

            df['nqp_A'] = df['dev_stress_A'] / df['eff_camb_A'].replace(0, np.nan)
            df['nqp_B'] = df['dev_stress_B'] / df['eff_camb_B'].replace(0, np.nan)

            df['m_A'] = np.degrees(
                np.arcsin(
                    ((3 * df['nqp_A']) / (6 + df['nqp_A'])).clip(-1, 1)
                )
            )
            df['m_B'] = np.degrees(
                np.arcsin(
                    ((3 * df['nqp_B']) / (6 + df['nqp_B'])).clip(-1, 1)
                )
            )

            df['shear_strain'] = (2 * ((df['ax_strain'] / 100) - (df['vol_strain'] / 100))) / 3
            df['shear_strain'] = df['shear_strain'] * 100

            df['diameter_A'] = 2 * np.sqrt(df['cur_area_A'].clip(lower=0) * 1e6 / np.pi)
            df['diameter_B'] = 2 * np.sqrt(df['cur_area_B'].clip(lower=0) * 1e6 / np.pi)

            df['b_val'] = np.where(
                df['stage_no'] == B_stage,
                (metadados_parte2.rad_press_0 - df['rad_press']) / (metadados_parte2.pore_press_0 - df['pore_press_Original']).replace(0, np.nan),
                np.nan
            )

            df['avg_eff_stress_A'] = (df['eff_ax_stress_A'] + df['eff_rad_stress']) / 2
            df['avg_eff_stress_B'] = (df['eff_ax_stress_B'] + df['eff_rad_stress']) / 2

            df['avg_mean_stress'] = (df['ax_stress'] + df['rad_press']) / 2

            df['rad_strain_A'] = (df['diameter_A'] - d_init) / d_init * 100
            df['rad_strain_B'] = (df['diameter_B'] - d_init) / d_init * 100

            columns_to_save = [
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
                'max_shear_stress_B', 'excessPWP', 'du_kpa', 'nqp_A', 'nqp_B',
                'm_A', 'm_B', 'shear_strain', 'diameter_A', 'diameter_B',
                'b_val', 'avg_eff_stress_A', 'avg_eff_stress_B', 'avg_mean_stress',
                'rad_strain_A', 'rad_strain_B'
            ]

            missing_columns_to_save = [col for col in columns_to_save if col not in df.columns]
            if missing_columns_to_save:
                raise ValueError(f"Colunas calculadas faltantes para salvar no banco: {missing_columns_to_save}")

            df_to_save = df[columns_to_save].copy()
            df_to_save = df_to_save.apply(pd.to_numeric, errors='coerce').fillna(0.0)

            # Atualizar metadados calculados
            metadados['dry_unit_weight'] = metadados_parte2.dry_unit_weight
            metadados['init_void_ratio'] = metadados_parte2.init_void_ratio
            metadados['init_sat'] = metadados_parte2.init_sat
            metadados['post_cons_void'] = metadados_parte2.post_cons_void

            metadados_parte2.print_attributes()

            return {'df': df_to_save, 'metadados_parte2': metadados_parte2}

        except Exception as e:
            print(f"Erro ao processar o arquivo '{gds_file}': {e}")
            return None
