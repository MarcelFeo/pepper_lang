# Obsidian Compiler
# Linguagem Obsidian — Documento de Referência

Esta documentação descreve a sintaxe, semântica e limitações atuais da linguagem "Obsidian" e como usar o compilador disponível neste repositório.

## Visão Geral

Obsidian é uma linguagem imperativa e tipada (estaticamente em notação), desenvolvida como um projeto educacional para demonstrar fases clássicas de compilador: lexer, parser, geração de AST e geração de LLVM IR. A implementação atual gera código LLVM usando `llvmlite` e pode executar programas via JIT.
# Obsidian Compiler

Obsidian é uma linguagem imperativa didática implementada neste repositório com um pipeline mínimo de compilador: lexer, parser, AST e geração de LLVM IR (via `llvmlite`). O projeto demonstra etapas clássicas de compilação e permite executar programas por JIT.

Este README traz um resumo rápido de uso, sintaxe essencial, exemplos e instruções de desenvolvimento.

## Sumário rápido

- Instalar dependências: `pip install llvmlite`
- Executar (por padrão o `main.py` lê `tests/test_for.obs`):

```bash
python main.py
```

- Ajuste as flags de debug em `main.py` (`LEXER_DEBUG`, `PARSER_DEBUG`, `COMPILER_DEBUG`, `RUN_CODE`).

## Sintaxe essencial

- Declaração de variável:

```
let name$int -> 5;
```

- Atribuição:

```
name -> expr;
```

- Função:

```
fun main(): int {
    return 0;
}
```

- Laços e controle:
  - `if <cond> { ... } [else { ... }]`
  - `while <cond> { ... }`
  - `for (<init>; <cond>, <post>) { ... }`  (sintaxe: init; condition, post)
  - `break;`, `continue;`

Exemplo de `for` (existe em `tests/test_for.obs`):

```
for (let i$int = 0; i < 10, i -> i + 1) {
    if (i == 2) { continue; }
    if (i == 5) { break; }
    printf("i = %i\n", i);
}
```

## Tipos suportados

- `int` — i32
- `float` — float
- `bool` — i1 (internamente)

Observação: há checagem de tipos incompleta em caminhos mais complexos; use exemplos em `tests/` como referência.

## Arquitetura do projeto (arquivos principais)

- `Lexer.py` — tokenização
- `Parser.py` — constrói AST
- `AST.py` — definições dos nós AST
- `Compiler.py` — gera LLVM IR com `llvmlite`
- `Environment.py` — ambiente/escopo de variáveis
- `Token.py` — tipos e lookup de palavras-chave
- `main.py` — orquestra leitura, parsing, compilação e execução JIT

## Instalação e execução

1. Instale dependências:

```bash
pip install llvmlite
```

2. Execute o compilador/runner:

```bash
python main.py
```

Observações:

- `main.py` lê por padrão `tests/test_for.obs`. Para testar outros arquivos, edite `main.py` ou substitua o conteúdo de `tests/test_for.obs`.
- Para salvar o IR gerado, ative `COMPILER_DEBUG = True` em `main.py` (gera `debug/ir.obs`).

## Testes e exemplos

Os exemplos estão em `tests/` (por ex. `test.obs`, `test_for.obs`, `test_while.obs`). Execute `python main.py` para compilar/rodar o exemplo atual.

## Desenvolvimento

- Para adicionar novas features, foque em `Lexer.py` → `Parser.py` → `AST.py` → `Compiler.py`.
- Use `PARSER_DEBUG = True` para gerar `debug/ast.json` e inspecionar a AST.

## Mudanças recentes e notas

- Implementado suporte ao laço `for` (parser + AST + geração de IR) e tratamento de `break`/`continue`.
- Ajustes no parser para evitar dessincronização ao consumir tokens de parênteses e chaves.
- O operador de potência (`**`) não tem backend implementado ainda.

## Como contribuir

- Abra uma issue descrevendo o problema ou a melhoria.
- Faça um fork, crie uma branch e envie um pull request com testes (adicionar exemplos em `tests/`).

---

Arquivo principal de documentação: `README.md`
- `AST.py`: modelos de nós da AST.

