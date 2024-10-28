import sqlite3
import os
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
import openpyxl
import numpy as np

def safe_float_conversion(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def gerar_planilha_para_amostra(amostra_selecionada):
    modelo_planilha = r'C:\Users\lgv_v\Documents\LUIZ\Modelo Planilha Final\Modelo_Planilha_Final.xlsx'
    wb = load_workbook(modelo_planilha)
    novo_arquivo = os.path.join(r'C:\Users\lgv_v\Documents\LUIZ\Modelo Planilha Final', f'Planilha_Preenchida_{amostra_selecionada}.xlsx')
    wb.save(novo_arquivo)
    wb = load_workbook(novo_arquivo)

    db_path = r'C:\Users\lgv_v\Documents\LUIZ\Laboratorio_Geotecnia.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT e.NomeCompleto
        FROM Ensaio e
        JOIN Amostra a ON e.id_amostra = a.id_amostra
        WHERE a.amostra = ?
    """, (amostra_selecionada,))
    arquivos = [row[0] for row in cursor.fetchall()]

    if not arquivos:
        conn.close()
        return

    if 'Quadro Resumo' in wb.sheetnames:
        resumo_sheet = wb['Quadro Resumo']
    else:
        resumo_sheet = wb.create_sheet('Quadro Resumo')

    colunas_resumo = [
        "Amostra",
        "Condição de moldagem",
        "Método de preparação",
        "Determinação de umidade final",
        "p'(kpa)- Método A",
        "p'(kpa)- Método B",
        "Gs",
        "e0",
        "eC",
        "eF",
        "su_A_final",
        "su_B_final",
        "su_A_max",
        "su_B_max"
    ]

    for col_num, col_name in enumerate(colunas_resumo, 1):
        resumo_sheet.cell(row=1, column=col_num, value=col_name)

    for row_num, arquivo in enumerate(arquivos, start=2):
        cursor.execute("SELECT id_ensaio FROM Ensaio WHERE NomeCompleto = ?", (arquivo,))
        result = cursor.fetchone()
        if not result:
            continue
        id_ensaio = result[0]

        cursor.execute("""
            SELECT m.metadados, ma.valor_metadados
            FROM MetadadosArquivo ma
            JOIN Metadados m ON ma.id_metadados = m.id_metadados
            WHERE ma.NomeCompleto = ?
        """, (arquivo,))
        metadados = dict(cursor.fetchall())

        spec_grav = safe_float_conversion(metadados.get('spec_grav', 0))
        init_void_ratio = safe_float_conversion(metadados.get('init_void_ratio', 0))
        post_cons_void = safe_float_conversion(metadados.get('post_cons_void', 0))
        w_f = safe_float_conversion(metadados.get('w_f', 0))

        eF = spec_grav * w_f

        cursor.execute("""
            SELECT *
            FROM EnsaiosTriaxiais
            WHERE id_ensaio = ?
        """, (id_ensaio,))
        ensaio_data = cursor.fetchall()
        colunas = [description[0] for description in cursor.description]

        data_dict = {col: [] for col in colunas}
        for row in ensaio_data:
            for col, value in zip(colunas, row):
                data_dict[col].append(safe_float_conversion(value))

        B_stage = int(metadados.get('B', 5))
        Adensamento_stage = int(metadados.get('Adensamento', 7))
        Cisalhamento_stage = int(metadados.get('Cisalhamento', 8))

        def get_stage_data(stage_number):
            indices = [i for i, val in enumerate(data_dict['stage_no']) if val == stage_number]
            stage_data = {col: [data_dict[col][i] for i in indices] for col in colunas}
            return stage_data

        adensamento_data = get_stage_data(Adensamento_stage)
        cisalhamento_data = get_stage_data(Cisalhamento_stage)
        B_data = get_stage_data(B_stage)

        p_kpa_metodo_A = adensamento_data.get('eff_camb_A', [0])[0]
        p_kpa_metodo_B = adensamento_data.get('eff_camb_B', [0])[0]

        su_A = cisalhamento_data.get('max_shear_stress_A', [])
        su_B = cisalhamento_data.get('max_shear_stress_B', [])
        eff_camb_A = cisalhamento_data.get('eff_camb_A', [])
        eff_camb_B = cisalhamento_data.get('eff_camb_B', [])

        if su_A and eff_camb_A:
            su_A_final = su_A[-1] / eff_camb_A[0] if eff_camb_A[0] != 0 else 0
            su_A_max = max(su_A) / eff_camb_A[0] if eff_camb_A[0] != 0 else 0
        else:
            su_A_final = su_A_max = 0

        if su_B and eff_camb_B:
            su_B_final = su_B[-1] / eff_camb_B[0] if eff_camb_B[0] != 0 else 0
            su_B_max = max(su_B) / eff_camb_B[0] if eff_camb_B[0] != 0 else 0
        else:
            su_B_final = su_B_max = 0

        resumo_sheet.cell(row=row_num, column=1, value=arquivo)
        resumo_sheet.cell(row=row_num, column=2, value="")
        resumo_sheet.cell(row=row_num, column=3, value="")
        resumo_sheet.cell(row=row_num, column=4, value="")
        resumo_sheet.cell(row=row_num, column=5, value=p_kpa_metodo_A)
        resumo_sheet.cell(row=row_num, column=6, value=p_kpa_metodo_B)
        resumo_sheet.cell(row=row_num, column=7, value=spec_grav)
        resumo_sheet.cell(row=row_num, column=8, value=init_void_ratio)
        resumo_sheet.cell(row=row_num, column=9, value=post_cons_void)
        resumo_sheet.cell(row=row_num, column=10, value=eF)
        resumo_sheet.cell(row=row_num, column=11, value=su_A_final)
        resumo_sheet.cell(row=row_num, column=12, value=su_B_final)
        resumo_sheet.cell(row=row_num, column=13, value=su_A_max)
        resumo_sheet.cell(row=row_num, column=14, value=su_B_max)

        sheet_name = f"{arquivo}"
        sheet_name = sheet_name[:31]
        if sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
        else:
            sheet = wb.create_sheet(sheet_name)

        sheet.merge_cells('A1:F1')
        sheet['A1'] = 'B'
        sheet.merge_cells('H1:R1')
        sheet['H1'] = 'Adensamento'
        sheet.merge_cells('T1:AG1')
        sheet['T1'] = 'Cisalhamento'

        colunas_B = ["Stage Time", "Cell Pressure", "Back Pressure", "Pore Pressure", "B-Value", "Stage Time (min)"]
        for col_num, col_name in enumerate(colunas_B, 1):
            sheet.cell(row=2, column=col_num, value=col_name)

        B_stage_time = B_data.get('time_stage_start', [])
        cell_pressure_B = B_data.get('rad_press', [])
        back_pressure_B = B_data.get('back_press', [])
        pore_pressure_B = B_data.get('pore_press_Original', [])

        b_values = []
        for rp, pp in zip(cell_pressure_B, pore_pressure_B):
            delta_rp = rp - cell_pressure_B[0]
            delta_pp = pp - pore_pressure_B[0]
            b = delta_pp / delta_rp if delta_rp != 0 else 0
            b_values.append(b)

        stage_time_min = [t / 60 for t in B_stage_time]

        for i in range(len(B_stage_time)):
            sheet.cell(row=i+3, column=1, value=B_stage_time[i])
            sheet.cell(row=i+3, column=2, value=cell_pressure_B[i])
            sheet.cell(row=i+3, column=3, value=back_pressure_B[i])
            sheet.cell(row=i+3, column=4, value=pore_pressure_B[i])
            sheet.cell(row=i+3, column=5, value=b_values[i])
            sheet.cell(row=i+3, column=6, value=stage_time_min[i])

        colunas_adensamento = [
            "Stage Number", "Time Since Start of Test (s)", "Time Since Start of Stage (s)",
            "Radial Pressure", "Radial Volume", "Back Pressure", "Back Volume",
            "Load Cell", "Pore Pressure", "Axial Displacement"
        ]
        for col_num, col_name in enumerate(colunas_adensamento, 8):
            sheet.cell(row=2, column=col_num, value=col_name)

        ad_stage_number = adensamento_data.get('stage_no', [])
        time_test_start = adensamento_data.get('time_test_start', [])
        time_stage_start = adensamento_data.get('time_stage_start', [])
        radial_pressure = adensamento_data.get('rad_press', [])
        radial_volume = adensamento_data.get('rad_vol', [])
        back_pressure_ad = adensamento_data.get('back_press', [])
        back_volume = adensamento_data.get('back_vol', [])
        load_cell = adensamento_data.get('load_cell_Original', [])
        pore_pressure_ad = adensamento_data.get('pore_press_Original', [])
        axial_displacement = adensamento_data.get('ax_disp', [])

        for i in range(len(ad_stage_number)):
            sheet.cell(row=i+3, column=8, value=ad_stage_number[i])
            sheet.cell(row=i+3, column=9, value=time_test_start[i])
            sheet.cell(row=i+3, column=10, value=time_stage_start[i])
            sheet.cell(row=i+3, column=11, value=radial_pressure[i])
            sheet.cell(row=i+3, column=12, value=radial_volume[i])
            sheet.cell(row=i+3, column=13, value=back_pressure_ad[i])
            sheet.cell(row=i+3, column=14, value=back_volume[i])
            sheet.cell(row=i+3, column=15, value=load_cell[i])
            sheet.cell(row=i+3, column=16, value=pore_pressure_ad[i])
            sheet.cell(row=i+3, column=17, value=axial_displacement[i])

        colunas_cisalhamento = [
            "Stage Time", "Stage Time", "Cell Pressure", "Back Pressure", "Pore Pressure",
            "Volume Change", "Axial Displacement", "Load Cell", "Axial Strain",
            "Corrected Deviator Stress", "Effective Principal Stress Ratio", "Induced Pore Pressure",
            "p'", "q"
        ]
        for col_num, col_name in enumerate(colunas_cisalhamento, 20):
            sheet.cell(row=2, column=col_num, value=col_name)

        cis_stage_time = cisalhamento_data.get('time_stage_start', [])
        cell_pressure_cis = cisalhamento_data.get('rad_press', [])
        back_pressure_cis = cisalhamento_data.get('back_press', [])
        pore_pressure_cis = cisalhamento_data.get('pore_press_Original', [])
        volume_change = cisalhamento_data.get('vol_change_Original', [])
        axial_displacement_cis = cisalhamento_data.get('ax_disp', [])
        load_cell_cis = cisalhamento_data.get('load_cell_Original', [])
        axial_strain = cisalhamento_data.get('ax_strain', [])
        corrected_deviator_stress = cisalhamento_data.get('dev_stress_A', [])
        effective_principal_stress_ratio = cisalhamento_data.get('eff_stress_rat_A', [])
        induced_pore_pressure = cisalhamento_data.get('excessPWP', [])
        p_prime = cisalhamento_data.get('eff_camb_A', [])
        q = cisalhamento_data.get('max_shear_stress_A', [])

        for i in range(len(cis_stage_time)):
            sheet.cell(row=i+3, column=20, value=cis_stage_time[i])
            sheet.cell(row=i+3, column=21, value=cis_stage_time[i])
            sheet.cell(row=i+3, column=22, value=cell_pressure_cis[i])
            sheet.cell(row=i+3, column=23, value=back_pressure_cis[i])
            sheet.cell(row=i+3, column=24, value=pore_pressure_cis[i])
            sheet.cell(row=i+3, column=25, value=volume_change[i])
            sheet.cell(row=i+3, column=26, value=axial_displacement_cis[i])
            sheet.cell(row=i+3, column=27, value=load_cell_cis[i])
            sheet.cell(row=i+3, column=28, value=axial_strain[i])
            sheet.cell(row=i+3, column=29, value=corrected_deviator_stress[i])
            sheet.cell(row=i+3, column=30, value=effective_principal_stress_ratio[i])
            sheet.cell(row=i+3, column=31, value=induced_pore_pressure[i])
            sheet.cell(row=i+3, column=32, value=p_prime[i])
            sheet.cell(row=i+3, column=33, value=q[i])

    wb.save(novo_arquivo)
    conn.close()
