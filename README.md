# Obsidian Compiler

## Descrição do Projeto

O **Obsidian Compiler** é um compilador completo para a linguagem de programação **Obsidian**, uma linguagem simples e imperativa projetada para fins educacionais e de demonstração. O compilador traduz código fonte escrito em Obsidian para código intermediário LLVM (IR), que pode ser executado diretamente usando o runtime LLVM. O projeto é implementado em Python e utiliza a biblioteca `llvmlite` para geração de código LLVM, permitindo a compilação just-in-time (JIT) e execução eficiente.

O objetivo principal do projeto é demonstrar os conceitos fundamentais de compiladores, incluindo análise léxica, parsing, geração de código intermediário e execução. A linguagem Obsidian suporta variáveis, expressões aritméticas, funções, controle de fluxo básico e tipos simples como inteiros e floats.

## Funcionamento da Linguagem Obsidian

### Visão Geral
Obsidian é uma linguagem imperativa com sintaxe inspirada em linguagens como C e Python, mas simplificada. Ela suporta:
- Declaração e atribuição de variáveis.
- Expressões aritméticas com operadores básicos.
- Definição de funções.
- Estruturas de controle como blocos e retornos.

O compilador processa o código fonte em várias fases:
1. **Análise Léxica (Lexer)**: Converte o código fonte em tokens.
2. **Análise Sintática (Parser)**: Constrói uma Árvore de Sintaxe Abstrata (AST) a partir dos tokens.
3. **Compilação (Compiler)**: Gera código LLVM IR a partir da AST.
4. **Execução (Opcional)**: Usa LLVM para executar o código compilado.

### Sintaxe da Linguagem

#### Declaração de Variáveis
```
let nome$tipo -> valor;
```
Exemplo:
```
let a$int -> 10;
let b$float -> 3.14;
```

#### Atribuição
```
nome -> expressão;
```
Exemplo:
```
a -> a * 2;
```

#### Funções
```
fun nome(parametros): tipo_retorno {
    // corpo da função
    return expressão;
}
```
Exemplo:
```
fun main(): int {
    let a$int -> 4;
    a -> a * 2;
    return a;
}
```

#### Expressões
- Literais: `10`, `3.14`
- Identificadores: `a`, `b`
- Operadores aritméticos: `+`, `-`, `*`, `/`, `%`, `**` (potência, não implementado)
- Agrupamento: `(expressão)`

#### Tipos Suportados
- `int`: Inteiro de 32 bits.
- `float`: Ponto flutuante.

### Como o Compilador Funciona

O compilador é dividido em módulos principais:

- **Lexer.py**: Responsável pela tokenização. Lê o código fonte e gera uma sequência de tokens.
- **Parser.py**: Constrói a AST a partir dos tokens, usando precedência de operadores.
- **AST.py**: Define as estruturas de dados para a árvore de sintaxe.
- **Compiler.py**: Gera código LLVM IR a partir da AST. Usa um ambiente (Environment) para gerenciar variáveis.
- **Environment.py**: Gerencia o escopo de variáveis, armazenando ponteiros LLVM.
- **Token.py**: Define os tipos de tokens.
- **main.py**: Ponto de entrada, coordena as fases de compilação e execução opcional.

Durante a compilação, variáveis são alocadas na pilha usando `alloca`, e operações são traduzidas para instruções LLVM correspondentes.

## Dependências e Motivos de Uso

O projeto utiliza as seguintes bibliotecas Python:

- **llvmlite**: Biblioteca para geração e manipulação de código LLVM IR. É usada porque LLVM é um backend robusto e eficiente para compilação, permitindo otimização e execução JIT. `llvmlite` fornece uma interface Python para LLVM, facilitando a geração de código sem precisar de C++.

- **ctypes**: Biblioteca padrão do Python para chamar funções C. É usada para executar o código compilado, criando ponteiros de função a partir do endereço gerado pelo LLVM JIT. Permite a integração direta com código nativo.

- **json**: Biblioteca padrão para manipulação de JSON. É usada para depuração, salvando a AST em formato JSON no arquivo `debug/ast.json`.

- **time**: Biblioteca padrão para medição de tempo. É usada para medir o tempo de execução do código compilado, fornecendo feedback de performance.

Nenhuma outra dependência externa é necessária, mantendo o projeto leve e fácil de instalar.

## Como Usar

### Pré-requisitos
- Python 3.8+
- LLVM instalado (para execução JIT)

### Instalação
Clone o repositório e instale as dependências:
```
pip install llvmlite
```

### Compilação e Execução
1. Escreva código Obsidian em um arquivo, e.g., `tests/test_fun.obs`.
2. Execute o compilador:
   ```
   python main.py
   ```
   - O código em `tests/test_fun.obs` será compilado.
   - Se `RUN_CODE = True` em `main.py`, o código será executado e o resultado impresso.
   - Se `COMPILER_DEBUG = True`, o IR LLVM será salvo em `debug/ir.obs`.

### Exemplos
Veja os arquivos em `tests/`:
- `test.obs`: Exemplo simples.
- `test_fun.obs`: Função main com operações.

### Depuração
- `LEXER_DEBUG`: Imprime tokens.
- `PARSER_DEBUG`: Salva AST em JSON.
- `COMPILER_DEBUG`: Salva IR LLVM.

## Contribuição
Contribuições são bem-vindas! Abra issues para bugs ou sugestões, e pull requests para melhorias.
