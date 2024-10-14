# teste3.py

import os
import pandas as pd
import numpy as np
from testeBD import process_file_for_db, safe_float_conversion

class TableProcessor:
    @staticmethod
    def process_table_data(metadados, gds_file):
        try:
            # Ler o arquivo .gds pulando as primeiras 57 linhas
            df = pd.read_csv(gds_file, encoding='latin-1', skiprows=57)
            df = df.rename(columns=lambda x: x.strip())
            original_headers = df.columns.tolist()

            # Mapear os nomes das colunas originais para nomes padronizados
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
                original_headers[22]: 'camb_p_A',
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

            # Ler valores dos metadados
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

            # Cálculos iniciais
            init_dry_mass = init_mass / (1 + w_0)
            v_0 = h_init * np.pi * (d_init ** 2) / 4
            vol_solid = init_dry_mass * 1000 / spec_grav
            v_w_f = w_f * init_dry_mass * 1000

            # Cálculo da força axial
            #df['ax_force'] = np.where(df['time_test_start'] == 0, 0, df['load_cell_Original'])
            df['ax_force'] =  df['load_cell_Original']

            # Variação e acúmulo de volume radial
            df['rad_vol_delta'] = np.where(df['time_test_start'] == 0, 0, df['rad_vol_Original'].diff().fillna(0))
            df['rad_vol'] = np.where(df['time_test_start'] == 0, 0, df['rad_vol_delta'].cumsum())

            # Pressões
            df['rad_press'] = df['rad_press_Original']
            df['back_press'] = df['back_press_Original']

            # Variação e acúmulo de volume de retorno
            df['back_vol_delta'] = np.where(df['time_test_start'] == 0, 0, df['back_vol_Original'].diff().fillna(0))
            df['back_vol'] = np.where(df['time_test_start'] == 0, 0, df['back_vol_delta'].cumsum())

            # Variação e acúmulo de deslocamento axial
            df['ax_disp_delta'] = np.where(df['time_test_start'] == 0, 0, df['ax_disp_Original'].diff().fillna(0))
            df['ax_disp'] = np.where(df['time_test_start'] == 0, 0, df['ax_disp_delta'].cumsum())

            # Cálculo da altura
            df['height'] = h_init - df['ax_disp']

            # Cálculo de vol_A e vol_B iniciais
            df['vol_A'] = v_0 - df['back_vol']
            df['vol_B'] = v_0 - df['back_vol']

            # Cálculo da área atual A inicial
            df['cur_area_A'] = df['vol_A'] / df['height']

            # Cálculo da área atual B inicial
            df['cur_area_B'] = df['vol_B'] / df['height']

            # Cálculo de void_ratio_B inicial
            df['void_ratio_B'] = (df['vol_B'] - vol_solid) / vol_solid

            # Cálculo da tensão efetiva radial
            df['eff_rad_stress'] = df['rad_press'] - df['pore_press_Original']

            # Cálculo da tensão desviadora A e B iniciais
            df['dev_stress_A'] =  df['load_cell_Original'] / (df['cur_area_A'] / 1000000)
            df['dev_stress_B'] =  df['load_cell_Original'] / (df['cur_area_B'] / 1000000)

            # Instanciar METADADOS_PARTE2 com df e metadados após cálculos iniciais
            metadados_parte2 = METADADOS_PARTE2(df, metadados, init_dry_mass, v_0, vol_solid, v_w_f)

            # Cálculo da tensão axial após a instância de METADADOS_PARTE2
            df['ax_stress'] = np.where(
                df['stage_no'] < Cisalhamento_stage,
                metadados_parte2.h_init_c / h_init,
                metadados_parte2.h_init_c - h_init / h_init
            )

            # Cálculos modificados para 'ax_strain' e 'vol_strain'
            df['ax_strain'] = np.where(
                df['stage_no'] < Cisalhamento_stage,
                df['ax_disp'] / h_init,
                ((-metadados_parte2.ax_disp_c) + df['ax_disp']) / (h_init - df['ax_disp'])
            )

            df['vol_strain'] = np.where(
                df['stage_no'] < Cisalhamento_stage,
                df['back_vol'] / v_0,
                (-df['back_vol'] + metadados_parte2.back_vol_c) / metadados_parte2.v_c_B
            )

            # Atualizar cálculos com base nos metadados atualizados
            # Recalcular vol_A e vol_B com base nos estágios
            df['vol_A'] = np.where(
                df['stage_no'] < Cisalhamento_stage,
                v_0 - df['back_vol'],
                metadados_parte2.v_c_A - df['back_vol']
            )
            df['vol_B'] = np.where(
                df['stage_no'] < Cisalhamento_stage,
                v_0 - df['back_vol'],
                metadados_parte2.v_c_B - (df['back_vol'] - metadados_parte2.back_vol_c)
            )

            # Recalcular cur_area_B com condição
            df['cur_area_B'] = np.where(
                df['stage_no'] < Cisalhamento_stage,
                df['vol_B'] / df['height'],
                metadados_parte2.consolidated_area * (1 - df['vol_strain']) / (1 - df['ax_strain'])
            )

             # Recalcular cur_area_A com condição
            df['cur_area_A'] = np.where(
                df['stage_no'] < Cisalhamento_stage,
                df['vol_A'] / df['height'],
                df['vol_A'] / df['height']
            )

            # Recalcular void_ratio_B
            df['void_ratio_B'] = (df['vol_B'] - vol_solid) / vol_solid
            # Recalcular void_ratio_B
            df['void_ratio_A'] = (df['vol_A'] - vol_solid) / vol_solid

            df['eff_ax_stress_A'] = df['dev_stress_A'] + df['eff_rad_stress']
            df['eff_ax_stress_B'] = df['dev_stress_B'] + df['eff_rad_stress']

            df['eff_stress_rat_A'] = df['eff_ax_stress_A'] / df['eff_rad_stress']
            df['eff_stress_rat_B'] = df['eff_ax_stress_B'] / df['eff_rad_stress']

            df['eff_camb_A'] = (df['eff_rad_stress'] + df['eff_rad_stress'] + df['eff_ax_stress_A']) / 3
            df['eff_camb_B'] = (df['eff_rad_stress'] + df['eff_rad_stress'] + df['eff_ax_stress_B']) / 3

            # Recalcular camb_p_A e camb_p_B com base nos novos valores
            df['camb_p_A'] = ((df['ax_stress'] - df['dev_stress_A']) * 2 + df['ax_stress']) / 3
            df['camb_p_B'] = ((df['ax_stress'] - df['dev_stress_B']) * 2 + df['ax_stress']) / 3

            # Recalcular max_shear_stress_A e max_shear_stress_B
            df['max_shear_stress_A'] = df['dev_stress_A'] / 2
            df['max_shear_stress_B'] = df['dev_stress_B'] / 2

            # Excesso de pressão de poros
            df['excess_PWP'] = df['pore_press_Original'] - df['back_press']

            # Resistência não drenada
            #df['su_A'] = df['max_shear_stress_A'] / metadados_parte2.camb_p_A
            #df['su_B'] = df['max_shear_stress_B'] / metadados_parte2.camb_p_B

            df['du_kpa_A'] = df['pore_press_Original'] - metadados_parte2.pore_press_0
            df['du_kpa_B'] = df['pore_press_Original'] - metadados_parte2.pore_press_0

            df['nqp_A'] = df['dev_stress_A'] / df['eff_camb_A']
            df['nqp_B'] = df['dev_stress_B'] / df['eff_camb_B']

            df['m_A'] = metadados_parte2.vol_solid / df['void_ratio_A']
            df['m_B'] = metadados_parte2.vol_solid / df['void_ratio_B']

            df['shear_strain'] = df['dev_stress_A'] / df['eff_ax_stress_A']

            df['diameter_A'] = 2 * np.sqrt(df['cur_area_A'] / np.pi)
            df['diameter_B'] = 2 * np.sqrt(df['cur_area_B'] / np.pi)

            df['b_val'] = np.where(
            df['stage_no'] == B_stage,
            (metadados_parte2.rad_press_0 - df['rad_press']) / (metadados_parte2.pore_press_0 - df['pore_press_Original']),
            "null")

            df['avg_eff_stress_A'] = (df['eff_ax_stress_A'] + df['eff_rad_stress']) / 2
            df['avg_eff_stress_B'] = (df['eff_ax_stress_B'] + df['eff_rad_stress']) / 2

            df['avg_mean_stress'] = (df['ax_stress'] + df['rad_press']) / 2

            # Salvar no banco de dados
            process_file_for_db(df, os.path.basename(gds_file), metadados)

            print(f"Dados processados e salvos no banco de dados para o arquivo: {os.path.basename(gds_file)}")

            # Adicionando o print dos metadados calculados
            #print("\nValores dos metadados calculados:")
            metadados_parte2.print_attributes()

            # Retornar a instância de metadados_parte2
            return metadados_parte2

        except Exception as e:
            print(f"Erro ao processar o arquivo '{gds_file}': {e}")

class CisalhamentoData:
    def __init__(self, df, metadados):
        # Obter o estágio de cisalhamento dinamicamente dos metadados
        self.Cisalhamento_stage = int(metadados.get("Cisalhamento"))
        
        # Filtrar os dados pelo estágio de cisalhamento
        self.df_cisalhamento = df[df['stage_no'] == self.Cisalhamento_stage]

        # Certificar-se de que os dados do estágio de cisalhamento estão presentes
        if self.df_cisalhamento.empty:
            raise ValueError(f"Nenhum dado encontrado para o estágio de Cisalhamento ({self.Cisalhamento_stage}).")

        # Declarar as colunas necessárias
        self.ax_strain = self.df_cisalhamento['ax_strain_Original']
        self.dev_stress_A = self.df_cisalhamento['dev_stress_A']  # Usar 'dev_stress_A'
        self.dev_stress_B = self.df_cisalhamento['dev_stress_B']  # Usar 'dev_stress_B'
        self.vol_strain = self.df_cisalhamento['vol_strain']
        self.eff_camb_A = self.df_cisalhamento['eff_camb_A']
        self.eff_camb_B = self.df_cisalhamento['eff_camb_B']
        self.du_kpa_A = self.df_cisalhamento['du_kpa_A']
        self.du_kpa_B = self.df_cisalhamento['du_kpa_B']
        self.void_ratio_A = self.df_cisalhamento['void_ratio_A']
        self.void_ratio_B = self.df_cisalhamento['void_ratio_B']
        self.nqp_A = self.df_cisalhamento['nqp_A']
        self.nqp_B = self.df_cisalhamento['nqp_B']
        self.m_A = self.df_cisalhamento['m_A']
        self.m_B = self.df_cisalhamento['m_B']

#       void_ratio_A * eff_camb_A e void_ratio_B *  eff_camb_B. ok
#       dev_stress_A * eff_camb_A e dev_stress_B *  eff_camb_B. ok
#       nqp_A        * ax_strain e nqp_B         *  ax_strain.  ok

    def get_cisalhamento_data(self):
        return {
            "ax_strain": self.ax_strain,
            "dev_stress_A": self.dev_stress_A,
            "dev_stress_B": self.dev_stress_B,
            "vol_strain": self.vol_strain,
            "eff_camb_A": self.eff_camb_A,
            "eff_camb_B": self.eff_camb_B,
            "du_kpa_A": self.du_kpa_A,
            "du_kpa_B": self.du_kpa_B,
            "void_ratio_A" : self.void_ratio_A,
            "void_ratio_B" : self.void_ratio_B,
            "nqp_A" : self.nqp_A,
            "nqp_B" : self.nqp_B,
            "m_A" : self.m_A,
            "m_B" : self.m_B
        }


class METADADOS_PARTE2:
    def __init__(self, df, metadados, init_dry_mass, v_0, vol_solid, v_w_f):
        def safe_divide(numerator, denominator, default_value=0):
            try:
                return numerator / denominator if denominator != 0 else default_value
            except ZeroDivisionError:
                return default_value

        # Variáveis diretas dos metadados
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

        # Valores calculados
        self.init_dry_mass = init_dry_mass
        self.v_0 = v_0
        self.vol_solid = vol_solid
        self.v_w_f = v_w_f

        self.ax_disp_0 = 0
        self.back_vol_0 = 0
        self.back_press_0 = df['back_press_Original'].iloc[0] if not df.empty else 0
        self.rad_press_0 = df['rad_press_Original'].iloc[0] if not df.empty else 0
        self.pore_press_0 = df['pore_press_Original'].iloc[0] if not df.empty else 0

        ad_stage_data = df[df['stage_no'] == self.Adensamento].copy()
        cis_stage_data = df[df['stage_no'] == self.Cisalhamento].copy()
        b_stage_data = df[df['stage_no'] == self.B].copy()

        if ad_stage_data.empty:
            raise ValueError(f"Nenhum dado encontrado para o estágio de Adensamento ({self.Adensamento}). Verifique se o valor está correto.")

        # ax_disp_c da coluna 'ax_disp', último valor do estágio de adensamento
        self.ax_disp_c = ad_stage_data['ax_disp'].iloc[-1]
        # back_vol_c da coluna 'back_vol', último valor do estágio de adensamento
        self.back_vol_c = ad_stage_data['back_vol'].iloc[-1]
        # h_init_c da coluna 'height', último valor do estágio de adensamento
        self.h_init_c = ad_stage_data['height'].iloc[-1]

        self.back_vol_f = df['back_vol'].iloc[-1] if not df.empty else 0

        # v_c_A e v_c_B
        self.v_c_A = self.v_0 - self.back_vol_c
        self.v_c_B = ((self.back_vol_c - self.back_vol_f) + self.v_w_f) + self.vol_solid

        # w_c_A e w_c_B
        self.w_c_A = self.v_c_A / self.init_dry_mass
        self.w_c_B = self.v_c_B / self.init_dry_mass

        # void_ratio_c da coluna 'void_ratio_B', último valor do estágio de adensamento
        self.void_ratio_c = ad_stage_data['void_ratio_B'].iloc[-1] if 'void_ratio_B' in ad_stage_data.columns else 0

        # void_ratio_f
        self.void_ratio_f = self.spec_grav * self.w_f / self.Saturacao_c

        self.saturacao_c = 1
        self.void_ratio_m = 0  # Conforme solicitado

        # vol_change_c: subtrair primeiro valor - último valor da coluna 'back_vol' do estágio de cisalhamento
        if not cis_stage_data.empty:
            self.vol_change_c = cis_stage_data['back_vol'].iloc[0] - cis_stage_data['back_vol'].iloc[-1]
        else:
            self.vol_change_c = 0

        # vol_change_f_c: pegar o próximo stage do cisalhamento e subtrair primeiro valor - último valor
        next_stage = self.Cisalhamento + 1
        next_stage_data = df[df['stage_no'] == next_stage].copy()
        if not next_stage_data.empty:
            self.vol_change_f_c = next_stage_data['back_vol'].iloc[0] - next_stage_data['back_vol'].iloc[-1]
        else:
            self.vol_change_f_c = 0

        # cons_void_vol
        self.cons_void_vol = self.v_w_f + (self.back_vol_c - self.back_vol_f)

        # final_void_vol
        self.final_void_vol = self.vol_solid * self.void_ratio_f

        # consolidated_area
        self.consolidated_area = (self.cons_void_vol + self.vol_solid) / self.h_init_c if self.h_init_c else 0

        # camb_p_A e camb_p_B da coluna correspondente, último valor do estágio de adensamento
        self.camb_p_A = ad_stage_data['camb_p_A'].iloc[-1] if 'camb_p_A' in ad_stage_data.columns else 0
        self.camb_p_B = ad_stage_data['camb_p_B'].iloc[-1] if 'camb_p_B' in ad_stage_data.columns else 0
        self.df = df
        
    def print_attributes(self):
        print("========================== VALORES CALCULADOS ==========================")
        for attr, value in vars(self).items():
            print(f"{attr}: {value}")
        print("==========================================================================\n")

# Não é necessário adicionar código no bloco abaixo, pois a interface chama diretamente o método process_table_data
if __name__ == "__main__":
    pass
