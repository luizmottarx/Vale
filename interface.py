# interface.py
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

# Classe para gerenciar o banco de dados, incluindo a tabela de usuários
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
                    NomeCompleto TEXT,
                    ensaio TEXT,
                    login_usuario TEXT,
                    FOREIGN KEY (id_tipo) REFERENCES TipoEnsaio(id_tipo),
                    FOREIGN KEY (id_amostra) REFERENCES Amostra(id_amostra),
                    FOREIGN KEY (login_usuario) REFERENCES usuarios(login)
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

# Interface principal do aplicativo
class InterfaceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gerenciamento de Ensaios")
        self.root.geometry("600x600")
        self.root.resizable(False, False)
        self.db_manager = DatabaseManager()
        self.user_type = None  # Para verificar se o usuário é admin ou não
        self.selected_file = None
        self.metadados = {}
        self.metadados_parte2 = None  # Adicionar este atributo
        self.terminal_output = ""  # Para armazenar a saída do terminal
        self.logged_in_user = None  # Armazenar o usuário logado

        self.create_login_screen()

    def create_login_screen(self):
        self.clear_screen()
        self.root.title("Login")

        tk.Label(self.root, text="Usuário:").pack(pady=10)
        self.user_entry = tk.Entry(self.root)
        self.user_entry.pack()

        tk.Label(self.root, text="Senha:").pack(pady=10)
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack()

        tk.Button(self.root, text="Login", command=self.check_login).pack(pady=20)

    def check_login(self):
        user = self.user_entry.get()
        password = self.password_entry.get()

        if user == "admin" and password == "000":  # Verificação simples de admin
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

        if self.user_type == "admin":
            tk.Button(self.root, text="Adicionar Usuário", command=self.add_user_screen).pack(pady=10)
            tk.Button(self.root, text="Gerenciar Usuários", command=self.manage_users_screen).pack(pady=10)

        tk.Button(self.root, text="Encontrar Arquivos", command=self.find_files).pack(pady=10)
        tk.Button(self.root, text="Upload de Arquivo .gds", command=self.upload_file).pack(pady=10)
        tk.Button(self.root, text="Verificar Ensaio", command=self.verificar_ensaio_screen).pack(pady=10)
        tk.Button(self.root, text="Sair", command=self.root.quit).pack(pady=10)

    def verificar_ensaio_screen(self):
        self.clear_screen()
        self.root.title("Verificar Ensaio")

        amostras = self.db_manager.get_amostras()
        if not amostras:
            messagebox.showinfo("Informação", "Nenhuma amostra encontrada.")
            self.create_main_menu()
            return

        tk.Label(self.root, text="Selecione uma amostra:").pack(pady=10)
        self.amostra_listbox = tk.Listbox(self.root, width=80, height=20)
        for amostra in amostras:
            self.amostra_listbox.insert(tk.END, amostra)
        self.amostra_listbox.pack()

        tk.Button(self.root, text="Avançar", command=self.avancar_amostra).pack(pady=10)
        tk.Button(self.root, text="Voltar ao Menu", command=self.create_main_menu).pack(pady=10)

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

        tk.Label(self.root, text=f"Arquivos encontrados para a amostra {amostra_selecionada}:").pack(pady=10)
        self.ensaio_listbox = tk.Listbox(self.root, width=80, height=20)
        for ensaio in ensaios:
            self.ensaio_listbox.insert(tk.END, ensaio)
        self.ensaio_listbox.pack()

        tk.Button(self.root, text="Ver Gráficos", command=lambda: self.plotar_graficos_amostra(amostra_selecionada)).pack(pady=5)
        tk.Button(self.root, text="Verificar Arquivo Individual", command=self.verificar_arquivo_individual).pack(pady=5)
        tk.Button(self.root, text="Voltar", command=self.verificar_ensaio_screen).pack(pady=5)

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

        tk.Label(self.root, text=f"Metadados do Arquivo {arquivo_selecionado}:").pack(pady=10)
        metadata_text = tk.Text(self.root, width=80, height=20)
        for metadado, valor in metadados:
            metadata_text.insert(tk.END, f"{metadado}: {valor}\n")
        metadata_text.config(state=tk.DISABLED)
        metadata_text.pack()

        tk.Button(self.root, text="Ver Gráficos", command=lambda: self.plotar_graficos_arquivo(arquivo_selecionado)).pack(pady=5)
        tk.Button(self.root, text="Sair", command=self.create_main_menu).pack(pady=5)

    def plotar_graficos_amostra(self, amostra_selecionada):
        data = self.db_manager.get_data_for_amostra(amostra_selecionada)
        if not data:
            messagebox.showinfo("Informação", "Nenhum dado encontrado para a amostra selecionada.")
            return

        self.plotar_graficos(data, f"Gráficos da Amostra {amostra_selecionada}")

    def plotar_graficos_arquivo(self, arquivo_selecionado):
        data = self.db_manager.get_data_for_file(arquivo_selecionado)
        if not data:
            messagebox.showinfo("Informação", "Nenhum dado encontrado para o arquivo selecionado.")
            return

        self.plotar_graficos(data, f"Gráficos do Arquivo {arquivo_selecionado}")

    def plotar_graficos(self, data, title):
        fig, axs = plt.subplots(3, 2, figsize=(12, 18))

        for row in data:
            eff_camb_A = float(row.get('eff_camb_A', 0))
            void_ratio_A = float(row.get('void_ratio_A', 0))
            eff_camb_B = float(row.get('eff_camb_B', 0))
            void_ratio_B = float(row.get('void_ratio_B', 0))
            dev_stress_A = float(row.get('dev_stress_A', 0))
            dev_stress_B = float(row.get('dev_stress_B', 0))
            nqp_A = float(row.get('nqp_A', 0))
            nqp_B = float(row.get('nqp_B', 0))
            ax_strain = float(row.get('ax_strain', 0))

            # Plotting each data point
            axs[0, 0].scatter(eff_camb_A, void_ratio_A, color='blue')
            axs[0, 1].scatter(eff_camb_B, void_ratio_B, color='green')
            axs[1, 0].scatter(eff_camb_A, dev_stress_A, color='red')
            axs[1, 1].scatter(eff_camb_B, dev_stress_B, color='orange')
            axs[2, 0].scatter(ax_strain, nqp_A, color='purple')
            axs[2, 1].scatter(ax_strain, nqp_B, color='brown')

        # Set titles
        axs[0, 0].set_title('void_ratio_A * eff_camb_A')
        axs[0, 1].set_title('void_ratio_B * eff_camb_B')
        axs[1, 0].set_title('dev_stress_A * eff_camb_A')
        axs[1, 1].set_title('dev_stress_B * eff_camb_B')
        axs[2, 0].set_title('nqp_A * ax_strain')
        axs[2, 1].set_title('nqp_B * ax_strain')

        plt.tight_layout()

        graph_window = tk.Toplevel(self.root)
        graph_window.title(title)

        canvas_graph = FigureCanvasTkAgg(fig, master=graph_window)
        canvas_graph.draw()
        canvas_graph.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        tk.Button(graph_window, text="Sair", command=graph_window.destroy).pack(pady=10)

    def add_user_screen(self):
        self.clear_screen()
        self.root.title("Adicionar Usuário")

        tk.Label(self.root, text="Login:").pack(pady=10)
        self.new_user_entry = tk.Entry(self.root)
        self.new_user_entry.pack()

        tk.Label(self.root, text="Senha:").pack(pady=10)
        self.new_password_entry = tk.Entry(self.root, show="*")
        self.new_password_entry.pack()

        tk.Button(self.root, text="Adicionar", command=self.add_user_to_db).pack(pady=20)
        tk.Button(self.root, text="Voltar", command=self.create_main_menu).pack(pady=10)

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

        tk.Label(self.root, text="Usuários:").pack(pady=10)
        self.user_listbox = tk.Listbox(self.root, height=15, width=50)
        for user in users:
            self.user_listbox.insert(tk.END, user)
        self.user_listbox.pack(fill="both", expand=True)

        tk.Button(self.root, text="Excluir Usuário", command=self.delete_selected_user).pack(pady=10)
        tk.Button(self.root, text="Voltar", command=self.create_main_menu).pack(pady=10)

    def delete_selected_user(self):
        selected_user = self.user_listbox.get(tk.ACTIVE)
        if selected_user:
            confirm = messagebox.askyesno("Confirmação", f"Tem certeza de que deseja excluir o usuário '{selected_user}'?")
            if confirm:
                self.db_manager.delete_user(selected_user)
                self.manage_users_screen()
        else:
            messagebox.showerror("Erro", "Nenhum usuário selecionado!")

    def find_files(self):
        self.clear_screen()
        self.root.title("Arquivos Encontrados")

        directory = r'C:\Users\lgv_v\Documents\LUIZ-Teste'
        files = [f for f in os.listdir(directory) if f.endswith('.gds')]

        if not files:
            messagebox.showinfo("Informação", "Nenhum arquivo .gds encontrado.")
            self.create_main_menu()
            return

        tk.Label(self.root, text="Selecione um arquivo:").pack(pady=10)
        self.file_var = tk.StringVar(value=files)
        self.file_listbox = tk.Listbox(self.root, listvariable=self.file_var, width=80, height=20)
        self.file_listbox.pack()

        tk.Button(self.root, text="Selecionar", command=self.select_file).pack(pady=10)
        tk.Button(self.root, text="Voltar", command=self.create_main_menu).pack(pady=10)

    def select_file(self):
        self.selected_file = self.file_listbox.get(tk.ACTIVE)
        if self.selected_file:
            directory = r'C:\Users\lgv_v\Documents\LUIZ-Teste'
            file_path = os.path.join(directory, self.selected_file)

            # Processamento do arquivo
            processor = FileProcessor(directory)
            self.metadados = processor.process_gds_file(file_path)  # Processa o arquivo com o teste1

            if self.metadados:
                self.metadados = StageProcessor.process_stage_data(directory, file_path, self.metadados)  # Processa o arquivo com o teste2
                self.show_metadata_selection_screen()
            else:
                messagebox.showerror("Erro", "Falha ao processar o arquivo.")
                self.create_main_menu()
        else:
            messagebox.showerror("Erro", "Nenhum arquivo selecionado!")

    def show_metadata_selection_screen(self):
        self.clear_screen()
        self.root.title("Seleção de Metadados")

        tk.Label(self.root, text=f"Selecione um metadado para editar:").pack(pady=10)

        self.metadata_list = tk.Listbox(self.root, height=15, width=80)
        for key, value in self.metadados.items():
            self.metadata_list.insert(tk.END, f"{key}: {value}")
        self.metadata_list.pack(fill="both", expand=True)

        tk.Button(self.root, text="Editar", command=self.edit_selected_metadata).pack(pady=10)
        tk.Button(self.root, text="Salvar no Banco", command=self.save_metadata).pack(pady=10)
        tk.Button(self.root, text="Voltar", command=self.find_files).pack(pady=10)
        tk.Button(self.root, text="Sair", command=self.root.quit).pack(pady=10)

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

        tk.Label(self.root, text=f"Editando: {selected_metadata}").pack(pady=10)

        self.metadata_entry = tk.Entry(self.root, width=80)
        self.metadata_entry.insert(0, self.metadados[selected_metadata])
        self.metadata_entry.pack(pady=10)

        tk.Button(self.root, text="Salvar Alterações", command=lambda: self.update_metadata(selected_metadata)).pack(pady=10)
        tk.Button(self.root, text="Voltar", command=self.show_metadata_selection_screen).pack(pady=10)
        tk.Button(self.root, text="Sair", command=self.root.quit).pack(pady=10)

    def update_metadata(self, selected_metadata):
        new_value = self.metadata_entry.get()
        self.metadados[selected_metadata] = new_value
        messagebox.showinfo("Sucesso", f"Metadado '{selected_metadata}' atualizado!")
        self.show_metadata_selection_screen()

    def save_metadata(self):
        directory = r'C:\Users\lgv_v\Documents\LUIZ-Teste'
        file_path = os.path.join(directory, self.selected_file)

        # Capturar a saída do terminal
        old_stdout = sys.stdout
        sys.stdout = mystdout = io.StringIO()

        # Processa o arquivo com o teste3 e captura metadados_parte2
        self.metadados_parte2 = TableProcessor.process_table_data(self.metadados, file_path)

        # Restaurar stdout
        sys.stdout = old_stdout

        # Obter o texto impresso
        self.terminal_output = mystdout.getvalue()

        # Salvar metadados no banco de dados
        self.save_to_database()

        self.show_save_status()

    def save_to_database(self):
        # Inserir ou recuperar id_tipo
        tipo_ensaio = self.metadados.get('TipoEnsaio', 'Desconhecido')
        cursor = self.db_manager.conn.cursor()
        cursor.execute("SELECT id_tipo FROM TipoEnsaio WHERE tipo = ?", (tipo_ensaio,))
        row = cursor.fetchone()
        if row:
            id_tipo = row[0]
        else:
            cursor.execute("INSERT INTO TipoEnsaio (tipo) VALUES (?)", (tipo_ensaio,))
            id_tipo = cursor.lastrowid

        # Inserir ou recuperar id_amostra
        amostra = self.metadados.get('Amostra', 'Desconhecida')
        cursor.execute("SELECT id_amostra FROM Amostra WHERE amostra = ?", (amostra,))
        row = cursor.fetchone()
        if row:
            id_amostra = row[0]
        else:
            cursor.execute("INSERT INTO Amostra (amostra) VALUES (?)", (amostra,))
            id_amostra = cursor.lastrowid

        # Inserir Ensaio
        nome_completo = self.selected_file
        ensaio = self.metadados.get('Ensaio', 'Desconhecido')
        login_usuario = self.logged_in_user  # Usuário logado

        cursor.execute("""
            INSERT INTO Ensaio (id_tipo, id_amostra, NomeCompleto, ensaio, login_usuario)
            VALUES (?, ?, ?, ?, ?)
        """, (id_tipo, id_amostra, nome_completo, ensaio, login_usuario))

        self.db_manager.conn.commit()

    def show_save_status(self):
        self.clear_screen()
        self.root.title("Status de Salvamento")

        tk.Label(self.root, text="Dados processados e salvos no banco de dados!").pack(pady=10)

        # Exibir o output capturado
        if self.terminal_output:
            tk.Label(self.root, text="Valores dos metadados calculados:").pack(pady=10)

            text_widget = tk.Text(self.root, height=25, width=80)
            text_widget.pack(pady=10)

            text_widget.insert(tk.END, self.terminal_output)
            text_widget.config(state=tk.DISABLED)  # Tornar o Text widget somente leitura
        else:
            tk.Label(self.root, text="Não foi possível obter os metadados calculados.").pack(pady=10)

        tk.Button(self.root, text="Ver Gráficos", command=self.show_scatter_plots).pack(pady=10)
        tk.Button(self.root, text="Voltar ao Menu Principal", command=self.create_main_menu).pack(pady=10)
        tk.Button(self.root, text="Sair", command=self.root.quit).pack(pady=10)

    def show_scatter_plots(self):
        if self.metadados_parte2 is None:
            messagebox.showerror("Erro", "Os dados não foram processados corretamente.")
            return

        try:
            # Filtrar os dados do estágio de cisalhamento dinamicamente
            cisalhamento_data = CisalhamentoData(self.metadados_parte2.df, self.metadados)

            # Recuperar os dados necessários para os gráficos
            dados_cisalhamento = cisalhamento_data.get_cisalhamento_data()
            ax_strain = dados_cisalhamento['ax_strain']
            dev_stress_A = dados_cisalhamento['dev_stress_A']
            dev_stress_B = dados_cisalhamento['dev_stress_B']
            vol_strain = dados_cisalhamento['vol_strain']
            eff_camb_A = dados_cisalhamento['eff_camb_A']
            eff_camb_B = dados_cisalhamento['eff_camb_B']
            void_ratio_A = dados_cisalhamento['void_ratio_A']
            void_ratio_B = dados_cisalhamento['void_ratio_B']
            du_kpa_A = dados_cisalhamento['du_kpa_A']
            du_kpa_B = dados_cisalhamento['du_kpa_B']
            nqp_A = dados_cisalhamento['nqp_A']
            nqp_B = dados_cisalhamento['nqp_B']
            m_A = dados_cisalhamento['m_A']
            m_B = dados_cisalhamento['m_B']

            # Criar janela de gráficos
            graph_window = tk.Toplevel(self.root)
            graph_window.title("Gráficos de Dispersão")
            graph_window.geometry("1280x960")

            # Criar um frame principal com barra de rolagem
            canvas = tk.Canvas(graph_window)
            scroll_y = tk.Scrollbar(graph_window, orient="vertical", command=canvas.yview)
            scroll_frame = tk.Frame(canvas)

            # Configurar o canvas com o frame
            scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
            canvas.configure(yscrollcommand=scroll_y.set)

            canvas.pack(side="left", fill="both", expand=True)
            scroll_y.pack(side="right", fill="y")

            # Criar os gráficos
            fig, axs = plt.subplots(7, 2, figsize=(19.2, 21.6))  # Set the size to allow more space vertically

            # Primeiro gráfico: dev_stress_A * ax_strain
            axs[0, 0].scatter(ax_strain, dev_stress_A)
            axs[0, 0].set_title('dev_stress_A * ax_strain')

            # Segundo gráfico: dev_stress_B * ax_strain
            axs[0, 1].scatter(ax_strain, dev_stress_B)
            axs[0, 1].set_title('dev_stress_B * ax_strain')

            # Terceiro gráfico: du_kpa_A * ax_strain
            axs[1, 0].scatter(ax_strain, du_kpa_A)
            axs[1, 0].set_title('du_kpa_A * ax_strain')

            # Quarto gráfico: du_kpa_B * ax_strain
            axs[1, 1].scatter(ax_strain, du_kpa_B)
            axs[1, 1].set_title('du_kpa_B * ax_strain')

            # Quinto gráfico: dev_stress_A * eff_camb_A
            axs[2, 0].scatter(eff_camb_A, dev_stress_A)
            axs[2, 0].set_title('dev_stress_A * eff_camb_A')

            # Sexto gráfico: dev_stress_B * eff_camb_B
            axs[2, 1].scatter(eff_camb_B, dev_stress_B)
            axs[2, 1].set_title('dev_stress_B * eff_camb_B')

            # Sétimo gráfico: vol_strain * ax_strain
            axs[3, 0].scatter(ax_strain, vol_strain)
            axs[3, 0].set_title('vol_strain * ax_strain')

            # Oitavo gráfico: void_ratio_A * eff_camb_A
            axs[3, 1].scatter(eff_camb_A, void_ratio_A)
            axs[3, 1].set_title('void_ratio_A * eff_camb_A')

            # Nono gráfico: void_ratio_B * eff_camb_B
            axs[4, 0].scatter(eff_camb_B, void_ratio_B)
            axs[4, 0].set_title('void_ratio_B * eff_camb_B')

            # Décimo gráfico: nqp_A * ax_strain
            axs[4, 1].scatter(ax_strain, nqp_A)
            axs[4, 1].set_title('nqp_A * ax_strain')

            # Décimo primeiro gráfico: nqp_B * ax_strain
            axs[5, 0].scatter(ax_strain, nqp_B)
            axs[5, 0].set_title('nqp_B * ax_strain')

            # Décimo segundo gráfico: m_A * ax_strain
            axs[5, 1].scatter(ax_strain, m_A)
            axs[5, 1].set_title('m_A * ax_strain')

            # Décimo terceiro gráfico: m_B * ax_strain
            axs[6, 0].scatter(ax_strain, m_B)
            axs[6, 0].set_title('m_B * ax_strain')

            plt.tight_layout()

            # Converter o gráfico matplotlib para tkinter
            canvas_graph = FigureCanvasTkAgg(fig, master=scroll_frame)
            canvas_graph.draw()
            canvas_graph.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except KeyError as e:
            messagebox.showerror("Erro", f"Coluna não encontrada: {e}")

    def upload_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("GDS files", "*.gds")])
        if file_path:
            directory = os.path.dirname(file_path)
            processor = FileProcessor(directory)
            self.metadados = processor.process_gds_file(file_path)  # Processa o arquivo com o teste1
            if self.metadados:
                self.metadados = StageProcessor.process_stage_data(directory, file_path, self.metadados)  # Processa o arquivo com o teste2
                self.selected_file = os.path.basename(file_path)
                self.show_metadata_selection_screen()
            else:
                messagebox.showerror("Erro", "Falha ao processar o arquivo.")
                self.create_main_menu()
        else:
            self.create_main_menu()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = InterfaceApp(root)
    root.mainloop()
