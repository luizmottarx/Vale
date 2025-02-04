# interface.py
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
from tkinter import messagebox, filedialog
import sqlite3
import os
import io
import sys
import matplotlib.pyplot as plt
from teste1 import FileProcessor
from teste2 import StageProcessor
from teste3 import TableProcessor, CisalhamentoData # Certifique-se de que o nome do arquivo está correto
import mplcursors
import random
import numpy as np
import pandas as pd
from testeBD import DatabaseManager  # Importar a classe DatabaseManager de testeBD.py
import re
import traceback
import PreencherExcel
import teste1
import teste2
import teste3
import testeBD


class InterfaceApp:
    def _rgb_to_hex(self, rgb):
        """Converte cores RGB para formato hexadecimal."""
        return "#{:02x}{:02x}{:02x}".format(
            int(rgb[0]*255),
            int(rgb[1]*255),
            int(rgb[2]*255)
        )


    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gerenciamento de Ensaios")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        self.db_manager = DatabaseManager()
        self.user_type = None
        self.selected_file = None
        self.metadados = {}
        self.metadados_parte2 = None
        self.terminal_output = ""
        self.logged_in_user = None

        self.create_login_screen()

    def create_login_screen(self):
        self.clear_screen()
        self.root.title("Login")

        frame = tk.Frame(self.root)
        frame.pack(pady=100)

        tk.Label(frame, text="Usuário:").grid(row=0, column=0, pady=10, padx=10)
        self.user_entry = tk.Entry(frame)
        self.user_entry.grid(row=0, column=1, pady=10, padx=10)

        tk.Label(frame, text="Senha:").grid(row=1, column=0, pady=10, padx=10)
        self.password_entry = tk.Entry(frame, show="*")
        self.password_entry.grid(row=1, column=1, pady=10, padx=10)

        tk.Button(frame, text="Login", command=self.check_login).grid(row=2, column=0, columnspan=2, pady=20)

    def filtrar_arquivos(self, graph_window, amostra_selecionada):
        # Criar uma nova janela para o filtro
        filter_window = tk.Toplevel(graph_window)
        filter_window.title("Filtrar Arquivos")
        filter_window.geometry("400x400")

        tk.Label(filter_window, text="Selecione os arquivos para visualizar:").pack(pady=10)

        # Criar o canvas e a barra de rolagem
        canvas = tk.Canvas(filter_window)
        scroll_y = tk.Scrollbar(filter_window, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll_y.set)

        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # Frame para os checkboxes dentro do scroll_frame
        checkbox_frame = tk.Frame(scroll_frame)
        checkbox_frame.pack()

        # Dicionário para armazenar os checkboxes
        checkboxes = {}
        for ensaio, var in self.selected_files_var.items():
            cb = tk.Checkbutton(checkbox_frame, text=ensaio, variable=var)
            cb.pack(anchor='w')
            checkboxes[ensaio] = cb

        def apply_filter():
            # Fechar a janela de filtro
            filter_window.destroy()
            # Fechar a janela de gráficos atual
            graph_window.destroy()
            # Replotar os gráficos com a seleção atualizada
            self.plotar_graficos_amostra(amostra_selecionada)

        # Botões "Aplicar" e "Cancelar"
        button_frame = tk.Frame(scroll_frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Aplicar", command=apply_filter, width=15).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancelar", command=filter_window.destroy, width=15).pack(side="right", padx=5)

    def check_login(self):
        user = self.user_entry.get()
        password = self.password_entry.get()

        if user == "admin" and password == "000":
            self.user_type = "admin"
            self.logged_in_user = user
            self.create_main_menu()
        elif self.verify_user_credentials(user, password):
            self.user_type = "user"
            self.logged_in_user = user
            self.create_main_menu()
        else:
            messagebox.showerror("Erro", "Usuário ou senha incorretos!")

    def verify_user_credentials(self, user, password):
        cursor = self.db_manager.conn.execute("SELECT * FROM usuarios WHERE login = ? AND senha = ?", (user, password))
        return cursor.fetchone() is not None

# No método create_main_menu da classe InterfaceApp, adicionar o novo botão

    def create_main_menu(self):
        self.clear_screen()
        self.root.title("Menu Principal")

        frame = tk.Frame(self.root)
        frame.pack(pady=50)

        if self.user_type == "admin":
            tk.Button(frame, text="Adicionar Usuário", command=self.add_user_screen, width=30).pack(pady=10)
            tk.Button(frame, text="Gerenciar Usuários", command=self.manage_users_screen, width=30).pack(pady=10)

        tk.Button(frame, text="Encontrar Arquivos", command=self.find_files, width=30).pack(pady=10)
        tk.Button(frame, text="Verificar Ensaio", command=self.verificar_ensaio_screen, width=30).pack(pady=10)
        tk.Button(frame, text="Ver Arquivos Aprovados", command=self.ver_arquivos_aprovados, width=30).pack(pady=10)
        tk.Button(frame, text="Ver Arquivos Refugados", command=self.ver_arquivos_refugados, width=30).pack(pady=10)
        tk.Button(frame, text="Gerar Planilha Cliente", command=self.gerar_planilha_cliente_screen, width=30).pack(pady=10)
        tk.Button(frame, text="Sair", command=self.root.quit, width=30).pack(pady=10)


    def ver_arquivos_aprovados(self):
        self.ver_arquivos_status_individual('Aprovado')

    def ver_arquivos_refugados(self):
        self.ver_arquivos_status_individual('Refugado')

    def ver_arquivos_status_individual(self, status):
        self.clear_screen()
        self.root.title(f"Arquivos com Status '{status}'")

        arquivos = self.db_manager.get_arquivos_by_status_individual(status)
        if not arquivos:
            messagebox.showinfo("Informação", f"Nenhum arquivo encontrado com status '{status}'.")
            self.create_main_menu()
            return

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text=f"Selecione um arquivo com status '{status}':").pack(pady=10)
        self.arquivo_listbox = tk.Listbox(frame, width=80, height=20)
        for arquivo in arquivos:
            self.arquivo_listbox.insert(tk.END, arquivo)
        self.arquivo_listbox.pack()

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Ver Gráfico", command=self.ver_grafico_arquivo_selecionado, width=15).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Voltar ao Menu", command=self.create_main_menu, width=15).grid(row=0, column=1, padx=10)


    def ver_grafico_arquivo_selecionado(self):
        selection = self.arquivo_listbox.curselection()
        if selection:
            index = selection[0]
            arquivo_selecionado = self.arquivo_listbox.get(index)
            self.plotar_graficos_arquivo(arquivo_selecionado)
        else:
            messagebox.showerror("Erro", "Nenhum arquivo selecionado!")

    # Fluxo Encontrar Arquivos
    def find_files(self):
        self.clear_screen()
        self.root.title("Encontrar Arquivos")

        directory = resource_path('LUIZ-Teste')
        if not os.path.isdir(directory):
            messagebox.showerror("Erro", f"O diretório {directory} não existe.")
            self.create_main_menu()
            return

        all_files = [f for f in os.listdir(directory) if f.endswith('.gds')]

        if not all_files:
            messagebox.showinfo("Informação", "Nenhum arquivo .gds encontrado.")
            self.create_main_menu()
            return

        # Buscar no banco de dados quais filenames já estão salvos
        arquivos_salvos = self.db_manager.get_existing_filenames()

        # Filtrar os arquivos que não estão salvos no banco
        arquivos_nao_salvos = [f for f in all_files if f not in arquivos_salvos]

        if not arquivos_nao_salvos:
            messagebox.showinfo("Informação", "Todos os arquivos .gds da pasta já foram salvos no banco de dados.")
            self.create_main_menu()
            return

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text="Selecione um arquivo:").pack(pady=10)
        self.file_var = tk.StringVar(value=arquivos_nao_salvos)
        self.file_listbox = tk.Listbox(frame, listvariable=self.file_var, width=80, height=20)
        self.file_listbox.pack()

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Avançar", command=self.select_file, width=15).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Voltar", command=self.create_main_menu, width=15).grid(row=0, column=1, padx=10)

    def select_file(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showerror("Erro", "Nenhum arquivo selecionado!")
            return

        index = selection[0]
        self.selected_file = self.file_listbox.get(index)
        directory = r'C:\Users\lgv_v\Documents\LUIZ-Teste'
        file_path = os.path.join(directory, self.selected_file)
        self.file_path = file_path

        processor = FileProcessor(directory)
        try:
            self.metadados = processor.process_gds_file(file_path)
            self.fixed_metadados = self.db_manager.get_fixed_metadados(self.selected_file)
            if self.fixed_metadados:
                for k, v in self.fixed_metadados.items():
                    if k not in self.metadados or not self.metadados[k]:
                        self.metadados[k] = v

            if "idcontrato" in self.metadados and not self.metadados.get("Job reference:"):
                self.metadados["Job reference:"] = self.metadados["idcontrato"]
            if "idcampanha" in self.metadados and not self.metadados.get("Borehole:"):
                self.metadados["Borehole:"] = self.metadados["idcampanha"]
            if "idamostra" in self.metadados and not self.metadados.get("Sample Name:"):
                self.metadados["Sample Name:"] = self.metadados["idamostra"]
            if "tipo" in self.metadados and not self.metadados.get("Description of Sample:"):
                self.metadados["Description of Sample:"] = self.metadados["tipo"]
            if "test_number" in self.metadados and not self.metadados.get("Test Number:"):
                self.metadados["Test Number:"] = self.metadados["test_number"]

            # Ajusta caso o FileProcessor tenha usado a chave "Description of Sample" (sem dois-pontos)
            if "Description of Sample" in self.metadados and "Description of Sample:" not in self.metadados:
                self.metadados["Description of Sample:"] = self.metadados["Description of Sample"]
                del self.metadados["Description of Sample"]

            desc_value = self.metadados.get("Description of Sample:", "").strip()
            match_desc = re.match(r"(\d+)[Ss](\d+)", desc_value)
            if match_desc:
                self.metadados["idtipoensaio"] = int(match_desc.group(1))
                self.metadados["sequencial"] = int(match_desc.group(2))
            else:
                self.metadados["idtipoensaio"] = 0
                self.metadados["sequencial"] = 0

            test_value = self.metadados.get("Test Number:", "").strip()
            match_test = re.match(r"([A-Za-z]+)[Rr]?(\d+)", test_value)
            if match_test:
                self.metadados["cp"] = match_test.group(1)[0].upper()
                self.metadados["repeticao"] = int(match_test.group(2))
            else:
                self.metadados["cp"] = None
                self.metadados["repeticao"] = None

            self.unify_metadados_keys()
            if not self.metadados:
                raise ValueError("Nenhum metadado encontrado no arquivo.")

            self.show_metadata_selection_screen()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar o arquivo: {e}")
            self.create_main_menu()


    def unify_metadados_keys(self):
        """
        Ajusta as chaves de metadados lidas do arquivo, mapeando-as para
        as colunas que realmente queremos salvar no banco de dados.
        Aqui ocorre a lógica de converter 'Cisalhamento' em dois valores:
        '_cis_inicial' e '_cis_final'.
        """
        desired_order = ["_B", "_ad", "_cis_inicial", "_cis_final", "w_0", "w_f",
                        "idcontrato", "idcampanha", "idamostra", "idtipoensaio",
                        "sequencial", "cp", "repeticao"]

        possible_aliases = {
            "B": "_B",
            "Adensamento": "_ad",

            # ALTERAÇÃO: Antes era "Cisalhamento" -> "_cis" teste
            # Agora possuímos dois campos:
            "Cisalhamento Inicial": "_cis_inicial",
            "Cisalhamento Final": "_cis_final",

            "Volume de umidade médio INICIAL": "w_0",
            "Volume de umidade médio FINAL": "w_f",
            "Initial Height (mm)": "h_init",
            "Initial Diameter (mm)": "d_init",
            "Ram Diameter": "ram_diam",
            "Specific Gravity (kN/m³):": "spec_grav",
            "Job reference:": "idcontrato",
            "Borehole:": "idcampanha",
            "Sample Name:": "idamostra",
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
            "camb_p_B0": "camb_p_B0"
        }

        # 1) Renomear as chaves do dicionário self.metadados conforme 'possible_aliases'
        for old_key, new_key in list(possible_aliases.items()):
            if old_key in self.metadados:
                # Se new_key estiver vazio ou não existir, substitui
                if new_key not in self.metadados or not self.metadados[new_key]:
                    self.metadados[new_key] = self.metadados[old_key]
                del self.metadados[old_key]

        # 2) Exemplo: caso o arquivo .gds ainda use apenas "Cisalhamento"
        # e a gente queira automaticamente criar '_cis_inicial' e '_cis_final'
        if "Cisalhamento" in self.metadados:
            valor_cis = str(self.metadados["Cisalhamento"]).strip()
            if "-" in valor_cis:
                ini, fim = valor_cis.split("-")
            else:
                ini, fim = valor_cis, valor_cis  # Ex.: se vier "8", então 8-8
            self.metadados["_cis_inicial"] = ini
            self.metadados["_cis_final"] = fim
            del self.metadados["Cisalhamento"]

        # 3) Ordenar metadados conforme 'desired_order'
        ordered_metadata = []
        remaining_metadata = []

        for key, value in self.metadados.items():
            if key in desired_order:
                ordered_metadata.append((key, value))
            else:
                remaining_metadata.append((key, value))

        # Reordena a lista final
        self.metadata_items = ordered_metadata + remaining_metadata

        # 4) Filtra apenas as colunas que serão salvas em MetadadosArquivo (se desejado)
        # Exemplo:
        metadadosarquivo_cols = [
            "_B", "_ad", "_cis_inicial", "_cis_final",
            "w_0", "w_f", "h_init", "d_init", "ram_diam", "spec_grav",
            "idcontrato", "idcampanha", "idamostra", "idtipoensaio", "depth",
            "samp_date", "tipo", "init_mass", "init_dry_mass", "spec_grav_assmeas",
            # ...
        ]

        final_dict = {}
        for col in metadadosarquivo_cols:
            if col in self.metadados:
                final_dict[col] = self.metadados[col]

        # Exemplos de cp e repeticao que podem não estar em metadadosarquivo_cols
        if "cp" in self.metadados:
            final_dict["cp"] = self.metadados["cp"]
        if "repeticao" in self.metadados:
            final_dict["repeticao"] = self.metadados["repeticao"]

        self.metadados = final_dict


    def save_metadata(self):
        try:
            result = TableProcessor.process_table_data(self.db_manager, self.metadados, self.file_path)
            if result is None:
                raise ValueError("Falha ao processar os dados do arquivo. Verifique se o arquivo está correto.")

            df_to_save = result['df']
            metadados_parte2 = result['metadados_parte2']

            self.db_manager.save_to_database(self.metadados, df_to_save, filename=os.path.basename(self.file_path))

            # Exibe a messagebox de sucesso
            messagebox.showinfo("Sucesso", "Metadados salvos com sucesso!")

            # Chama a função para exibir a tela de resultados
            self.show_save_status()  # Alterado de show_results_screen para show_save_status

        except Exception as e:
            print(f"Erro ao salvar metadados: {e}")
            traceback.print_exc()
            messagebox.showerror("Erro", f"Falha ao salvar os metadados: {e}")

    def alterar_status_arquivo(self, filename, novo_status):
        try:
            self.db_manager.update_status_cp(filename, novo_status)
            messagebox.showinfo("Sucesso", f"Status do arquivo '{filename}' atualizado para '{novo_status}'.")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível atualizar o status: {e}")
            #logging.error(f"Erro ao alterar status do arquivo '{filename}': {e}")
            traceback.print_exc()

    def edit_selected_metadata(self):
        selection = self.metadata_list.curselection()
        if selection:
            index = selection[0]
            selected_metadata, original_value = self.metadata_items[index]
            # Verifique se o metadado selecionado é "tipo_sequencial"
            self.show_metadata_edit_screen(selected_metadata)
        else:
            messagebox.showerror("Erro", "Nenhum metadado selecionado!")

    def show_metadata_edit_screen(self, selected_metadata):
        """
        Exibe a tela para editar um metadado específico.
        Caso o metadado seja '_cis_inicial' ou '_cis_final',
        usamos um Entry mais simples, pois queremos um valor numérico (int).
        """
        self.clear_screen()
        self.root.title("Edição de Metadado")

        frame = tk.Frame(self.root)
        frame.pack(pady=50)

        tk.Label(frame, text=f"Editando: {selected_metadata}").pack(pady=10)

        # Caso seja cisalhamento inicial/final, esperamos um valor int
        if selected_metadata in ["_cis_inicial", "_cis_final"]:
            valor_atual = str(self.metadados.get(selected_metadata, ""))
            self.metadata_entry = tk.Entry(frame, width=20)
            self.metadata_entry.insert(0, valor_atual)
            self.metadata_entry.pack(pady=10)
        else:
            # Edição normal para os demais metadados
            valor_atual = str(self.metadados.get(selected_metadata, ""))
            self.metadata_entry = tk.Entry(frame, width=80)
            self.metadata_entry.insert(0, valor_atual)
            self.metadata_entry.pack(pady=10)

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        self.current_editing_metadata = selected_metadata

        tk.Button(button_frame, text="Salvar Alterações",
                command=self.on_edit_save, width=20).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Voltar",
                command=self.show_metadata_selection_screen, width=20).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Sair",
                command=self.root.quit, width=20).grid(row=0, column=2, padx=5)



    def show_metadata_selection_screen(self):
        """
        Exibe uma tela/listbox com os metadados para o usuário editar ou salvar.
        Esta função deve ser chamada depois de self.metadados ter sido preenchido.
        """
        self.clear_screen()
        self.root.title("Edição de Metadados")

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text="Edite os metadados abaixo:").pack(pady=10)

        # Listbox para exibir os metadados (chave e valor)
        self.metadata_list = tk.Listbox(frame, height=15, width=100)
        self.metadata_list.pack(fill="both", expand=True)

        # Define a ordem desejada
        desired_order = ["_B", "_ad", "_cis_inicial", "_cis_final", "w_0", "w_f", "idcontrato", "idcampanha", "idamostra", "idtipoensaio", "sequencial", "cp", "repeticao"]

        # Cria uma lista de pares (chave, valor) ordenados
        ordered_metadata = []
        remaining_metadata = []

        for key, value in self.metadados.items():
            if key in desired_order:
                ordered_metadata.append((key, value))
            else:
                remaining_metadata.append((key, value))

        # Ordena os metadados conforme desired_order
        self.metadata_items = ordered_metadata + remaining_metadata

        # Limpa e povoa o Listbox
        self.metadata_list.delete(0, tk.END)
        for metadado, valor in self.metadata_items:
            # Insere a string "<chave>: <valor>"
            self.metadata_list.insert(tk.END, f"{metadado}: {valor}")

        # Botões
        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Editar",
                command=self.edit_selected_metadata, width=20).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Salvar no Banco",
                command=self.save_metadata, width=20).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Voltar",
                command=self.find_files, width=20).grid(row=0, column=2, padx=5)
        tk.Button(button_frame, text="Sair",
                command=self.root.quit, width=20).grid(row=0, column=3, padx=5)



    def on_edit_save(self):
        """
        Função chamada ao clicar em "Salvar Alterações" na tela de edição de um metadado.
        Aqui lidamos separadamente com '_cis_inicial' e '_cis_final',
        que devem ser valores inteiros (intervalo de estágios).
        """
        new_value = self.metadata_entry.get()

        # Se for cisalhamento inicial ou final, convertemos para int
        if self.current_editing_metadata in ["_cis_inicial", "_cis_final"]:
            if not new_value.strip():
                messagebox.showerror("Erro", "O valor do cisalhamento não pode estar vazio!")
                return
            try:
                self.metadados[self.current_editing_metadata] = int(new_value)
                messagebox.showinfo("Sucesso",
                                    f"{self.current_editing_metadata} atualizado para {new_value}")
            except ValueError:
                messagebox.showerror("Erro", "Insira um valor inteiro válido para cisalhamento!")
                return

            self.show_metadata_selection_screen()
            return

        # Para os demais metadados, mantemos a lógica anterior
        if new_value:
            if self.current_editing_metadata in self.metadados:
                self.metadados[self.current_editing_metadata] = new_value
                messagebox.showinfo("Sucesso",
                                    f"Metadado '{self.current_editing_metadata}' atualizado para '{new_value}'!")
                self.show_metadata_selection_screen()
            else:
                messagebox.showerror("Erro", f"Metadado '{self.current_editing_metadata}' não encontrado.")
        else:
            messagebox.showerror("Erro", "O valor não pode estar vazio!")



    def get_tipoensaio_id(self, tipo_ensaio):
        try:
            return self.db_manager.get_tipoensaio_id(tipo_ensaio)
        except ValueError as ve:
            messagebox.showerror("Erro", str(ve))
            return None


    def update_metadata(self, selected_metadata):
        new_value = self.metadata_entry.get()
        if new_value:
            if selected_metadata in self.metadados:
                self.metadados[selected_metadata] = new_value
                messagebox.showinfo("Sucesso", f"Metadado '{selected_metadata}' atualizado para '{new_value}'!")
                self.show_metadata_selection_screen()  # Atualiza a tela de metadados
            else:
                messagebox.showerror("Erro", f"Metadado '{selected_metadata}' não encontrado.")
        else:
            messagebox.showerror("Erro", "O valor não pode estar vazio!")

    def show_save_status(self):
        """
        Exibe uma tela com todos os metadados do arquivo salvo,
        permitindo ao usuário visualizar e interagir com os dados.
        """
        self.clear_screen()
        self.root.title("Metadados Salvos")
        
        frame = tk.Frame(self.root)
        frame.pack(pady=20)
        
        tk.Label(frame, text="Metadados do Arquivo Salvo", font=("Helvetica", 16)).pack(pady=10)
        
        try:
            # Obter o idnome do arquivo salvo
            idnome = self.db_manager.get_idnome_by_filename(os.path.basename(self.file_path))
            if not idnome:
                messagebox.showerror("Erro", "Não foi possível encontrar os metadados para o arquivo salvo.")
                self.create_main_menu()
                return
            
            # Obter todos os metadados do arquivo salvo
            metadados = self.db_manager.get_all_metadados_for_idnome(idnome)
            if not metadados:
                messagebox.showerror("Erro", "Nenhum metadado encontrado para o arquivo salvo.")
                self.create_main_menu()
                return
            
            # Exibir os metadados em um widget de texto com scrollbar
            results_frame = tk.Frame(frame)
            results_frame.pack(pady=10)
            
            scrollbar = tk.Scrollbar(results_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget = tk.Text(results_frame, height=20, width=100, yscrollcommand=scrollbar.set)
            text_widget.pack()
            
            scrollbar.config(command=text_widget.yview)
            
            # Inserir os metadados no widget de texto
            for key, value in metadados.items():
                text_widget.insert(tk.END, f"{key}: {value}\n")
            
            text_widget.config(state=tk.DISABLED)
        
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao obter os metadados: {e}")
            self.create_main_menu()
            return
        
        # Botões
        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Plotar Gráficos", command=lambda: self.plotar_graficos_arquivo(os.path.basename(self.file_path)), width=20).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Voltar ao Menu Principal", command=self.create_main_menu, width=25).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Sair", command=self.root.quit, width=20).grid(row=0, column=2, padx=5)


    def show_scatter_plots_wrapper(self):
        if self.selected_file:
            self.plotar_graficos_arquivo(self.selected_file)
        else:
            messagebox.showerror("Erro", "Nenhum arquivo selecionado para plotar os gráficos.")

    # Fluxo Verificar Ensaio
    def verificar_ensaio_screen(self):
        self.clear_screen()
        self.root.title("Verificar Ensaio")

        # Obter todas as amostras
        all_amostras = self.db_manager.get_amostras()
        if not all_amostras:
            messagebox.showinfo("Informação", "Nenhuma amostra encontrada.")
            self.create_main_menu()
            return

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        # Campo de busca
        tk.Label(frame, text="Buscar Amostra:").pack(pady=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.update_amostra_list())
        self.search_entry = tk.Entry(frame, textvariable=self.search_var)
        self.search_entry.pack(pady=5)

        # Lista de amostras
        tk.Label(frame, text="Selecione uma amostra:").pack(pady=10)
        self.amostra_listbox = tk.Listbox(frame, width=80, height=20)
        self.amostra_listbox.pack()

        # Inicializar lista de amostras
        self.all_amostras = all_amostras
        self.filtered_amostras = all_amostras.copy()
        self.update_amostra_list()

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Ver gráficos da amostra",  command=self.avancar_amostra, width=25).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Selecionar Individual", command=self.selecionar_individual_amostra, width=25).grid(row=0, column=1, padx=10)
        tk.Button(button_frame, text="Voltar ao Menu", command=self.create_main_menu, width=25).grid(row=0, column=2, padx=10)


    def avancar_planilha_cliente(self):
        selection = self.amostra_listbox.curselection()
        if selection:
            index = selection[0]
            amostra_selecionada = self.amostra_listbox.get(index)
            self.tipo_ensaio_screen_planilha_cliente(amostra_selecionada)
        else:
            messagebox.showerror("Erro", "Nenhuma amostra selecionada!")

    def tipo_ensaio_screen_planilha_cliente(self, amostra_selecionada):
        self.clear_screen()
        self.root.title("Selecionar Modelo de Planilha")

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text="Selecione o modelo de planilha:").pack(pady=10)
        self.modelo_var = tk.StringVar(value='TIR')  # Valor padrão
        modelo_frame = tk.Frame(frame)
        modelo_frame.pack(pady=5)
        tk.Radiobutton(modelo_frame, text="TIR", variable=self.modelo_var, value='TIR').pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(modelo_frame, text="TER", variable=self.modelo_var, value='TER').pack(side=tk.LEFT, padx=5)

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Avançar", command=lambda: self.selecionar_arquivos_planilha_cliente(amostra_selecionada), width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Voltar", command=self.gerar_planilha_cliente_screen, width=15).pack(side=tk.RIGHT, padx=5)

    def selecionar_arquivos_planilha_cliente(self, amostra_selecionada):
        self.clear_screen()
        self.root.title(f"Selecionar Arquivos para Planilha Cliente - {amostra_selecionada}")

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text=f"Selecione até 5 arquivos da amostra {amostra_selecionada}:").pack(pady=10)
        self.planilha_cliente_listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, width=80, height=10)
        
        # Obter arquivos aprovados da amostra
        arquivos_aprovados = self.db_manager.get_ensaios_by_amostra(
            amostra_selecionada,
            status_individual='Aprovado'
        )
        for arquivo in arquivos_aprovados:
            self.planilha_cliente_listbox.insert(tk.END, arquivo)
        self.planilha_cliente_listbox.pack()

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        # Passar 'amostra_selecionada' como parâmetro usando lambda
        tk.Button(button_frame, text="Gerar Planilha", command=lambda: self.metodo_selection_screen_planilha_cliente(amostra_selecionada), width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Voltar", command=lambda: self.tipo_ensaio_screen_planilha_cliente(amostra_selecionada), width=15).pack(side=tk.RIGHT, padx=5)

    def metodo_selection_screen_planilha_cliente(self, amostra_selecionada):
        selection = self.planilha_cliente_listbox.curselection()
        if not selection:
            messagebox.showerror("Erro", "Nenhum arquivo selecionado!")
            return
        if len(selection) > 5:
            messagebox.showerror("Erro", "Selecione no máximo 5 arquivos!")
            return

        arquivos_selecionados = [self.planilha_cliente_listbox.get(i) for i in selection]
        tipo_ensaio_selecionado = self.modelo_var.get()

        self.clear_screen()
        self.root.title("Selecionar Método")

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text="Selecione o Método:").pack(pady=10)
        self.metodo_planilha_var = tk.StringVar(value='A')  # Valor padrão
        metodo_frame = tk.Frame(frame)
        metodo_frame.pack(pady=5)
        tk.Radiobutton(metodo_frame, text="Método A", variable=self.metodo_planilha_var, value='A').pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(metodo_frame, text="Método B", variable=self.metodo_planilha_var, value='B').pack(side=tk.LEFT, padx=5)

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        # Passar 'amostra_selecionada' se necessário na função de 'Voltar'
        tk.Button(button_frame, text="Gerar Planilha", command=lambda: self.chamar_gerar_planilha(arquivos_selecionados, tipo_ensaio_selecionado, self.metodo_planilha_var.get()), width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Voltar", command=lambda: self.selecionar_arquivos_planilha_cliente(amostra_selecionada), width=15).pack(side=tk.RIGHT, padx=5)


    def chamar_gerar_planilha(self, arquivos_selecionados, tipo_ensaio_selecionado, metodo):
        try:
            from PreencherExcel import gerar_planilha_para_arquivos
            gerar_planilha_para_arquivos(arquivos_selecionados, tipo_ensaio_selecionado, metodo)
            messagebox.showinfo("Sucesso", "Planilha gerada com sucesso!")
            self.create_main_menu()
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao gerar a planilha: {e}")
        finally:
            self.create_main_menu()


    def selecionar_individual_amostra(self):
        selection = self.amostra_listbox.curselection()
        if selection:
            index = selection[0]
            amostra_selecionada = self.amostra_listbox.get(index)
            self.mostrar_ensaios_individuais(amostra_selecionada)
        else:
            messagebox.showerror("Erro", "Nenhuma amostra selecionada!")

    def mostrar_ensaios_individuais(self, amostra_selecionada):
        self.clear_screen()
        self.root.title(f"Arquivos Individuais da Amostra {amostra_selecionada}")

        # Obter todos os ensaios da amostra, excluindo os com status 'Refugado'
        ensaios = self.db_manager.get_ensaios_by_amostra(amostra_selecionada, exclude_status='Refugado')
        if not ensaios:
            messagebox.showinfo("Informação", "Nenhum ensaio encontrado para a amostra selecionada.")
            self.verificar_ensaio_screen()
            return

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text=f"Selecione um arquivo individual da amostra {amostra_selecionada}:").pack(pady=10)
        self.ensaio_individual_listbox = tk.Listbox(frame, width=80, height=20)
        for ensaio in ensaios:
            self.ensaio_individual_listbox.insert(tk.END, ensaio)
        self.ensaio_individual_listbox.pack()

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Plotar Gráfico", command=self.plotar_grafico_individual_selecionado, width=20).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Voltar", command=self.verificar_ensaio_screen, width=20).grid(row=0, column=1, padx=5)

    def plotar_grafico_individual_selecionado(self):
        selection = self.ensaio_individual_listbox.curselection()
        if selection:
            index = selection[0]
            arquivo_selecionado = self.ensaio_individual_listbox.get(index)
            self.plotar_graficos_arquivo(arquivo_selecionado)
        else:
            messagebox.showerror("Erro", "Nenhum arquivo selecionado!")


    def update_amostra_list(self):
        search_text = self.search_var.get().strip().lower()
        if search_text == "":
            self.filtered_amostras = self.all_amostras.copy()
        else:
            self.filtered_amostras = [amostra for amostra in self.all_amostras if search_text in amostra.lower()]
        # Atualizar a listbox
        self.amostra_listbox.delete(0, tk.END)
        for amostra in self.filtered_amostras:
            self.amostra_listbox.insert(tk.END, amostra)

    def avancar_amostra(self):
        selection = self.amostra_listbox.curselection()
        if selection:
            index = selection[0]
            amostra_selecionada = self.amostra_listbox.get(index)
            self.amostra_selecionada = amostra_selecionada
            self.selecionar_arquivos_amostra(amostra_selecionada)
        else:
            messagebox.showerror("Erro", "Nenhuma amostra selecionada!")
            return

    def mostrar_ensaios_amostra(self, amostra_selecionada):
        # Remova self.clear_screen()
        self.root.title(f"Arquivos da Amostra {amostra_selecionada}")

        # Obter todos os arquivos da amostra, excluindo os com status 'Refugado'
        ensaios = self.db_manager.get_ensaios_by_amostra(amostra_selecionada, exclude_status='Refugado')
        if not ensaios:
            messagebox.showinfo("Informação", "Nenhum ensaio encontrado para a amostra selecionada.")
            self.verificar_ensaio_screen()
            return

        # Inicializar a variável selected_files_var com todos os arquivos selecionados
        self.selected_files_var = {}
        for ensaio in ensaios:
            var = tk.BooleanVar(value=True)
            self.selected_files_var[ensaio] = var

        # Plotar os gráficos com todos os arquivos selecionados
        self.plotar_graficos_amostra(amostra_selecionada)

    def selecionar_arquivos_amostra(self, amostra_selecionada):
        self.clear_screen()
        self.root.title(f"Selecionar Arquivos para Amostra {amostra_selecionada}")

        # Obter ensaios com statusIndividual != 'Refugado'
        ensaios = self.db_manager.get_ensaios_by_amostra(amostra_selecionada, exclude_status='Refugado')
        if not ensaios:
            messagebox.showinfo("Informação", "Nenhum ensaio encontrado para a amostra selecionada.")
            self.verificar_ensaio_screen()
            return

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text=f"Selecione os arquivos para visualizar nos gráficos da amostra {amostra_selecionada}:").pack(pady=10)

        self.selected_files_var = {}
        for ensaio in ensaios:
            # Por padrão, marcar os arquivos com statusIndividual = 'Aprovado'
            status_individual = self.db_manager.get_status_individual(ensaio)
            var = tk.BooleanVar(value=(status_individual == 'Aprovado'))
            self.selected_files_var[ensaio] = var
            cb = tk.Checkbutton(frame, text=ensaio, variable=var)
            cb.pack(anchor='w')

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Plotar Gráficos", command=lambda: self.plotar_graficos_amostra(amostra_selecionada), width=20).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Voltar", command=self.verificar_ensaio_screen, width=20).grid(row=0, column=1, padx=5)

    def configurar_escalas(self, fig, axs):
        config_window = tk.Toplevel(self.root)
        config_window.title("Configurar Escalas dos Gráficos")

        canvas = tk.Canvas(config_window)
        scroll_y = tk.Scrollbar(config_window, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll_y.set)

        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        entries = []

        for i, ax in enumerate(axs):
            frame = tk.Frame(scroll_frame)
            frame.pack(pady=5)

            tk.Label(frame, text=f"Gráfico {i+1} ({ax.get_title()}):").grid(row=0, column=0, columnspan=2)

            tk.Label(frame, text="X min:").grid(row=1, column=0)
            x_min_entry = tk.Entry(frame, width=10)
            x_min_entry.grid(row=1, column=1)

            tk.Label(frame, text="X max:").grid(row=1, column=2)
            x_max_entry = tk.Entry(frame, width=10)
            x_max_entry.grid(row=1, column=3)

            tk.Label(frame, text="Y min:").grid(row=2, column=0)
            y_min_entry = tk.Entry(frame, width=10)
            y_min_entry.grid(row=2, column=1)

            tk.Label(frame, text="Y max:").grid(row=2, column=2)
            y_max_entry = tk.Entry(frame, width=10)
            y_max_entry.grid(row=2, column=3)

            entries.append({
                'ax': ax,
                'x_min': x_min_entry,
                'x_max': x_max_entry,
                'y_min': y_min_entry,
                'y_max': y_max_entry
            })

        tk.Button(scroll_frame, text="Aplicar", command=lambda: self.aplicar_escalas(entries, fig, config_window)).pack(pady=10)

    def aplicar_escalas(self, entries, fig, config_window):
        for entry in entries:
            ax = entry['ax']
            try:
                x_min = float(entry['x_min'].get())
                x_max = float(entry['x_max'].get())
                ax.set_xlim(x_min, x_max)
            except ValueError:
                pass

            try:
                y_min = float(entry['y_min'].get())
                y_max = float(entry['y_max'].get())
                ax.set_ylim(y_min, y_max)
            except ValueError:
                pass

        fig.canvas.draw_idle()
        config_window.destroy()

    def safe_cast_to_int(value, default=0):
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default
        
    def plotar_graficos_arquivo(self, arquivo_selecionado):
        """
        Carrega os dados do arquivo selecionado, obtém os metadados
        e plota diversos gráficos referentes ao intervalo de cisalhamento.
        """
        try:
            # 1) Obter dados do arquivo
            data = self.db_manager.get_data_for_file(arquivo_selecionado)
            if data is None:
                messagebox.showerror("Erro", "Não foi possível obter os dados para plotagem.")
                return

            # 2) Obter metadados para o arquivo
            metadados = self.db_manager.get_metadata_for_file(arquivo_selecionado)
            if not metadados:
                messagebox.showerror("Erro", "Nenhum metadado encontrado para o arquivo selecionado.")
                return

            # 3) Ler cisalhamento inicial e final (default 8~11, por exemplo)
            try:
                cis_inicial = int(float(metadados.get("Cisalhamento Inicial", 8)))
                cis_final   = int(float(metadados.get("Cisalhamento Final", 8)))
            except ValueError as ve:
                messagebox.showerror("Erro", f"Erro ao converter valores de Cisalhamento para inteiro: {ve}")
                return

            # 4) Converter lista de dicts em DataFrame
            df = pd.DataFrame(data)

            # 5) Converter colunas necessárias para float
            numeric_columns = [
                'void_ratio_A', 'void_ratio_B', 'eff_camb_A', 'eff_camb_B',
                'dev_stress_A', 'dev_stress_B', 'nqp_A', 'nqp_B',
                'ax_strain', 'vol_strain', 'du_kpa', 'm_A', 'm_B', 'stage_no'
            ]
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # 6) Filtrar dados pelo intervalo de cisalhamento
            df_cisalhamento = df[
                (df['stage_no'] >= cis_inicial) &
                (df['stage_no'] <= cis_final)
            ]

            if df_cisalhamento.empty:
                messagebox.showinfo(
                    "Informação",
                    f"Nenhum dado encontrado no intervalo de cisalhamento ({cis_inicial} a {cis_final})."
                )
                return

            # 7) Definir os plots desejados (y_col, x_col)
            plots = [
                ('dev_stress_A', 'ax_strain'),
                ('dev_stress_B', 'ax_strain'),
                ('dev_stress_A', 'eff_camb_A'),
                ('dev_stress_B', 'eff_camb_B'),
                ('du_kpa', 'ax_strain'),
                ('vol_strain', 'ax_strain'),
                ('void_ratio_A', 'eff_camb_A'),
                ('void_ratio_B', 'eff_camb_B'),
                ('nqp_A', 'ax_strain'),
                ('nqp_B', 'ax_strain'),
                ('m_A', 'ax_strain'),
                ('m_B', 'ax_strain'),
            ]

            # 8) Plotar em subplots
            import mplcursors
            import matplotlib.pyplot as plt

            num_plots = len(plots)
            cols = 3
            rows = num_plots // cols + int(num_plots % cols > 0)

            fig, axs = plt.subplots(rows, cols, figsize=(18, 6 * rows))
            axs = axs.flatten()

            artists = []
            for i, (y_col, x_col) in enumerate(plots):
                ax = axs[i]
                # Scatter plot
                sc = ax.scatter(
                    df_cisalhamento[x_col],
                    df_cisalhamento[y_col],
                    picker=True,
                    label=arquivo_selecionado
                )
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
                ax.set_title(f"{y_col} x {x_col}")
                artists.append(sc)

            # Se sobrar algum eixo não usado, removemos
            for i in range(num_plots, len(axs)):
                fig.delaxes(axs[i])

            plt.tight_layout()

            # 9) Janela Tk para exibir os gráficos
            graph_window = tk.Toplevel(self.root)
            graph_window.title(f"Gráficos do Arquivo {arquivo_selecionado}")
            graph_window.geometry("1280x960")

            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

            # Cria Canvas + Scrollbars
            canvas = tk.Canvas(graph_window)
            scroll_y = tk.Scrollbar(graph_window, orient="vertical", command=canvas.yview)
            scroll_x = tk.Scrollbar(graph_window, orient="horizontal", command=canvas.xview)
            canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

            canvas.pack(side="left", fill="both", expand=True)
            scroll_y.pack(side="right", fill="y")
            scroll_x.pack(side="bottom", fill="x")

            # Cria um frame interno ao Canvas
            scroll_frame = tk.Frame(canvas)
            scroll_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

            # Agora insere o FigureCanvas e a toolbar dentro de scroll_frame
            canvas_plot = FigureCanvasTkAgg(fig, master=scroll_frame)
            canvas_plot.draw()
            canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(canvas_plot, scroll_frame)
            toolbar.update()
            canvas_plot.get_tk_widget().pack()

            cursor = mplcursors.cursor(artists, hover=True)

            @cursor.connect("add")
            def on_add(sel):
                x, y = sel.target
                sel.annotation.set_text(f"x: {x:.4f}\ny: {y:.4f}")

            # Botões extras no final da janela
            button_frame = tk.Frame(scroll_frame)
            button_frame.pack(pady=10)

            def atualizar_status(status):
                self.db_manager.update_status_cp(arquivo_selecionado, status)
                messagebox.showinfo("Sucesso", f"Status do arquivo '{arquivo_selecionado}' atualizado para '{status}'.")
                graph_window.destroy()

            tk.Button(
                button_frame,
                text="Configurar Escalas",
                command=lambda: self.configurar_escalas(fig, axs),
                width=20
            ).pack(side="left", padx=5)

            tk.Button(
                button_frame,
                text="Aprovado",
                command=lambda: atualizar_status('Aprovado'),
                width=20
            ).pack(side="left", padx=5)

            tk.Button(
                button_frame,
                text="Refugado",
                command=lambda: atualizar_status('Refugado'),
                width=20
            ).pack(side="left", padx=5)

            tk.Button(button_frame, text="Sair", command=graph_window.destroy, width=20).pack(side="left", padx=5)

        except KeyError as e:
            messagebox.showerror("Erro", f"Coluna não encontrada: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao plotar os gráficos: {e}")


            def atualizar_status(status):
                self.db_manager.update_status_cp(arquivo_selecionado, status)
                messagebox.showinfo("Sucesso", f"Status do arquivo '{arquivo_selecionado}' atualizado para '{status}'.")
                graph_window.destroy()

            button_frame = tk.Frame(scroll_frame)
            button_frame.pack(pady=10)

            tk.Button(button_frame, text="Configurar Escalas", command=lambda: self.configurar_escalas(fig, axs), width=20).pack(side="left", padx=5)

            tk.Button(button_frame, text="Aprovado", command=lambda: atualizar_status('Aprovado'), width=20).pack(side="left", padx=5)

            tk.Button(button_frame, text="Refugado", command=lambda: atualizar_status('Refugado'), width=20).pack(side="left", padx=5)

            tk.Button(button_frame, text="Sair", command=graph_window.destroy, width=20).pack(side="left", padx=5)

        except KeyError as e:
            messagebox.showerror("Erro", f"Coluna não encontrada: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao plotar os gráficos: {e}")


    def verificar_arquivo_individual(self):
        selection = self.ensaio_listbox.curselection()
        if selection:
            index = selection[0]
            arquivo_selecionado = self.ensaio_listbox.get(index)
            self.mostrar_metadados_arquivo(arquivo_selecionado)
        else:
            messagebox.showerror("Erro", "Nenhum arquivo selecionado!")

    def mostrar_metadados_arquivo(self, arquivo_selecionado):
        self.clear_screen()
        self.root.title(f"Metadados do Arquivo {arquivo_selecionado}")

        metadados = self.db_manager.get_metadata_for_file(arquivo_selecionado)
        if not metadados:
            messagebox.showinfo("Informação", "Nenhum metadado encontrado para o arquivo selecionado.")
            self.mostrar_ensaios_amostra()
            return

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text=f"Metadados do Arquivo {arquivo_selecionado}:").pack(pady=10)
        metadata_text = tk.Text(frame, width=80, height=20)
        for metadado, valor in metadados.items():
            # Exibir apenas as abreviações
            metadata_text.insert(tk.END, f"{metadado}: {valor}\n")
        metadata_text.config(state=tk.DISABLED)
        metadata_text.pack()

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Ver Gráficos", command=lambda: self.plotar_graficos_arquivo(arquivo_selecionado), width=20).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Sair", command=self.create_main_menu, width=20).grid(row=0, column=1, padx=5)

    def get_data_for_file(self, filename):
        """
        Recupera os dados necessários para plotagem com base no filename.
        Busca na tabela EnsaiosTriaxiais e retorna como DataFrame.
        """
        try:
            idnome = self.db_manager.get_idnome_by_filename(filename)
            if not idnome:
                print(f"Arquivo '{filename}' não encontrado na tabela 'Cp'.")
                return None

            df = self.db_manager.get_ensaios_by_idnome(idnome)

            if df is None or df.empty:
                print(f"Nenhum dado encontrado para o arquivo '{filename}' (idnome={idnome}).")
                return None

            return df

        except Exception as e:
            print(f"Erro ao recuperar dados para '{filename}': {e}")
            traceback.print_exc()
            return None

    # Funções de Plotagem de Gráficos Unificadas
    def plotar_graficos_amostra(self, amostra_selecionada):
        """
        Obtém múltiplos arquivos associados à amostra selecionada,
        filtra pelo intervalo de cisalhamento, e plota diversos gráficos
        comparando cada arquivo em um único subplot.
        """
        try:
            # 1) Quais arquivos (filenames) estão selecionados?
            selected_files = [filename for filename, var in self.selected_files_var.items() if var.get()]
            if not selected_files:
                messagebox.showerror("Erro", "Nenhum arquivo selecionado para plotar.")
                return

            # 2) Buscar dados no banco
            data = self.db_manager.get_data_for_files(selected_files)
            if not data:
                messagebox.showinfo("Informação", "Nenhum dado encontrado para os arquivos selecionados.")
                return

            # 3) Agrupar dados por arquivo
            data_by_file = {}
            for row in data:
                arquivo = row['NomeCompleto']
                if arquivo not in data_by_file:
                    data_by_file[arquivo] = []
                data_by_file[arquivo].append(row)

            # 4) Para cada arquivo, criar DataFrame e filtrar cisalhamento
            import pandas as pd
            datasets = {}

            for arquivo, rows in data_by_file.items():
                metadados = self.db_manager.get_metadata_for_file(arquivo)

                # Se não houver metadados, usar defaults
                if not metadados:
                    # Exemplo: default 8~11
                    cis_inicial = 8
                    cis_final   = 11
                else:
                    # Tentar ler do dicionário
                    try:
                        cis_inicial = int(float(metadados.get("Cisalhamento Inicial", 8)))
                        cis_final   = int(float(metadados.get("Cisalhamento Final", 8)))
                    except ValueError:
                        # Se der erro, usar valores padrão
                        cis_inicial = 8
                        cis_final   = 11

                df = pd.DataFrame(rows)

                numeric_columns = [
                    'void_ratio_A', 'void_ratio_B', 'eff_camb_A', 'eff_camb_B',
                    'dev_stress_A', 'dev_stress_B', 'nqp_A', 'nqp_B',
                    'ax_strain', 'vol_strain', 'du_kpa', 'm_A', 'm_B', 'stage_no'
                ]
                for col in numeric_columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                # Filtrar intervalos
                df_cisalhamento = df[
                    (df['stage_no'] >= cis_inicial) &
                    (df['stage_no'] <= cis_final)
                ]
                if df_cisalhamento.empty:
                    messagebox.showwarning(
                        "Aviso",
                        f"Arquivo '{arquivo}': Nenhum dado no intervalo {cis_inicial}–{cis_final}. Usando DF vazio."
                    )
                    datasets[arquivo] = pd.DataFrame(columns=numeric_columns)
                else:
                    datasets[arquivo] = df_cisalhamento

            if not datasets:
                messagebox.showinfo("Informação", "Nenhum dado encontrado para os arquivos selecionados.")
                return

            # 5) Plotar todos os datasets no mesmo conjunto de subplots
            import mplcursors
            import matplotlib.pyplot as plt

            # Se quiser, pode alterar quantos gráficos serão feitos
            plots = [
                ('void_ratio_A', 'eff_camb_A'),
                ('void_ratio_B', 'eff_camb_B'),
                ('dev_stress_A', 'ax_strain'),
                ('dev_stress_B', 'ax_strain'),
                ('nqp_A', 'ax_strain'),
                ('nqp_B', 'ax_strain'),
            ]

            num_plots = len(plots)
            cols = 3
            rows = num_plots // cols + int(num_plots % cols > 0)
            fig, axs = plt.subplots(rows, cols, figsize=(18, 6 * rows))
            axs = axs.flatten()

            artists = []

            for idx, (y_col, x_col) in enumerate(plots):
                ax = axs[idx]
                for arquivo, df_cisalhamento in datasets.items():
                    if not df_cisalhamento.empty:
                        sc = ax.scatter(
                            df_cisalhamento[x_col],
                            df_cisalhamento[y_col],
                            picker=True,
                            label=arquivo
                        )
                        artists.append(sc)
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
                ax.set_title(f"{y_col} x {x_col}")

            for i in range(num_plots, len(axs)):
                fig.delaxes(axs[i])

            plt.tight_layout()

            # 6) Criar janela Tk com barra de rolagem
            graph_window = tk.Toplevel(self.root)
            graph_window.title(f"Gráficos da Amostra {amostra_selecionada}")
            graph_window.geometry("1280x960")

            canvas = tk.Canvas(graph_window)
            scroll_y = tk.Scrollbar(graph_window, orient="vertical", command=canvas.yview)
            scroll_x = tk.Scrollbar(graph_window, orient="horizontal", command=canvas.xview)
            canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

            scroll_frame = tk.Frame(canvas)
            scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

            canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
            canvas.pack(side="left", fill="both", expand=True)
            scroll_y.pack(side="right", fill="y")
            scroll_x.pack(side="bottom", fill="x")

            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

            canvas_plot = FigureCanvasTkAgg(fig, master=scroll_frame)
            canvas_plot.draw()
            canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(canvas_plot, scroll_frame)
            toolbar.update()
            canvas_plot.get_tk_widget().pack()

            cursor = mplcursors.cursor(artists, hover=True)
            @cursor.connect("add")
            def on_add(sel):
                x, y = sel.target
                sel.annotation.set_text(f"x: {x:.4f}\ny: {y:.4f}")

            # Botões extras
            button_frame = tk.Frame(scroll_frame)
            button_frame.pack(pady=10)

            tk.Button(button_frame, text="Configurar Escalas",
                    command=lambda: self.configurar_escalas(fig, axs), width=20).pack(side="left", padx=10)
            tk.Button(button_frame, text="Filtrar Arquivos",
                    command=lambda: self.filtrar_arquivos(graph_window, amostra_selecionada), width=20).pack(side="left", padx=10)
            tk.Button(button_frame, text="Sair",
                    command=graph_window.destroy, width=20).pack(side="right", padx=10)

        except KeyError as e:
            messagebox.showerror("Erro", f"Coluna não encontrada: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao plotar os gráficos: {e}")


    def gerar_planilha_cliente_screen(self):
        self.clear_screen()
        self.root.title("Gerar Planilha Cliente")

        amostras = self.db_manager.get_amostras()
        if not amostras:
            messagebox.showinfo("Informação", "Nenhuma amostra encontrada.")
            self.create_main_menu()
            return

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text="Selecione uma amostra para gerar a planilha:").pack(pady=10)
        self.amostra_listbox = tk.Listbox(frame, width=80, height=10)
        for amostra in amostras:
            self.amostra_listbox.insert(tk.END, amostra)
        self.amostra_listbox.pack()

        tk.Button(frame, text="Avançar", command=self.avancar_planilha_cliente, width=15).pack(pady=10)

        tk.Button(frame, text="Voltar ao Menu", command=self.create_main_menu, width=15).pack(pady=10)


    def selecionar_tipo_ensaio(self):
        # Sempre obter a seleção atual da listbox
        selection = self.amostra_listbox.curselection()
        if selection:
            index = selection[0]
            self.amostra_selecionada = self.amostra_listbox.get(index)
        else:
            messagebox.showerror("Erro", "Nenhuma amostra selecionada!")
            return

        tipos_ensaio = self.db_manager.get_tipo_ensaio_by_amostra(self.amostra_selecionada)
        if not tipos_ensaio:
            messagebox.showinfo("Informação", "Nenhum TipoEnsaio encontrado para a amostra selecionada.")
            return

        self.clear_screen()
        self.root.title("Selecionar TipoEnsaio")

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text="Selecione o TipoEnsaio para gerar a planilha:").pack(pady=10)
        self.tipo_ensaio_listbox = tk.Listbox(frame, width=80, height=10)
        for tipo in tipos_ensaio:
            self.tipo_ensaio_listbox.insert(tk.END, tipo)
        self.tipo_ensaio_listbox.pack()

        tk.Button(frame, text="Avançar", command=self.selecionar_metodo, width=15).pack(pady=10)
        tk.Button(frame, text="Voltar", command=self.gerar_planilha_cliente_screen, width=15).pack(pady=10)

    def selecionar_metodo(self):
        # Sempre obter a seleção atual da listbox
        selection = self.tipo_ensaio_listbox.curselection()
        if selection:
            index = selection[0]
            self.tipo_ensaio_selecionado = self.tipo_ensaio_listbox.get(index)
        else:
            messagebox.showerror("Erro", "Nenhum TipoEnsaio selecionado!")
            return

        self.clear_screen()
        self.root.title("Selecionar Método")

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text="Selecione o Método:").pack(pady=10)
        self.metodo_var = tk.StringVar(value='A')  # Valor padrão
        metodo_frame = tk.Frame(frame)
        metodo_frame.pack(pady=5)
        tk.Radiobutton(metodo_frame, text="Método A", variable=self.metodo_var, value='A').pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(metodo_frame, text="Método B", variable=self.metodo_var, value='B').pack(side=tk.LEFT, padx=5)

        tk.Button(frame, text="Avançar", command=self.avancar_metodo, width=15).pack(pady=10)  # Alterado para chamar 'avancar_metodo'
        tk.Button(frame, text="Voltar", command=self.selecionar_tipo_ensaio_screen, width=15).pack(pady=10)


    def avancar_metodo(self):
        metodo_selecionado = self.metodo_var.get()
        if not metodo_selecionado:
            messagebox.showerror("Erro", "Nenhum Método selecionado!")
            return
        self.metodo_selecionado = metodo_selecionado
        self.selecionar_arquivos()


    def selecionar_metodo_screen(self):
        self.clear_screen()
        self.root.title("Selecionar Método")

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text="Selecione o Método:").pack(pady=10)
        self.metodo_var = tk.StringVar(value='A')  # Valor padrão
        metodo_frame = tk.Frame(frame)
        metodo_frame.pack(pady=5)
        tk.Radiobutton(metodo_frame, text="Método A", variable=self.metodo_var, value='A').pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(metodo_frame, text="Método B", variable=self.metodo_var, value='B').pack(side=tk.LEFT, padx=5)

        tk.Button(frame, text="Avançar", command=self.avancar_metodo, width=15).pack(pady=10)
        tk.Button(frame, text="Voltar", command=self.selecionar_tipo_ensaio_screen, width=15).pack(pady=10)

    def avancar_tipo_ensaio(self):
        selection = self.tipo_ensaio_listbox.curselection()
        if selection:
            index = selection[0]
            self.tipo_ensaio_selecionado = self.tipo_ensaio_listbox.get(index)
            self.selecionar_metodo_screen()
        else:
            messagebox.showerror("Erro", "Nenhum TipoEnsaio selecionado!")
            return

    def selecionar_tipo_ensaio_screen(self):
        tipos_ensaio = self.db_manager.get_tipo_ensaio_by_amostra(self.amostra_selecionada)
        if not tipos_ensaio:
            messagebox.showinfo("Informação", "Nenhum TipoEnsaio encontrado para a amostra selecionada.")
            return

        self.clear_screen()
        self.root.title("Selecionar TipoEnsaio")

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text="Selecione o TipoEnsaio para gerar a planilha:").pack(pady=10)
        self.tipo_ensaio_listbox = tk.Listbox(frame, width=80, height=10)
        for tipo in tipos_ensaio:
            self.tipo_ensaio_listbox.insert(tk.END, tipo)
        self.tipo_ensaio_listbox.pack()

        tk.Button(frame, text="Avançar", command=self.avancar_tipo_ensaio, width=15).pack(pady=10)
        tk.Button(frame, text="Voltar", command=self.gerar_planilha_cliente_screen, width=15).pack(pady=10)

    def selecionar_arquivos(self):
        self.clear_screen()
        self.root.title(f"Selecionar Arquivos da Amostra {self.amostra_selecionada}")

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text=f"Selecione até 5 arquivos individuais aprovados da amostra {self.amostra_selecionada} e TipoEnsaio '{self.tipo_ensaio_selecionado}':").pack(pady=10)
        self.arquivos_listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, width=80, height=10)
        self.arquivos_listbox.pack()

        # Obter arquivos aprovados da amostra selecionada e do TipoEnsaio selecionado
        arquivos_aprovados = self.db_manager.get_ensaios_by_amostra(
            self.amostra_selecionada,
            status_individual='Aprovado',
            tipo_ensaio=self.tipo_ensaio_selecionado
        )
        if not arquivos_aprovados:
            messagebox.showinfo("Informação", f"Nenhum arquivo aprovado encontrado para a amostra '{self.amostra_selecionada}' e TipoEnsaio '{self.tipo_ensaio_selecionado}'.")
            self.selecionar_metodo_screen()
            return

        for arquivo in arquivos_aprovados:
            self.arquivos_listbox.insert(tk.END, arquivo)

        tk.Button(frame, text="Gerar Planilha", command=self.gerar_planilha_selecionada, width=15).pack(pady=10)
        tk.Button(frame, text="Voltar", command=self.selecionar_metodo_screen, width=15).pack(pady=10)


    def gerar_planilha_selecionada(self):
        arquivos_selecionados_indices = self.arquivos_listbox.curselection()
        if not arquivos_selecionados_indices:
            messagebox.showerror("Erro", "Nenhum arquivo selecionado!")
            return
        if len(arquivos_selecionados_indices) > 5:
            messagebox.showerror("Erro", "Selecione no máximo 5 arquivos!")
            return
        self.arquivos_selecionados = [self.arquivos_listbox.get(i) for i in arquivos_selecionados_indices]

        try:
            from PreencherExcel import gerar_planilha_para_arquivos
            gerar_planilha_para_arquivos(
                self.arquivos_selecionados,
                self.tipo_ensaio_selecionado,
                self.metodo_selecionado
            )
            messagebox.showinfo("Sucesso", f"Planilha gerada com sucesso com os arquivos selecionados.")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao gerar a planilha: {e}")
     
    # Gerenciamento de Usuários
    def add_user_screen(self):
        self.clear_screen()
        self.root.title("Adicionar Usuário")

        frame = tk.Frame(self.root)
        frame.pack(pady=100)

        tk.Label(frame, text="Login:").grid(row=0, column=0, pady=10, padx=10)
        self.new_user_entry = tk.Entry(frame)
        self.new_user_entry.grid(row=0, column=1, pady=10, padx=10)

        tk.Label(frame, text="Senha:").grid(row=1, column=0, pady=10, padx=10)
        self.new_password_entry = tk.Entry(frame, show="*")
        self.new_password_entry.grid(row=1, column=1, pady=10, padx=10)

        button_frame = tk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)

        tk.Button(button_frame, text="Adicionar", command=self.add_user_to_db, width=15).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Voltar", command=self.create_main_menu, width=15).grid(row=0, column=1, padx=10)

    def add_user_to_db(self):
        login = self.new_user_entry.get()
        senha = self.new_password_entry.get()

        if login and senha:
            self.db_manager.add_user(login, senha)
            self.create_main_menu()
        else:
            messagebox.showerror("Erro", "Login e senha são obrigatórios!")

    # interface.py
    # Certifique-se de que a chamada para get_all_users está correta no método manage_users_screen

    def manage_users_screen(self):
        self.clear_screen()
        self.root.title("Gerenciar Usuários")

        users = self.db_manager.get_all_users()  # Certifique-se de que este método existe
        if not users:
            messagebox.showinfo("Informação", "Nenhum usuário encontrado.")
            self.create_main_menu()
            return

        frame = tk.Frame(self.root)
        frame.pack(pady=50)

        tk.Label(frame, text="Usuários:").pack(pady=10)
        self.user_listbox = tk.Listbox(frame, height=15, width=50)
        for user in users:
            self.user_listbox.insert(tk.END, user)
        self.user_listbox.pack()

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Excluir Usuário", command=self.delete_selected_user, width=20).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Voltar", command=self.create_main_menu, width=20).grid(row=0, column=1, padx=10)


    def delete_selected_user(self):
        selected_user = self.user_listbox.get(tk.ACTIVE)
        if selected_user:
            confirm = messagebox.askyesno("Confirmação", f"Tem certeza de que deseja excluir o usuário '{selected_user}'?")
            if confirm:
                self.db_manager.delete_user(selected_user)
                self.manage_users_screen()
        else:
            messagebox.showerror("Erro", "Nenhum usuário selecionado!")

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()


import os
import sys

def resource_path(relative_path):
    """Obtém o caminho absoluto para um recurso, funcionando tanto no desenvolvimento quanto no PyInstaller."""
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    print("ABRIU APLICAÇÃO")
    db_manager = DatabaseManager()
    root = tk.Tk()
    app = InterfaceApp(root)
    root.mainloop()
    print("FECHOU APLICAÇÃO")