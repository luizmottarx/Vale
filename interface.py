from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox, filedialog
import sqlite3
import os
import io
import sys
import matplotlib.pyplot as plt
from teste1 import FileProcessor
from teste2 import StageProcessor
from teste3 import TableProcessor, CisalhamentoData
import random
import numpy as np
import pandas as pd

class DatabaseManager:
    def __init__(self, db_name='C:/Users/lgv_v/Documents/LUIZ/Laboratorio_Geotecnia.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    login TEXT UNIQUE NOT NULL,
                    senha TEXT NOT NULL
                )
            """)
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
                    NomeCompleto TEXT UNIQUE,
                    ensaio TEXT,
                    FOREIGN KEY (id_tipo) REFERENCES TipoEnsaio(id_tipo),
                    FOREIGN KEY (id_amostra) REFERENCES Amostra(id_amostra)
                )
            """)

    def add_user(self, login, senha):
        with self.conn:
            try:
                self.conn.execute("INSERT INTO usuarios (login, senha) VALUES (?, ?)", (login, senha))
                messagebox.showinfo("Sucesso", f"Usuário '{login}' adicionado com sucesso!")
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", f"Usuário '{login}' já existe.")

    def get_all_users(self):
        cursor = self.conn.execute("SELECT login FROM usuarios")
        return [row[0] for row in cursor.fetchall()]

    def delete_user(self, login):
        with self.conn:
            self.conn.execute("DELETE FROM usuarios WHERE login = ?", (login,))
            messagebox.showinfo("Sucesso", f"Usuário '{login}' foi excluído com sucesso.")

    def get_amostras(self):
        cursor = self.conn.execute("SELECT amostra FROM Amostra")
        return [row[0] for row in cursor.fetchall()]

    def get_ensaios_by_amostra(self, amostra):
        cursor = self.conn.execute("SELECT id_amostra FROM Amostra WHERE amostra = ?", (amostra,))
        row = cursor.fetchone()
        if row:
            id_amostra = row[0]
            cursor = self.conn.execute("SELECT NomeCompleto FROM Ensaio WHERE id_amostra = ?", (id_amostra,))
            return [row[0] for row in cursor.fetchall()]
        else:
            return []

    def get_data_for_amostra(self, amostra):
        cursor = self.conn.execute("""
            SELECT et.*
            FROM EnsaiosTriaxiais et
            JOIN Ensaio e ON et.id_ensaio = e.id_ensaio
            JOIN Amostra a ON e.id_amostra = a.id_amostra
            WHERE a.amostra = ?
        """, (amostra,))
        columns = [description[0] for description in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return data

    def get_data_for_file(self, nome_completo):
        cursor = self.conn.execute("""
            SELECT et.*
            FROM EnsaiosTriaxiais et
            JOIN Ensaio e ON et.id_ensaio = e.id_ensaio
            WHERE e.NomeCompleto = ?
        """, (nome_completo,))
        columns = [description[0] for description in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return data

    def get_metadata_for_file(self, nome_completo):
        cursor = self.conn.execute("""
            SELECT m.metadados, ma.valor_metadados
            FROM MetadadosArquivo ma
            JOIN Metadados m ON ma.id_metadados = m.id_metadados
            WHERE ma.NomeCompleto = ?
        """, (nome_completo,))
        return cursor.fetchall()

    def close(self):
        self.conn.close()

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
        tk.Button(frame, text="Sair", command=self.root.quit, width=30).pack(pady=10)

    # Fluxo Encontrar Arquivos
    def find_files(self):
        self.clear_screen()
        self.root.title("Encontrar Arquivos")

        directory = r'C:\Users\lgv_v\Documents\LUIZ-Teste'
        if not os.path.isdir(directory):
            messagebox.showerror("Erro", f"O diretório {directory} não existe.")
            self.create_main_menu()
            return

        all_files = [f for f in os.listdir(directory) if f.endswith('.gds')]

        if not all_files:
            messagebox.showinfo("Informação", "Nenhum arquivo .gds encontrado.")
            self.create_main_menu()
            return

        cursor = self.db_manager.conn.cursor()
        cursor.execute("SELECT NomeCompleto FROM Ensaio")
        arquivos_salvos = {row[0] for row in cursor.fetchall()}

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
        if selection:
            index = selection[0]
            self.selected_file = self.file_listbox.get(index)
            directory = r'C:\Users\lgv_v\Documents\LUIZ-Teste'
            file_path = os.path.join(directory, self.selected_file)

            processor = FileProcessor(directory)
            try:
                self.metadados = processor.process_gds_file(file_path)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao processar o arquivo: {e}")
                self.create_main_menu()
                return

            if self.metadados:
                try:
                    self.metadados = StageProcessor.process_stage_data(directory, file_path, self.metadados)
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao processar dados de estágio: {e}")
                    self.create_main_menu()
                    return
                self.show_metadata_selection_screen()
            else:
                messagebox.showerror("Erro", "Falha ao processar o arquivo.")
                self.create_main_menu()
        else:
            messagebox.showerror("Erro", "Nenhum arquivo selecionado!")

    # Fluxo Editar Metadados (Encontrar Arquivos)
    def show_metadata_selection_screen(self):
        self.clear_screen()
        self.root.title("Seleção de Metadados")

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text="Selecione um metadado para editar:").pack(pady=10)

        self.metadata_list = tk.Listbox(frame, height=15, width=80)
        for key, value in self.metadados.items():
            self.metadata_list.insert(tk.END, f"{key}: {value}")
        self.metadata_list.pack(fill="both", expand=True)

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Editar", command=self.edit_selected_metadata, width=20).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Salvar no Banco", command=self.save_metadata, width=20).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Voltar", command=self.find_files, width=20).grid(row=0, column=2, padx=5)
        tk.Button(button_frame, text="Sair", command=self.root.quit, width=20).grid(row=0, column=3, padx=5)

    def edit_selected_metadata(self):
        selected_metadata_text = self.metadata_list.get(tk.ACTIVE)
        if selected_metadata_text:
            selected_metadata = selected_metadata_text.split(":")[0].strip()
            self.show_metadata_edit_screen(selected_metadata)
        else:
            messagebox.showerror("Erro", "Nenhum metadado selecionado!")

    def show_metadata_edit_screen(self, selected_metadata):
        self.clear_screen()
        self.root.title("Edição de Metadado")

        frame = tk.Frame(self.root)
        frame.pack(pady=50)

        tk.Label(frame, text=f"Editando: {selected_metadata}").pack(pady=10)

        self.metadata_entry = tk.Entry(frame, width=80)
        self.metadata_entry.insert(0, self.metadados[selected_metadata])
        self.metadata_entry.pack(pady=10)

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Salvar Alterações", command=lambda: self.update_metadata(selected_metadata), width=20).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Voltar", command=self.show_metadata_selection_screen, width=20).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Sair", command=self.root.quit, width=20).grid(row=0, column=2, padx=5)

    def update_metadata(self, selected_metadata):
        new_value = self.metadata_entry.get()
        if new_value:
            self.metadados[selected_metadata] = new_value
            messagebox.showinfo("Sucesso", f"Metadado '{selected_metadata}' atualizado!")
            self.show_metadata_selection_screen()
        else:
            messagebox.showerror("Erro", "O valor não pode estar vazio!")

    def save_metadata(self):
        directory = r'C:\Users\lgv_v\Documents\LUIZ-Teste'
        file_path = os.path.join(directory, self.selected_file)

        old_stdout = sys.stdout
        sys.stdout = mystdout = io.StringIO()

        try:
            self.metadados_parte2 = TableProcessor.process_table_data(self.metadados, file_path)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar dados da tabela: {e}")
            sys.stdout = old_stdout
            return

        sys.stdout = old_stdout

        self.terminal_output = mystdout.getvalue()

        self.save_to_database()

        self.show_save_status()

    def save_to_database(self):
        cursor = self.db_manager.conn.cursor()

        # Extrair 'Amostra', 'TipoEnsaio' e 'Ensaio' do nome do arquivo
        base_nome = os.path.basename(self.selected_file)
        nome_partes = os.path.splitext(base_nome)[0].split('_')

        if len(nome_partes) >= 3:
            amostra = nome_partes[0]
            tipo_ensaio = '_'.join(nome_partes[1:-1])
            ensaio = nome_partes[-1]
        else:
            amostra = 'Desconhecida'
            tipo_ensaio = 'Desconhecido'
            ensaio = 'Desconhecido'

        # Verificar se o NomeCompleto já existe na tabela Ensaio
        cursor.execute("SELECT NomeCompleto FROM Ensaio WHERE NomeCompleto = ?", (self.selected_file,))
        ensaio_existente = cursor.fetchone()

        # Se o arquivo já existe, interromper o processo sem exibir pop-up
        if ensaio_existente:
            #messagebox.showinfo("Informação", "Este ensaio já está registrado no banco de dados.")
            return  # Não prosseguir com o salvamento se o arquivo já existe

        try:
            # Inserir ou recuperar id_amostra
            cursor.execute("INSERT OR IGNORE INTO Amostra (amostra) VALUES (?)", (amostra,))
            cursor.execute("SELECT id_amostra FROM Amostra WHERE amostra = ?", (amostra,))
            id_amostra = cursor.fetchone()[0]

            # Inserir ou recuperar id_tipo
            cursor.execute("INSERT OR IGNORE INTO TipoEnsaio (tipo) VALUES (?)", (tipo_ensaio,))
            cursor.execute("SELECT id_tipo FROM TipoEnsaio WHERE tipo = ?", (tipo_ensaio,))
            id_tipo = cursor.fetchone()[0]

            # Inserir o novo registro no banco de dados
            cursor.execute("""
                INSERT INTO Ensaio (id_tipo, id_amostra, NomeCompleto, ensaio)
                VALUES (?, ?, ?, ?)
            """, (id_tipo, id_amostra, self.selected_file, ensaio))

            # Commit das alterações
            self.db_manager.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao salvar no banco de dados: {e}")

    def show_save_status(self):
        self.clear_screen()
        self.root.title("Status de Salvamento")

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text="Dados processados e salvos no banco de dados!").pack(pady=10)

        if self.terminal_output:
            tk.Label(frame, text="Valores dos metadados calculados:").pack(pady=10)

            text_widget = tk.Text(frame, height=25, width=80)
            text_widget.pack(pady=10)

            text_widget.insert(tk.END, self.terminal_output)
            text_widget.config(state=tk.DISABLED)
        else:
            tk.Label(frame, text="Não foi possível obter os metadados calculados.").pack(pady=10)

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Ver Gráficos", command=self.show_scatter_plots_wrapper, width=20).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Voltar ao Menu Principal", command=self.create_main_menu, width=20).grid(row=0, column=1, padx=5)
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

        amostras = self.db_manager.get_amostras()
        if not amostras:
            messagebox.showinfo("Informação", "Nenhuma amostra encontrada.")
            self.create_main_menu()
            return

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text="Selecione uma amostra:").pack(pady=10)
        self.amostra_listbox = tk.Listbox(frame, width=80, height=20)
        for amostra in amostras:
            self.amostra_listbox.insert(tk.END, amostra)
        self.amostra_listbox.pack()

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Avançar", command=self.avancar_amostra, width=15).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Voltar ao Menu", command=self.create_main_menu, width=15).grid(row=0, column=1, padx=10)

    def avancar_amostra(self):
        selection = self.amostra_listbox.curselection()
        if selection:
            index = selection[0]
            amostra_selecionada = self.amostra_listbox.get(index)
            self.mostrar_ensaios_amostra(amostra_selecionada)
        else:
            messagebox.showerror("Erro", "Nenhuma amostra selecionada!")

    def mostrar_ensaios_amostra(self, amostra_selecionada):
        self.clear_screen()
        self.root.title(f"Arquivos da Amostra {amostra_selecionada}")

        ensaios = self.db_manager.get_ensaios_by_amostra(amostra_selecionada)
        if not ensaios:
            messagebox.showinfo("Informação", "Nenhum ensaio encontrado para a amostra selecionada.")
            self.verificar_ensaio_screen()
            return

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        tk.Label(frame, text=f"Arquivos encontrados para a amostra {amostra_selecionada}:").pack(pady=10)
        self.ensaio_listbox = tk.Listbox(frame, width=80, height=20)
        for ensaio in ensaios:
            self.ensaio_listbox.insert(tk.END, ensaio)
        self.ensaio_listbox.pack()

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Ver Gráficos da Amostra", command=lambda: self.plotar_graficos_amostra(amostra_selecionada), width=25).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Verificar Arquivo Individual", command=self.verificar_arquivo_individual, width=25).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Voltar", command=self.verificar_ensaio_screen, width=25).grid(row=0, column=2, padx=5)

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
        for metadado, valor in metadados:
            metadata_text.insert(tk.END, f"{metadado}: {valor}\n")
        metadata_text.config(state=tk.DISABLED)
        metadata_text.pack()

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Ver Gráficos", command=lambda: self.plotar_graficos_arquivo(arquivo_selecionado), width=20).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Sair", command=self.create_main_menu, width=20).grid(row=0, column=1, padx=5)

    # Funções de Plotagem de Gráficos Unificadas
    def plotar_graficos_amostra(self, amostra_selecionada):
        try:
            # Obter os dados de todos os arquivos da amostra
            data = self.db_manager.get_data_for_amostra(amostra_selecionada)
            if not data:
                messagebox.showinfo("Informação", "Nenhum dado encontrado para a amostra selecionada.")
                return

            # Organizar os dados por arquivo (NomeCompleto)
            data_by_file = {}
            for row in data:
                arquivo = row['NomeCompleto']
                if arquivo not in data_by_file:
                    data_by_file[arquivo] = []
                data_by_file[arquivo].append(row)

            # Inicializar listas para cada par de dados
            void_ratio_A = {}
            void_ratio_B = {}
            eff_camb_A = {}
            eff_camb_B = {}
            dev_stress_A = {}
            dev_stress_B = {}
            nqp_A = {}
            nqp_B = {}
            ax_strain = {}
            vol_strain = {}
            du_kpa_A = {}
            du_kpa_B = {}
            m_A = {}
            m_B = {}

            for arquivo, rows in data_by_file.items():
                # Obter metadados para o arquivo
                metadados = self.db_manager.get_metadata_for_file(arquivo)
                if not metadados:
                    continue  # Se não há metadados, pular este arquivo

                # Converter a lista de tuplas em um dicionário
                metadados_dict = {key: value for key, value in metadados}

                cisalhamento_stage = int(metadados_dict.get("Cisalhamento", 8))  # Valor padrão 8 se não encontrado

                # Converter a lista de dicts para DataFrame
                df = pd.DataFrame(rows)

                # Converter as colunas necessárias para float
                numeric_columns = [
                    'void_ratio_A', 'void_ratio_B', 'eff_camb_A', 'eff_camb_B',
                    'dev_stress_A', 'dev_stress_B', 'nqp_A', 'nqp_B', 'ax_strain',
                    'vol_strain', 'du_kpa_A', 'du_kpa_B', 'm_A', 'm_B', 'stage_no'
                ]
                for col in numeric_columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                # Filtrar os dados para o estágio de cisalhamento
                df_cisalhamento = df[df['stage_no'] == cisalhamento_stage]

                if df_cisalhamento.empty:
                    continue  # Se não há dados para o estágio de cisalhamento, pular este arquivo

                # Agora, adicionar os dados às listas
                void_ratio_A[arquivo] = df_cisalhamento['void_ratio_A'].tolist()
                void_ratio_B[arquivo] = df_cisalhamento['void_ratio_B'].tolist()
                eff_camb_A[arquivo] = df_cisalhamento['eff_camb_A'].tolist()
                eff_camb_B[arquivo] = df_cisalhamento['eff_camb_B'].tolist()
                dev_stress_A[arquivo] = df_cisalhamento['dev_stress_A'].tolist()
                dev_stress_B[arquivo] = df_cisalhamento['dev_stress_B'].tolist()
                nqp_A[arquivo] = df_cisalhamento['nqp_A'].tolist()
                nqp_B[arquivo] = df_cisalhamento['nqp_B'].tolist()
                ax_strain[arquivo] = df_cisalhamento['ax_strain'].tolist()
                vol_strain[arquivo] = df_cisalhamento['vol_strain'].tolist()
                du_kpa_A[arquivo] = df_cisalhamento['du_kpa_A'].tolist()
                du_kpa_B[arquivo] = df_cisalhamento['du_kpa_B'].tolist()
                m_A[arquivo] = df_cisalhamento['m_A'].tolist()
                m_B[arquivo] = df_cisalhamento['m_B'].tolist()

            # Verificar se há dados para plotar
            if not void_ratio_A:
                messagebox.showinfo("Informação", "Nenhum dado encontrado para o estágio de cisalhamento nos arquivos selecionados.")
                return

            # Criar o layout dos gráficos (3x2 layout)
            fig, axs = plt.subplots(3, 2, figsize=(12, 28))

            # Função para gerar uma cor aleatória
            def random_color():
                return [random.random() for _ in range(3)]

            # Dicionário para armazenar as cores usadas em cada arquivo
            color_dict = {}

            # Plotar os gráficos com cores diferentes para cada arquivo
            for arquivo in void_ratio_A.keys():
                color = random_color()  # Cor aleatória para cada arquivo
                color_dict[arquivo] = color  # Armazenar a cor para a legenda

                # Plot void_ratio_A * eff_camb_A
                axs[0, 0].scatter(eff_camb_A[arquivo], void_ratio_A[arquivo], color=color, label=arquivo)
                axs[0, 0].set_xlabel('eff_camb_A')
                axs[0, 0].set_ylabel('void_ratio_A')
                axs[0, 0].set_title('void_ratio_A * eff_camb_A')

                # Plot void_ratio_B * eff_camb_B
                axs[0, 1].scatter(eff_camb_B[arquivo], void_ratio_B[arquivo], color=color, label=arquivo)
                axs[0, 1].set_xlabel('eff_camb_B')
                axs[0, 1].set_ylabel('void_ratio_B')
                axs[0, 1].set_title('void_ratio_B * eff_camb_B')

                # Plot dev_stress_A * eff_camb_A
                axs[1, 0].scatter(eff_camb_A[arquivo], dev_stress_A[arquivo], color=color, label=arquivo)
                axs[1, 0].set_xlabel('eff_camb_A')
                axs[1, 0].set_ylabel('dev_stress_A')
                axs[1, 0].set_title('dev_stress_A * eff_camb_A')

                # Plot dev_stress_B * eff_camb_B
                axs[1, 1].scatter(eff_camb_B[arquivo], dev_stress_B[arquivo], color=color, label=arquivo)
                axs[1, 1].set_xlabel('eff_camb_B')
                axs[1, 1].set_ylabel('dev_stress_B')
                axs[1, 1].set_title('dev_stress_B * eff_camb_B')

                # Plot nqp_A * ax_strain
                axs[2, 0].scatter(ax_strain[arquivo], nqp_A[arquivo], color=color, label=arquivo)
                axs[2, 0].set_xlabel('ax_strain')
                axs[2, 0].set_ylabel('nqp_A')
                axs[2, 0].set_title('nqp_A * ax_strain')

                # Plot nqp_B * ax_strain
                axs[2, 1].scatter(ax_strain[arquivo], nqp_B[arquivo], color=color, label=arquivo)
                axs[2, 1].set_xlabel('ax_strain')
                axs[2, 1].set_ylabel('nqp_B')
                axs[2, 1].set_title('nqp_B * ax_strain')

            plt.tight_layout()

            # Criar a janela de gráficos com barra de rolagem, sem bordas, 1280x960
            graph_window = tk.Toplevel(self.root)
            graph_window.title(f"Gráficos da Amostra {amostra_selecionada}")
            graph_window.geometry("1280x960")

            # Habilitar botões de minimizar, maximizar e fechar
            graph_window.attributes('-toolwindow', False)

            # Criar o canvas e a barra de rolagem
            canvas = tk.Canvas(graph_window)
            scroll_y = tk.Scrollbar(graph_window, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scroll_y.set)

            scroll_frame = tk.Frame(canvas)
            scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

            canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
            canvas.pack(side="left", fill="both", expand=True)
            scroll_y.pack(side="right", fill="y")

            # Adicionar o gráfico ao canvas
            canvas_graph = FigureCanvasTkAgg(fig, master=scroll_frame)
            canvas_graph.draw()
            canvas_graph.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # Adicionar a legenda no final da tela
            legend_frame = tk.Frame(scroll_frame)
            legend_frame.pack(pady=10)
            for arquivo, color in color_dict.items():
                hex_color = self._rgb_to_hex(color)
                legend_label = tk.Label(legend_frame, text=f"Arquivo: {arquivo}", bg=hex_color, width=50)
                legend_label.pack(side="top", padx=5, pady=5)

            # Adicionar o botão "Sair" no final
            sair_button = tk.Button(scroll_frame, text="Sair", command=graph_window.destroy)
            sair_button.pack(side="bottom", pady=10)

        except KeyError as e:
            messagebox.showerror("Erro", f"Coluna não encontrada: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao plotar os gráficos: {e}")



    def plotar_graficos_arquivo(self, arquivo_selecionado):
        data = self.db_manager.get_data_for_file(arquivo_selecionado)
        if not data:
            messagebox.showinfo("Informação", "Nenhum dado encontrado para o arquivo selecionado.")
            return

        self.plotar_graficos(data, f"Gráficos do Arquivo {arquivo_selecionado}")

    def plotar_graficos(self, data, title):
        try:
            # Obter o nome do arquivo a partir do título
            arquivo = title.replace("Gráficos do Arquivo ", "")

            # Obter metadados para o arquivo
            metadados = self.db_manager.get_metadata_for_file(arquivo)
            if not metadados:
                messagebox.showerror("Erro", f"Metadados não encontrados para o arquivo: {arquivo}")
                return

            # Converter a lista de tuplas em um dicionário
            metadados_dict = {key: value for key, value in metadados}

            cisalhamento_stage = int(metadados_dict.get("Cisalhamento", 8))  # Valor padrão 8 se não encontrado

            # Converter data (lista de dicts) em DataFrame
            df = pd.DataFrame(data)

            # Converter as colunas necessárias para float
            numeric_columns = [
                'void_ratio_A', 'void_ratio_B', 'eff_camb_A', 'eff_camb_B',
                'dev_stress_A', 'dev_stress_B', 'nqp_A', 'nqp_B', 'ax_strain',
                'vol_strain', 'm_A', 'm_B', 'du_kpa_A', 'du_kpa_B', 'stage_no'
            ]
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Filtrar os dados para o estágio de cisalhamento
            df_cisalhamento = df[df['stage_no'] == cisalhamento_stage]

            if df_cisalhamento.empty:
                messagebox.showinfo("Informação", "Nenhum dado encontrado para o estágio de cisalhamento.")
                return

            # Extrair as colunas para listas
            void_ratio_A = df_cisalhamento['void_ratio_A'].tolist()
            void_ratio_B = df_cisalhamento['void_ratio_B'].tolist()
            eff_camb_A = df_cisalhamento['eff_camb_A'].tolist()
            eff_camb_B = df_cisalhamento['eff_camb_B'].tolist()
            dev_stress_A = df_cisalhamento['dev_stress_A'].tolist()
            dev_stress_B = df_cisalhamento['dev_stress_B'].tolist()
            nqp_A = df_cisalhamento['nqp_A'].tolist()
            nqp_B = df_cisalhamento['nqp_B'].tolist()
            ax_strain = df_cisalhamento['ax_strain'].tolist()
            vol_strain = df_cisalhamento['vol_strain'].tolist()
            m_A = df_cisalhamento['m_A'].tolist()
            m_B = df_cisalhamento['m_B'].tolist()
            du_kpa_A = df_cisalhamento['du_kpa_A'].tolist()
            du_kpa_B = df_cisalhamento['du_kpa_B'].tolist()

            # Função auxiliar para remover valores 0 ou NaN antes de plotar
            def remove_zeros_nan(x, y):
                filtered_x = []
                filtered_y = []
                for i in range(len(x)):
                    if not np.isnan(x[i]) and not np.isnan(y[i]) and x[i] != 0 and y[i] != 0:
                        filtered_x.append(x[i])
                        filtered_y.append(y[i])
                return filtered_x, filtered_y

            # Criar os gráficos usando os dados filtrados
            fig, axs = plt.subplots(6, 2, figsize=(14, 32))  # Ajuste o figsize para aumentar o espaçamento entre os gráficos

            # Plot void_ratio_A * eff_camb_A
            x, y = remove_zeros_nan(eff_camb_A, void_ratio_A)
            axs[0, 0].scatter(x, y, color='blue')
            axs[0, 0].set_xlabel('eff_camb_A')
            axs[0, 0].set_ylabel('void_ratio_A')
            axs[0, 0].set_title('void_ratio_A * eff_camb_A')

            # Plot void_ratio_B * eff_camb_B
            x, y = remove_zeros_nan(eff_camb_B, void_ratio_B)
            axs[0, 1].scatter(x, y, color='blue')
            axs[0, 1].set_xlabel('eff_camb_B')
            axs[0, 1].set_ylabel('void_ratio_B')
            axs[0, 1].set_title('void_ratio_B * eff_camb_B')

            # Plot dev_stress_A * eff_camb_A
            x, y = remove_zeros_nan(eff_camb_A, dev_stress_A)
            axs[1, 0].scatter(x, y, color='blue')
            axs[1, 0].set_xlabel('eff_camb_A')
            axs[1, 0].set_ylabel('dev_stress_A')
            axs[1, 0].set_title('dev_stress_A * eff_camb_A')

            # Plot dev_stress_B * eff_camb_B
            x, y = remove_zeros_nan(eff_camb_B, dev_stress_B)
            axs[1, 1].scatter(x, y, color='blue')
            axs[1, 1].set_xlabel('eff_camb_B')
            axs[1, 1].set_ylabel('dev_stress_B')
            axs[1, 1].set_title('dev_stress_B * eff_camb_B')

            # Plot nqp_A * ax_strain
            x, y = remove_zeros_nan(ax_strain, nqp_A)
            axs[2, 0].scatter(x, y, color='blue')
            axs[2, 0].set_xlabel('ax_strain')
            axs[2, 0].set_ylabel('nqp_A')
            axs[2, 0].set_title('nqp_A * ax_strain')

            # Plot nqp_B * ax_strain
            x, y = remove_zeros_nan(ax_strain, nqp_B)
            axs[2, 1].scatter(x, y, color='blue')
            axs[2, 1].set_xlabel('ax_strain')
            axs[2, 1].set_ylabel('nqp_B')
            axs[2, 1].set_title('nqp_B * ax_strain')

            # Plot m_A * ax_strain
            x, y = remove_zeros_nan(ax_strain, m_A)
            axs[3, 0].scatter(x, y, color='blue')
            axs[3, 0].set_xlabel('ax_strain')
            axs[3, 0].set_ylabel('m_A')
            axs[3, 0].set_title('m_A * ax_strain')

            # Plot m_B * ax_strain
            x, y = remove_zeros_nan(ax_strain, m_B)
            axs[3, 1].scatter(x, y, color='blue')
            axs[3, 1].set_xlabel('ax_strain')
            axs[3, 1].set_ylabel('m_B')
            axs[3, 1].set_title('m_B * ax_strain')

            # vol_strain * ax_strain
            x, y = remove_zeros_nan(ax_strain, vol_strain)
            axs[4, 0].scatter(x, y, color='blue')
            axs[4, 0].set_xlabel('ax_strain')
            axs[4, 0].set_ylabel('vol_strain')
            axs[4, 0].set_title('vol_strain * ax_strain')

            # Plot du_kpa_A * ax_strain
            x, y = remove_zeros_nan(ax_strain, du_kpa_A)
            axs[4, 1].scatter(x, y, color='blue')
            axs[4, 1].set_xlabel('ax_strain')
            axs[4, 1].set_ylabel('du_kpa_A')
            axs[4, 1].set_title('du_kpa_A * ax_strain')

            # Plot du_kpa_B * ax_strain
            x, y = remove_zeros_nan(ax_strain, du_kpa_B)
            axs[5, 0].scatter(x, y, color='blue')
            axs[5, 0].set_xlabel('ax_strain')
            axs[5, 0].set_ylabel('du_kpa_B')
            axs[5, 0].set_title('du_kpa_B * ax_strain')

            plt.tight_layout()

            # Criar a janela de gráficos com barra de rolagem
            graph_window = tk.Toplevel(self.root)
            graph_window.title(title)
            graph_window.geometry("1280x960")

            # Criar o canvas e a barra de rolagem
            canvas = tk.Canvas(graph_window)
            scroll_y = tk.Scrollbar(graph_window, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scroll_y.set)

            scroll_frame = tk.Frame(canvas)
            scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

            canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
            canvas.pack(side="left", fill="both", expand=True)
            scroll_y.pack(side="right", fill="y")

            # Adicionar o gráfico ao canvas
            canvas_graph = FigureCanvasTkAgg(fig, master=scroll_frame)
            canvas_graph.draw()
            canvas_graph.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # Mover o botão "Sair" para o final
            tk.Button(scroll_frame, text="Sair", command=graph_window.destroy).pack(pady=20)

        except KeyError as e:
            messagebox.showerror("Erro", f"Coluna não encontrada: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao plotar os gráficos: {e}")


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

    def manage_users_screen(self):
        self.clear_screen()
        self.root.title("Gerenciar Usuários")

        users = self.db_manager.get_all_users()

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

if __name__ == "__main__":
    root = tk.Tk()
    app = InterfaceApp(root)
    root.mainloop()
