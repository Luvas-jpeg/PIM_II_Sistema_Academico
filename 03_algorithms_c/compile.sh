#!/bin/bash
# 03_algorithms_c/compile.sh

# Nome do arquivo C de origem
SOURCE_FILE="algorithms.c"
# Nome da biblioteca compartilhada a ser gerada (.so para Linux/macOS)
OUTPUT_LIB="algorithms.so"

echo "⚙️  Compilando '$SOURCE_FILE' em '$OUTPUT_LIB'..."

# Comando de compilação usando gcc
# -fPIC: Gera código de posição independente (necessário para bibliotecas compartilhadas)
# -shared: Cria uma biblioteca compartilhada (.so) em vez de um executável
# -o [nome_saida]: Especifica o nome do arquivo de saída
gcc -fPIC -shared "$SOURCE_FILE" -o "$OUTPUT_LIB"

# Verifica se a compilação foi bem-sucedida
if [ $? -eq 0 ]; then
  echo "✅ Compilação concluída com sucesso! Biblioteca '$OUTPUT_LIB' criada."
else
  echo "❌ Erro durante a compilação."
  exit 1 # Sai com código de erro
fi

echo "Para testar o executável C diretamente (função main):"
echo "gcc $SOURCE_FILE -o algorithms_test -lm" 
# O -lm é necessário se você usar funções matemáticas como sqrt, pow, etc. (não usamos aqui)
echo "E então execute: ./algorithms_test"

exit 0 # Sai com sucesso