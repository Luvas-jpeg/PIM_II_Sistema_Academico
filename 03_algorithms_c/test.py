# 03_algorithms_c/test_algorithms.py

import ctypes # Biblioteca padrão do Python para carregar bibliotecas C
import os
import platform # Para saber se é Windows, Linux ou Mac

# --- 1. Definir Estruturas de Dados (Espelho do C) ---
# Precisamos recriar a struct 'DesempenhoAluno' em Python
class DesempenhoAluno(ctypes.Structure):
    _fields_ = [
        ("id_aluno", ctypes.c_int),
        ("media_final", ctypes.c_float)
    ]

# --- 2. Carregar a Biblioteca Dinâmica (.dll ou .so) ---

lib_path = ""
# Define o nome do arquivo da biblioteca com base no Sistema Operacional
if platform.system() == "Windows":
    lib_path = os.path.join(os.path.dirname(__file__), "algorithms.dll")
elif platform.system() == "Darwin": # macOS
    lib_path = os.path.join(os.path.dirname(__file__), "algorithms.so")
else: # Linux
    lib_path = os.path.join(os.path.dirname(__file__), "algorithms.so")

print(f"Tentando carregar a biblioteca C de: {lib_path}")

try:
    # Carrega a biblioteca na memória
    lib_c = ctypes.CDLL(lib_path) 
    print("Biblioteca C carregada com sucesso!")
except OSError as e:
    print(f"ERRO: Não foi possível carregar a biblioteca '{lib_path}'.")
    print(f"   Verifique se o arquivo foi compilado (compile.bat ou compile.sh).")
    print(f"   Detalhe do Erro: {e}")
    exit(1)

# --- 3. Definir Tipos de Argumento e Retorno (Interface Python <-> C) ---

# --- Função 1: calcular_media_ponderada ---
# Define os tipos de argumento (argtypes)
lib_c.calcular_media_ponderada.argtypes = [
    ctypes.POINTER(ctypes.c_float), # Ponteiro para array de notas (float*)
    ctypes.POINTER(ctypes.c_float), # Ponteiro para array de pesos (float*)
    ctypes.c_int                    # Contagem (int)
]
# Define o tipo de retorno (restype)
lib_c.calcular_media_ponderada.restype = ctypes.c_float

# --- Função 2: ordenar_por_desempenho ---
lib_c.ordenar_por_desempenho.argtypes = [
    ctypes.POINTER(DesempenhoAluno), # Ponteiro para array da struct (DesempenhoAluno*)
    ctypes.c_int                     # Contagem (int)
]
lib_c.ordenar_por_desempenho.restype = None # É uma função void (não retorna nada)


# --- 4. Executar os Testes em Python ---

print("\n--- Teste 1: Chamando C para calcular Média Ponderada ---")
# Prepara os dados em Python
notas_py = [7.5, 9.0, 6.0]
pesos_py = [2.0, 3.0, 5.0]
count = len(notas_py)

# Converte os dados Python para tipos ctypes (Arrays C)
NotasArrayType = ctypes.c_float * count
notas_c = NotasArrayType(*notas_py)
PesosArrayType = ctypes.c_float * count
pesos_c = PesosArrayType(*pesos_py)

# Chama a função C
media_c = lib_c.calcular_media_ponderada(notas_c, pesos_c, count)
print(f"Python chamou C. Média Ponderada: {media_c:.2f} (Esperado: 7.20)")


print("\n--- Teste 2: Chamando C para Ordenar Desempenho ---")
# Prepara os dados em Python (lista de structs)
turma_py = [
    DesempenhoAluno(id_aluno=101, media_final=8.5),
    DesempenhoAluno(id_aluno=102, media_final=6.2),
    DesempenhoAluno(id_aluno=103, media_final=9.8),
    DesempenhoAluno(id_aluno=104, media_final=7.5)
]
count_alunos = len(turma_py)

# Converte para um Array C da struct
TurmaArrayType = DesempenhoAluno * count_alunos
turma_c = TurmaArrayType(*turma_py)

print("  Valores Originais:")
for aluno in turma_c:
    print(f"    ID: {aluno.id_aluno}, Média: {aluno.media_final:.2f}")

# Chama a função C (que modifica o array 'turma_c' diretamente)
lib_c.ordenar_por_desempenho(turma_c, count_alunos)

print("\n  Valores Ordenados (pela função C):")
for aluno in turma_c:
    print(f"    ID: {aluno.id_aluno}, Média: {aluno.media_final:.2f}")

print("\n--- Integração C <-> Python concluída! ---")