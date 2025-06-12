# Compilador da Linguagem Coins

Este projeto implementa um compilador completo para a linguagem Coins, desenvolvido como parte do trabalho da disciplina de Compiladores. O compilador inclui analisadores léxico, sintático e semântico, além de um gerador de código Python.

## Estrutura do Projeto

O projeto está organizado nas seguintes pastas:

- **src/**: Arquivos-fonte do compilador
  - `analisador_lexico.py`: Implementação do analisador léxico
  - `analisador_sintatico.py`: Implementação do analisador sintático
  - `analisador_semantico.py`: Implementação do analisador semântico
  - `gerador_codigo.py`: Gerador de código Python
  - `compilador.py`: Script principal que integra todas as fases do compilador

- **docs/**: Documentação do projeto
  - `TDE-Compiladores-Vespertino.pdf`: Requisitos originais do trabalho

- **examples/**: Exemplos de código na linguagem Coins
  - `codigo.txt`: Exemplo de código com casos válidos e inválidos

## Como Usar

1. Coloque seu código fonte no arquivo `examples/codigo.txt`
2. Execute o compilador:
   ```
   python3 src/compilador.py
   ```

## Características da Linguagem Coins

- **Tipos de dados**: inteiro, real, texto
- **Estruturas de controle**: se/senao, enquanto
- **Subrotinas**: procedimentos e funções com parâmetros
- **Operadores**:
  - Aritméticos: +, -, *, /, %
  - Lógicos: &&, ||, !
  - Comparação: ==, !=, >, <, >=, <=
- **Comentários**: suporte para comentários de linha (//) e bloco (/* */)
