# Obsidian Compiler
# Linguagem Obsidian — Documento de Referência

Esta documentação descreve a sintaxe, semântica e limitações atuais da linguagem "Obsidian" e como usar o compilador disponível neste repositório.

## Visão Geral

Obsidian é uma linguagem imperativa e tipada (estaticamente em notação), desenvolvida como um projeto educacional para demonstrar fases clássicas de compilador: lexer, parser, geração de AST e geração de LLVM IR. A implementação atual gera código LLVM usando `llvmlite` e pode executar programas via JIT.

## Sintaxe e Gramática Essencial

Observações gerais:
- Blocos usam chaves `{ ... }`.
- Instruções terminam em `;` quando necessário.
- Comentários ainda não formalizados (considere usar apenas código limpo nos exemplos).

### Declaração de Variáveis

Forma:

```
let <ident>$<tipo> -> <expressão>;
```

Exemplos:

```
let a$int -> 5;
let x$float -> 3.14;
```

Notas:
- O tipo é escrito após `$` (por exemplo `a$int`).
- A declaração aloca um espaço para a variável e armazena o valor inicial.

### Atribuição

Forma:

```
<ident> -> <expressão>;
```

Exemplo:

```
a -> 10;
```

### Funções

Assinatura:

```
fun <nome>(<params>): <tipo_retorno> { ... }
```

Exemplo básico:

```
fun main(): int {
    let a$int -> 4;
    a -> a * 2;
    return a;
}
```

Observações:
- O parser consome a lista de parâmetros, mas ainda não há suporte completo para tipos e nomes de parâmetros no gerador de código (implementação futura).

### Expressões e Operadores

- Literais: inteiros (ex.: `10`), floats (ex.: `3.14`).
- Identificadores: nomes alfanuméricos.
- Operadores aritméticos: `+`, `-`, `*`, `/`, `%`.
- Operador de potência: `**` (sintaxe suportada pelo parser, sem implementação completa no backend).
- Comparações: `<`, `<=`, `>`, `>=`, `==`, `!=`.
- Operadores booleanos ainda limitados — comparação produz `bool` (representado internamente como `i1` em LLVM).

Precedência de operadores é tratada no parser (ver `Parser.py`).

### Controle de Fluxo — `if` / `else`

Forma:

```
if <condicao> { <consequencia> } else { <alternativa> }
```

Exemplo:

```
if a == 5 {
    a -> 10;
} else {
    a -> 20;
}
```

Semântica atual:
- `if` avalia a condição (uma expressão booleana) e executa o bloco consequente quando verdadeira.
- `else` é opcional; quando presente, produz um ramo alternativo.
- O compilador traduz `if`/`else` para blocos condicionais LLVM; mudanças recentes corrigiram bugs na detecção/consumo do token `else` e na geração do IR correspondente.

### `return`

Usado dentro de funções para retornar um valor:

```
return <expressao>;
```

## Tipos Suportados

- `int` — inteiro de 32 bits (LLVM `i32`).
- `float` — ponto flutuante (LLVM `float`).
- `bool` — valor booleano representado como `i1` em LLVM.

Observações: tipagem estática explícita (o tipo aparece na declaração `let` e em assinaturas de função) mas o sistema atual ainda não faz checagem completa de tipos em todos os caminhos.

## Módulos Principais do Compilador

- `Lexer.py`: tokenização.
- `Parser.py`: construção da AST (utiliza funções de prefix/infix parsing e mapa de precedência).
- `AST.py`: modelos de nós da AST.
- `Compiler.py`: geração de LLVM IR usando `llvmlite` e um `Environment` para variáveis.
- `Environment.py`: tabela de símbolos, mapeando nomes para ponteiros LLVM e tipos.
- `main.py`: orquestra leitura do arquivo de entrada, parsing, compilação e execução JIT.

## Limitações Atuais e Pontos Conhecidos

- Operador de potência `**` não está implementado no backend.
- Suporte a parâmetros de função está parcial (parâmetros são consumidos no parser, mas tipos/uso em código ainda não completos).
- Inferência de tipos, checagem de tipos mais completa e tratamento de erros semânticos ainda a implementar.
- Sistema de módulos/import ainda não existe.

## Como Compilar e Executar

Pré-requisitos:

- Python 3.8+
- `llvmlite` instalado (`pip install llvmlite`)
- LLVM adequado ao seu ambiente (para JIT nativo)

Executar (por padrão `main.py` lê `tests/test_if.obs`):

```bash
python main.py
```

Flags de depuração em `main.py`:
- `LEXER_DEBUG = True` — imprime tokens do lexer.
- `PARSER_DEBUG = True` — salva AST em `debug/ast.json`.
- `COMPILER_DEBUG = True` — salva IR em `debug/ir.obs`.

## Exemplo Completo

Arquivo `tests/test_if.obs`:

```
fun main(): int {
    let a$int -> 5;

    if a == 5 {
        a -> 10;
    } else {
        a -> 20;
    }

    return a;
}
```

Esperado: o `if` altera `a` para `10` quando `a == 5`, caso contrário para `20`. O runtime JIT retorna o inteiro final da função `main`.

## Desenvolvimento e Contribuição

- Abra issues para bugs/evoluções.
- Pull requests são bem-vindos; foque em testes de unidade e exemplos em `tests/`.

## Mudanças Recentes (resumo)

- Corrigido parsing de `if/else` em `Parser.py` para consumir corretamente `else` e blocos.
- Corrigida geração de `if/else` em `Compiler.py` para emitir corretamente ramos `then` e `else`.

---

Arquivo principal de documentação: [README.md](README.md)

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

## Mudanças Recentes

- Parser (`Parser.py`): Corrigido `__parse_if_expression` para detectar e consumir corretamente o token `else` e os blocos `{}` associados, evitando que tokens de chave sejam deixados como `current_token` sem uma função de prefixo.
- Parser (`Parser.py`): Melhorias no parsing de declarações de função (`__parse_function_statement`) — agora consumimos corretamente os parâmetros (mesmo quando não implementados) e o tipo de retorno, evitando dessincronização do parser.
- Compiler (`Compiler.py`): Corrigida a lógica de `__visit_if_statement` que estava invertida — agora gera um `if/else` quando há alternativa, ou um `if` simples quando não há.
- Vários pequenos ajustes de consistência e comentários para clarificar o fluxo de parsing/compilação.

Próximos passos recomendados:
- Rodar os testes em `tests/` para validar os casos de controle de fluxo.
- Verificar `debug/ast.json` para inspecionar AST gerada para `if`/`else`.

