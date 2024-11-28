# PreencherExcel.py

import sqlite3
import os
from openpyxl import load_workbook
import numpy as np
import shutil

def safe_float_conversion(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def gerar_planilha_para_arquivos(arquivos_selecionados, tipo_ensaio_selecionado, metodo):
    # Determinar o modelo de planilha com base no TipoEnsaio
    if tipo_ensaio_selecionado.startswith('TIR'):
        modelo_planilha = r'C:\Users\lgv_v\Documents\LUIZ\Modelo Planilha Final\ModeloPlanilhaFinal_TIR.xlsx'
    elif tipo_ensaio_selecionado.startswith('TER'):
        modelo_planilha = r'C:\Users\lgv_v\Documents\LUIZ\Modelo Planilha Final\ModeloPlanilhaFinal_TER.xlsx'
    else:
        print(f"TipoEnsaio '{tipo_ensaio_selecionado}' não reconhecido.")
        return

    if not os.path.exists(modelo_planilha):
        print(f"O modelo de planilha não foi encontrado em: {modelo_planilha}")
        return

    # Copiar o modelo para criar a nova planilha
    novo_arquivo = os.path.join(
        r'C:\Users\lgv_v\Documents\LUIZ\Modelo Planilha Final',
        f'Planilha_Preenchida_{tipo_ensaio_selecionado}_{metodo}.xlsx'
    )
    shutil.copy(modelo_planilha, novo_arquivo)

    # Abrir o workbook
    wb = load_workbook(novo_arquivo)

    db_path = r'C:\Users\lgv_v\Documents\LUIZ\Laboratorio_Geotecnia.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if not arquivos_selecionados:
        print("Nenhum arquivo selecionado para gerar a planilha.")
        conn.close()
        return

    # Dicionário para mapear índices a letras (A, B, C, D, E)
    letras = ['A', 'B', 'C', 'D', 'E']

    for idx, arquivo in enumerate(arquivos_selecionados):
        if idx >= len(letras):
            print(f"Mais de {len(letras)} arquivos selecionados. Apenas os primeiros {len(letras)} serão processados.")
            break

        # Nome da folha correspondente
        sheet_name = f"CP {letras[idx]} Data"

        # Verificar se a folha já existe
        if sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
        else:
            print(f"A planilha não contém a aba '{sheet_name}'.")
            continue

        # Recuperar id_ensaio
        cursor.execute("SELECT id_ensaio FROM Ensaio WHERE NomeCompleto = ?", (arquivo,))
        result = cursor.fetchone()
        if not result:
            print(f"Não foi possível encontrar id_ensaio para o arquivo {arquivo}")
            continue
        id_ensaio = result[0]

        # Recuperar metadados
        cursor.execute("""
            SELECT m.metadados, ma.valor_metadados
            FROM MetadadosArquivo ma
            JOIN Metadados m ON ma.id_metadados = m.id_metadados
            WHERE ma.NomeCompleto = ?
        """, (arquivo,))
        metadados = dict(cursor.fetchall())

        # Obter os estágios dos metadados
        try:
            B_stage = int(metadados['B'])
            Adensamento_stage = int(metadados['Adensamento'])
            Cisalhamento_stage = int(metadados['Cisalhamento'])
        except KeyError as e:
            print(f"Estágio '{e.args[0]}' não encontrado nos metadados do arquivo {arquivo}.")
            continue
        except ValueError:
            print(f"Valores inválidos para os estágios nos metadados do arquivo {arquivo}.")
            continue

        # Recuperar dados de EnsaiosTriaxiais
        cursor.execute("""
            SELECT *
            FROM EnsaiosTriaxiais
            WHERE id_ensaio = ?
        """, (id_ensaio,))
        ensaio_data = cursor.fetchall()
        if not ensaio_data:
            print(f"Nenhum dado encontrado para id_ensaio {id_ensaio}")
            continue
        colunas = [description[0] for description in cursor.description]

        data_dict = {col: [] for col in colunas}
        for row in ensaio_data:
            for col, value in zip(colunas, row):
                data_dict[col].append(safe_float_conversion(value))

        def get_stage_data(stage_number):
            indices = [i for i, val in enumerate(data_dict['stage_no']) if val == stage_number]
            if not indices:
                print(f"Nenhum dado encontrado para o estágio {stage_number} no arquivo {arquivo}")
                return {}
            stage_data = {col: [data_dict[col][i] for i in indices] for col in colunas}
            return stage_data

        B_data = get_stage_data(B_stage)
        adensamento_data = get_stage_data(Adensamento_stage)
        cisalhamento_data = get_stage_data(Cisalhamento_stage)

        if not B_data or not adensamento_data or not cisalhamento_data:
            print(f"Dados incompletos para o arquivo {arquivo}")
            continue

        # Preencher dados do estágio B
        b_rows = len(B_data.get('time_stage_start', []))
        for i in range(b_rows):
            sheet.cell(row=10 + i, column=1, value=B_data.get('time_stage_start', [])[i])  # A10 em diante
            sheet.cell(row=10 + i, column=3, value=B_data.get('rad_press_Original', [])[i])  # C10 em diante
            sheet.cell(row=10 + i, column=4, value=B_data.get('back_press_Original', [])[i])  # D10 em diante
            sheet.cell(row=10 + i, column=5, value=B_data.get('pore_press_Original', [])[i])  # E10 em diante

        # Preencher dados do estágio de Adensamento
        ad_rows = len(adensamento_data.get('stage_no', []))
        ad_columns = [
            'stage_no', 'time_test_start', 'time_stage_start', 'rad_press_Original', 'rad_vol_Original',
            'back_press_Original', 'back_vol_Original', 'load_cell_Original', 'pore_press_Original', 'ax_disp_Original'
        ]
        ad_column_indices = [38, 39, 40, 41, 42, 43, 44, 45, 46, 47]  # Colunas AL(38) a AU(47)

        for idx_row in range(ad_rows):
            for idx_col, col_name in enumerate(ad_columns):
                value = adensamento_data.get(col_name, [])[idx_row]
                sheet.cell(row=7 + idx_row, column=ad_column_indices[idx_col], value=value)

        # Preencher dados do estágio de Cisalhamento
        cis_rows = len(cisalhamento_data.get('stage_no', []))

        # Calcular pore_press_0 como o primeiro valor de pore_press_Original no estágio de cisalhamento
        pore_press_0 = cisalhamento_data.get('pore_press_Original', [0])[0]

        # Calcular eff_rad_stress = rad_press_Original - pore_press_Original
        eff_rad_stress = [rad_p - pore_p for rad_p, pore_p in zip(
            cisalhamento_data.get('rad_press_Original', []),
            cisalhamento_data.get('pore_press_Original', [])
        )]

        # Calcular eff_ax_stress_B = dev_stress_B + eff_rad_stress
        dev_stress_B = cisalhamento_data.get('dev_stress_B', [])
        eff_ax_stress_B = [dev + eff_rad for dev, eff_rad in zip(dev_stress_B, eff_rad_stress)]

        # Calcular stress_ratio = eff_ax_stress_B / eff_rad_stress
        stress_ratio = [ea / er if er != 0 else None for ea, er in zip(eff_ax_stress_B, eff_rad_stress)]

        # Calcular pore_press_diff = pore_press_Original - pore_press_0
        pore_press_diff = [pp - pore_press_0 for pp in cisalhamento_data.get('pore_press_Original', [])]

        # Calcular eff_stress_avg = (eff_ax_stress_B + eff_rad_stress)/2
        eff_stress_avg = [(ea + er)/2 for ea, er in zip(eff_ax_stress_B, eff_rad_stress)]

        # Calcular eff_stress_diff = (eff_ax_stress_B - eff_rad_stress)/2
        eff_stress_diff = [(ea - er)/2 for ea, er in zip(eff_ax_stress_B, eff_rad_stress)]

        # Ajustar back_vol_Original subtraindo o primeiro valor no estágio
        back_vol_Original = cisalhamento_data.get('back_vol_Original', [])
        if back_vol_Original:
            first_back_vol_Original = back_vol_Original[0]
            adjusted_back_vol_Original = [value - first_back_vol_Original for value in back_vol_Original]
        else:
            adjusted_back_vol_Original = []

        # Ajustar ax_disp_Original subtraindo o primeiro valor no estágio
        ax_disp_Original = cisalhamento_data.get('ax_disp_Original', [])
        if ax_disp_Original:
            first_ax_disp_Original = ax_disp_Original[0]
            adjusted_ax_disp_Original = [value - first_ax_disp_Original for value in ax_disp_Original]
        else:
            adjusted_ax_disp_Original = []

        # Utilizar ax_strain sem multiplicar por 100
        ax_strain_percent = cisalhamento_data.get('ax_strain', [])

        # Calcular Corrected Deviator Stress (q) = dev_stress_B
        corrected_deviator_stress = dev_stress_B

        # Preparar dados para preenchimento
        cis_data = {
            'time_stage_start': cisalhamento_data.get('time_stage_start', []),
            'time_stage_start_div_60': [t / 60 for t in cisalhamento_data.get('time_stage_start', [])],
            'rad_press_Original': cisalhamento_data.get('rad_press_Original', []),
            'back_press_Original': cisalhamento_data.get('back_press_Original', []),
            'pore_press_Original': cisalhamento_data.get('pore_press_Original', []),
            'adjusted_back_vol_Original': adjusted_back_vol_Original,
            'adjusted_ax_disp_Original': adjusted_ax_disp_Original,
            'load_cell_Original': cisalhamento_data.get('load_cell_Original', []),
            'ax_strain_percent': ax_strain_percent,
            'corrected_deviator_stress': corrected_deviator_stress,
            'stress_ratio': stress_ratio,
            'pore_press_diff': pore_press_diff,
            'eff_stress_avg': eff_stress_avg,
            'eff_stress_diff': eff_stress_diff
        }

        # Colunas a serem preenchidas e seus índices de coluna no Excel
        cis_column_names = [
            'time_stage_start',                  # R7
            'time_stage_start_div_60',           # S7
            'rad_press_Original',                # T7
            'back_press_Original',               # U7
            'pore_press_Original',               # V7
            'adjusted_back_vol_Original',        # W7
            'adjusted_ax_disp_Original',         # X7
            'load_cell_Original',                # Y7
            'ax_strain_percent',                 # Z7
            'corrected_deviator_stress',         # AA7
            'stress_ratio',                      # AB7
            'pore_press_diff',                   # AC7
            'eff_stress_avg',                    # AD7
            'eff_stress_diff'                    # AE7
        ]
        cis_column_indices = [18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]  # R(18) a AE(31)

        cis_rows_to_fill = len(cis_data['time_stage_start'])

        # Preencher os dados nas células especificadas
        for idx_row in range(cis_rows_to_fill):
            for idx_col, col_name in enumerate(cis_column_names):
                value_list = cis_data[col_name]
                if idx_row < len(value_list):
                    value = value_list[idx_row]
                else:
                    value = None
                sheet.cell(row=7 + idx_row, column=cis_column_indices[idx_col], value=value)

    # Salvar e fechar o workbook
    wb.save(novo_arquivo)
    wb.close()
    conn.close()
    print(f"Planilha gerada com sucesso: {novo_arquivo}")
