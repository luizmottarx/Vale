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
        # Preencher células AL7 a AU7 (colunas 38 a 47) com dados do estágio de adensamento
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

        # Calcula pore_press_0 como o primeiro valor de pore_press_Original no estágio de cisalhamento
        pore_press_0 = cisalhamento_data.get('pore_press_Original', [0])[0]

        # Redução de dados para o estágio de Cisalhamento
        cis_data_length = cis_rows

        # Obter os dados do estágio de cisalhamento
        cis_columns = [
            'time_test_start', 'rad_press_Original', 'back_press_Original', 'pore_press_Original',
            'cur_area_A' if metodo == 'A' else 'cur_area_Original', 'ax_disp_Original', 'load_cell_Original',
            'ax_strain_Original', 'dev_stress_Original'
        ]

        # Calcula eff_ax_stress e eff_rad_press
        eff_ax_stress = []
        eff_rad_press = []

        for i in range(cis_rows):
            load_cell = cisalhamento_data.get('load_cell_Original', [])[i]
            rad_press = cisalhamento_data.get('rad_press_Original', [])[i]
            pore_press = cisalhamento_data.get('pore_press_Original', [])[i]
            eff_ax = load_cell - pore_press
            eff_rad = rad_press - pore_press
            eff_ax_stress.append(eff_ax)
            eff_rad_press.append(eff_rad)

        # Cálculos adicionais
        time_test_start = cisalhamento_data.get('time_test_start', [])
        time_test_start_div_60 = [t / 60 for t in time_test_start]
        eff_ax_stress_div_eff_rad_press = [ea / er if er != 0 else None for ea, er in zip(eff_ax_stress, eff_rad_press)]
        pore_press_diff = [pore_press_0 - pp for pp in cisalhamento_data.get('pore_press_Original', [])]
        eff_stress_avg = [(ea + er) / 2 for ea, er in zip(eff_ax_stress, eff_rad_press)]
        eff_stress_diff = [(ea - er) / 2 for ea, er in zip(eff_ax_stress, eff_rad_press)]

        # Prepare data for filling
        cis_data = {
            'time_test_start': time_test_start,
            'time_test_start_div_60': time_test_start_div_60,
            'rad_press_Original': cisalhamento_data.get('rad_press_Original', []),
            'back_press_Original': cisalhamento_data.get('back_press_Original', []),
            'pore_press_Original': cisalhamento_data.get('pore_press_Original', []),
            'cur_area': cisalhamento_data.get('cur_area_A' if metodo == 'A' else 'cur_area_Original', []),
            'ax_disp_Original': cisalhamento_data.get('ax_disp_Original', []),
            'load_cell_Original': cisalhamento_data.get('load_cell_Original', []),
            'ax_strain_Original': cisalhamento_data.get('ax_strain_Original', []),
            'dev_stress_Original': cisalhamento_data.get('dev_stress_Original', []),
            'eff_ax_stress_div_eff_rad_press': eff_ax_stress_div_eff_rad_press,
            'pore_press_diff': pore_press_diff,
            'eff_stress_avg': eff_stress_avg,
            'eff_stress_diff': eff_stress_diff
        }

        # Redução dos dados conforme especificado
        # Obter as primeiras 30 linhas
        first_30_indices = list(range(min(30, cis_data_length)))
        # Restante dos dados
        remaining_indices = list(range(30, cis_data_length))

        # Dividir o restante dos dados em 10 partes e selecionar a primeira linha de cada parte
        num_parts = 10
        if remaining_indices:
            indices_per_part = max(len(remaining_indices) // num_parts, 1)
            sampled_indices = [remaining_indices[i * indices_per_part] for i in range(num_parts) if i * indices_per_part < len(remaining_indices)]
        else:
            sampled_indices = []

        # Combinar os índices
        cis_indices = first_30_indices + sampled_indices

        # Ordenar os índices
        cis_indices.sort()

        # Colunas a serem preenchidas e seus índices de coluna no Excel
        cis_column_names = [
            'time_test_start', 'time_test_start_div_60', 'rad_press_Original', 'back_press_Original',
            'pore_press_Original', 'cur_area', 'ax_disp_Original', 'load_cell_Original', 'ax_strain_Original',
            'dev_stress_Original', 'eff_ax_stress_div_eff_rad_press', 'pore_press_diff', 'eff_stress_avg',
            'eff_stress_diff'
        ]
        cis_column_indices = [18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]  # R(18) a AE(31)

        # Preencher os dados nas células especificadas
        for idx_row, data_idx in enumerate(cis_indices):
            for idx_col, col_name in enumerate(cis_column_names):
                value = cis_data[col_name][data_idx]
                sheet.cell(row=7 + idx_row, column=cis_column_indices[idx_col], value=value)

    # Salvar e fechar o workbook
    wb.save(novo_arquivo)
    wb.close()
    conn.close()
    print(f"Planilha gerada com sucesso: {novo_arquivo}")
