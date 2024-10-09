# teste2.py

import os

class StageProcessor:
    @staticmethod
    def process_stage_data(directory, gds_file, metadados):
        try:
            # Mapeamento de chaves para nomes internos
            metadados_definidos = {
                "_B": "B",
                "_ad": "Adensamento",
                "_cis": "Cisalhamento",
                "Volume de agua medio inicial":"w_0",
                "Volume de agua medio final":"w_f",
                "Initial Height (mm)": "h_init",
                "Initial Diameter (mm)": "d_init",
                "Ram Diameter": "ram_diam",
                "Specific Gravity (kN/m³):": "spec_grav",
                "Job reference:": "job_ref",
                "Borehole:": "borehole",
                "Sample Name:": "samp_name",
                "Depth:": "depth",
                "Sample Date (dd/mm/yyyy):": "samp_date",
                "Description of Sample:": "samp_desc",
                "Initial mass (g):": "init_mass",
                "Initial dry mass (g):": "init_dry_mass",
                "Specific Gravity (ass/meas):": "spec_grav_am",
                "Date Test Started:": "test_start",
                "Date Test Finished:": "test_end",
                "Specimen Type (dis/undis):": "spec_type",
                "Top Drain Used (y/n):": "top_drain",
                "Base Drain Used (y/n)": "base_drain",
                "Side Drains Used (y/n)": "side_drains",
                "Final Mass:": "fin_mass",
                "Final Dry Mass:": "fin_dry_mass",
                "Machine No.:": "mach_no",
                "Pressure System:": "press_sys",
                "Cell No.:": "cell_no",
                "Ring No.:": "ring_no",
                "Job Location:": "job_loc",
                "Membrane Thickness (mm):": "mem_thick",
                "Test Number:": "test_no",
                "Technician Name:": "tech_name",
                "Sample Liquid Limit (%):": "liq_lim",
                "Sample Plastic Limit (%):": "plas_lim",
                "Average Water Content of Sample Trimmings (%):": "avg_wc_trim",
                "Additional Notes (info source or occurrence and size of large particles etc.):": "notes",
                "% by mass of Sample retained on No. 4 sieve (Gravel):": "mass_no4",
                "% by mass of Sample retained on No. 10 sieve (Coarse Sand):": "mass_no10",
                "% by mass of Sample retained on No. 40 sieve (Medium Sand): ": "mass_no40",
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
                "Specify method to determine post-consolidation specimen area (A/B/A and B):": "post_consol_area",
                "Specify failure criterion (max deviator stress/deviator stress at 15% strain/max eff. stress/other):": "fail_crit",
                "Load carried by filter paper strips (kN/mm):": "load_filt_paper",
                "Specimen perimeter covered by filter paper (mm):": "filt_paper_cov",
                "Young's modulus of membrane material (kPa):": "young_mod_mem",
                "Time of Test:": "test_time",
                "Date of Test:": "test_date",
                "Start of Repeated Data:": "start_rep_data"
            }

            metadados_valores = {}
            for chave_original, chave_interna in metadados_definidos.items():
                if chave_original in metadados:
                    metadados_valores[chave_interna] = metadados[chave_original]

            # Definir valores padrão usando as chaves internas
            metadados_valores.setdefault("B", "5")
            metadados_valores.setdefault("Adensamento", "7")
            metadados_valores.setdefault("Cisalhamento", "8")
            metadados_valores.setdefault("w_0", "0.1375")
            metadados_valores.setdefault("w_f", "0.2223")

            # Adicionar os metadados restantes sem mapeamento
            for chave, valor in metadados.items():
                if chave not in metadados_definidos:
                    metadados_valores[chave] = valor

            return metadados_valores

        except Exception as e:
            print(f"Erro ao processar o estágio dos dados: {e}")
            return None

if __name__ == "__main__":
    directory = r'C:\Users\lgv_v\Documents\LUIZ-Teste'
    arquivos = os.listdir(directory)
    for arquivo in arquivos:
        if arquivo.endswith('.gds'):
            StageProcessor.process_stage_data(directory, os.path.join(directory, arquivo), [])
