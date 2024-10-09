# comparar_excel_dashboard.py

import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

def encontrar_arquivos(diretorio):
    """
    Encontra e retorna uma lista de arquivos Excel ou CSV no diretório especificado.
    """
    arquivos = [f for f in os.listdir(diretorio) if f.endswith(('.xlsx', '.xls', '.csv'))]
    return arquivos

def ler_arquivo(caminho_arquivo):
    """
    Lê um arquivo Excel ou CSV e retorna um DataFrame.
    """
    if caminho_arquivo.endswith(('.xlsx', '.xls')):
        return pd.read_excel(caminho_arquivo)
    elif caminho_arquivo.endswith('.csv'):
        return pd.read_csv(caminho_arquivo)
    else:
        raise ValueError(f"Formato de arquivo não suportado: {caminho_arquivo}")

def main():
    st.title("Comparação de Colunas entre Dois Arquivos")

    # Especifique o diretório contendo os arquivos Excel ou CSV
    diretorio = r'C:\Users\lgv_v\Documents\LUIZ\compararExcel'  # Substitua pelo caminho do seu diretório

    # Encontrar arquivos Excel ou CSV no diretório
    arquivos = encontrar_arquivos(diretorio)
    if len(arquivos) < 2:
        st.error("Menos de dois arquivos Excel ou CSV encontrados no diretório.")
        return

    # Permitir que o usuário selecione os arquivos
    arquivo1_nome = st.selectbox("Selecione o primeiro arquivo:", arquivos)
    arquivo2_nome = st.selectbox("Selecione o segundo arquivo:", arquivos, index=1)

    arquivo1 = os.path.join(diretorio, arquivo1_nome)
    arquivo2 = os.path.join(diretorio, arquivo2_nome)

    # Ler os arquivos em DataFrames
    df1 = ler_arquivo(arquivo1)
    df2 = ler_arquivo(arquivo2)

    # Encontrar colunas correspondentes
    colunas_comuns = df1.columns.intersection(df2.columns)
    if len(colunas_comuns) == 0:
        st.error("Não há colunas correspondentes entre os dois arquivos.")
        return

    # Selecionar a coluna para comparação
    coluna_selecionada = st.selectbox("Selecione a coluna para comparar:", colunas_comuns)

    # Converter as colunas selecionadas para numérico
    serie1 = pd.to_numeric(df1[coluna_selecionada], errors='coerce')
    serie2 = pd.to_numeric(df2[coluna_selecionada], errors='coerce')

    # Criar um DataFrame combinado para facilitar o plot
    df_combined = pd.DataFrame({
        'Índice': serie1.index,
        f'{coluna_selecionada} - Arquivo 1': serie1,
        f'{coluna_selecionada} - Arquivo 2': serie2
    }).set_index('Índice')

    # Calcular a diferença entre as colunas
    df_combined['Diferença'] = df_combined.iloc[:, 0] - df_combined.iloc[:, 1]

    # Plotar o gráfico comparativo
    st.subheader(f"Comparação da coluna: {coluna_selecionada}")
    st.line_chart(df_combined[[f'{coluna_selecionada} - Arquivo 1', f'{coluna_selecionada} - Arquivo 2']])

    # Plotar o gráfico da diferença entre os valores
    st.subheader("Gráfico da Diferença entre os Valores")
    st.line_chart(df_combined['Diferença'])

    # Exibir tabela com os dados
    st.subheader("Dados Comparados")
    st.dataframe(df_combined)

    # Adicionar gráficos de dispersão (scatter plots)
    st.subheader("Gráficos de Dispersão")

    # Gráfico de dispersão dos valores dos dois arquivos
    fig1, ax1 = plt.subplots()
    ax1.scatter(df_combined.index, df_combined[f'{coluna_selecionada} - Arquivo 1'], label=f'{coluna_selecionada} - Arquivo 1', alpha=0.7)
    ax1.scatter(df_combined.index, df_combined[f'{coluna_selecionada} - Arquivo 2'], label=f'{coluna_selecionada} - Arquivo 2', alpha=0.7)
    ax1.set_xlabel('Índice')
    ax1.set_ylabel('Valor')
    ax1.set_title('Dispersão dos Valores dos Dois Arquivos')
    ax1.legend()
    st.pyplot(fig1)

    # Gráfico de dispersão da diferença em relação ao índice
    fig2, ax2 = plt.subplots()
    ax2.scatter(df_combined.index, df_combined['Diferença'], color='red', alpha=0.7)
    ax2.set_xlabel('Índice')
    ax2.set_ylabel('Diferença')
    ax2.set_title('Dispersão da Diferença dos Valores')
    st.pyplot(fig2)

    # Gráfico de dispersão dos valores do Arquivo 1 vs Arquivo 2
    fig3, ax3 = plt.subplots()
    ax3.scatter(df_combined[f'{coluna_selecionada} - Arquivo 1'], df_combined[f'{coluna_selecionada} - Arquivo 2'], alpha=0.7)
    ax3.set_xlabel(f'{coluna_selecionada} - Arquivo 1')
    ax3.set_ylabel(f'{coluna_selecionada} - Arquivo 2')
    ax3.set_title('Dispersão: Arquivo 1 vs Arquivo 2')
    st.pyplot(fig3)

    # Opcional: Destacar dados discrepantes
    st.subheader("Análise de Dados Discrepantes")

    # Definir um limiar para considerar discrepâncias significativas
    limiar = st.number_input("Defina o limiar para discrepâncias significativas:", value=0.001, step=0.001, format="%.6f")

    # Identificar discrepâncias acima do limiar
    discrepantes = df_combined[abs(df_combined['Diferença']) > limiar]

    if not discrepantes.empty:
        st.write(f"Encontrados {len(discrepantes)} valores discrepantes:")
        st.dataframe(discrepantes)
    else:
        st.write("Nenhum valor discrepante encontrado com o limiar definido.")

if __name__ == "__main__":
    main()



#PARA RODAR, DIGITAR PELO PROMPT:
#                           cd C:\Users\lgv_v\Documents\LUIZ
#                           streamlit run compararExcel.py