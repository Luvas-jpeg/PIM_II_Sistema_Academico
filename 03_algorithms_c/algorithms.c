// 03_algorithms_c/algorithms.c

#include <stdio.h>  // Para printf
#include <stdlib.h> // Para malloc, free, qsort
#include <string.h> // Para memcpy (se necessário)

// --- Estruturas de Dados ---

// Estrutura para representar o desempenho de um aluno (para ordenação)
typedef struct {
    int id_aluno;         // Identificador do aluno
    float media_final;    // Média calculada (usada para ordenar)
} DesempenhoAluno;

// --- Funções Principais (Exportáveis para Python) ---

/**
 * @brief Calcula a média ponderada de um array de notas e pesos.
 * * @param notas Ponteiro para o array de notas.
 * @param pesos Ponteiro para o array de pesos correspondentes.
 * @param count O número de notas/pesos no array.
 * @return float A média ponderada calculada. Retorna 0.0 se count <= 0 ou soma dos pesos for 0.
 */
float calcular_media_ponderada(const float *notas, const float *pesos, int count) {
    if (count <= 0) {
        return 0.0f;
    }

    float soma_produtos = 0.0f;
    float soma_pesos = 0.0f;

    for (int i = 0; i < count; i++) {
        soma_produtos += notas[i] * pesos[i];
        soma_pesos += pesos[i];
    }

    // Evita divisão por zero
    if (soma_pesos == 0.0f) {
        return 0.0f;
    }

    return soma_produtos / soma_pesos;
}

/**
 * @brief Função de comparação usada pelo qsort para ordenar DesempenhoAluno.
 * Ordena da maior média para a menor.
 */
int comparar_desempenho(const void *a, const void *b) {
    DesempenhoAluno *alunoA = (DesempenhoAluno *)a;
    DesempenhoAluno *alunoB = (DesempenhoAluno *)b;

    // Compara as médias para ordenação decrescente
    if (alunoA->media_final < alunoB->media_final) {
        return 1; // B vem antes de A
    } else if (alunoA->media_final > alunoB->media_final) {
        return -1; // A vem antes de B
    } else {
        // Se as médias forem iguais, mantém a ordem original (ou ordena por ID, se preferir)
        return 0; 
    }
}

/**
 * @brief Ordena um array de estruturas DesempenhoAluno pela média final (decrescente).
 * Modifica o array original.
 * * @param desempenhos Ponteiro para o array de DesempenhoAluno.
 * @param num_alunos O número de alunos no array.
 */
void ordenar_por_desempenho(DesempenhoAluno *desempenhos, int num_alunos) {
    if (desempenhos == NULL || num_alunos <= 1) {
        return; // Nada a ordenar
    }
    // qsort: função padrão do C para ordenação eficiente (Quick Sort)
    qsort(desempenhos, num_alunos, sizeof(DesempenhoAluno), comparar_desempenho);
}

// --- Função Main (Para Teste Direto em C) ---
// Esta função NÃO será chamada pelo Python, serve apenas para compilar e testar o C isoladamente.
int main() {
    printf("--- Testando Módulo de Algoritmos em C ---\n");

    // Teste 1: Cálculo de Média Ponderada
    float notas_teste[] = {7.5f, 9.0f, 6.0f};
    float pesos_teste[] = {2.0f, 3.0f, 5.0f}; // Ex: NP1 peso 2, NP2 peso 3, Exame peso 5
    int n_notas = sizeof(notas_teste) / sizeof(notas_teste[0]);
    
    float media = calcular_media_ponderada(notas_teste, pesos_teste, n_notas);
    printf("1. Média Ponderada Calculada: %.2f\n", media); // Esperado: (7.5*2 + 9*3 + 6*5) / (2+3+5) = 72 / 10 = 7.2

    // Teste 2: Ordenação de Desempenho
    DesempenhoAluno turma[] = {
        {101, 8.5f},
        {102, 6.2f},
        {103, 9.8f},
        {104, 7.5f}
    };
    int n_alunos = sizeof(turma) / sizeof(turma[0]);

    printf("\n2. Ordenando Desempenho da Turma (Original):\n");
    for (int i = 0; i < n_alunos; i++) {
        printf("   ID: %d, Média: %.2f\n", turma[i].id_aluno, turma[i].media_final);
    }

    ordenar_por_desempenho(turma, n_alunos);

    printf("\n   Desempenho Ordenado (Melhor para Pior):\n");
    for (int i = 0; i < n_alunos; i++) {
        printf("   ID: %d, Média: %.2f\n", turma[i].id_aluno, turma[i].media_final);
    }
    // Esperado: ID 103 (9.8), ID 101 (8.5), ID 104 (7.5), ID 102 (6.2)

    return 0; // Indica sucesso
}