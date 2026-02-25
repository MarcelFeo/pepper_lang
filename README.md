# Obsidian Language Compiler - PROJECT IN PROGRESS

A simple compiler for a custom language ("Obsidian") implemented in Python, using [llvmlite](https://github.com/numba/llvmlite) for LLVM IR code generation.

## Features

- **Lexer**: Tokenizes source code into tokens.
- **Parser**: Builds an Abstract Syntax Tree (AST) from tokens.
- **Compiler**: Generates LLVM IR from the AST.
- **Custom Language**: Supports variable declarations, arithmetic expressions, and basic types (`int`, `float`).
- **Debugging**: Outputs AST as JSON and LLVM IR for inspection.

## Project Structure

```
AST.py              # AST node definitions
Compiler.py         # LLVM IR code generation
Environment.py      # Variable environment for codegen
Lexer.py            # Tokenizer
main.py             # Entry point
Parser.py           # Parser (AST builder)
Token.py            # Token types and utilities
debug/
    ast.json        # Last generated AST (JSON)
    ir.obs          # Last generated LLVM IR
tests/
    compiler.obs    # Test input for compiler
    lexer.obs       # Test input for lexer
    parser.obs      # Test input for parser
    test.obs        # Main test input
```

## Language Syntax

### Variable Declaration

```
let a$int -> 10;
make b$int equal 15 now
let c$float -> 22.2;
make d$float equal 4.20 now
```

- `let` or `make` to declare.
- `$` separates name and type.
- `->` or `equal ... now` for assignment.
- `;` or `now` to end statement.

### Expressions

Supports arithmetic: `+`, `-`, `.`, `/`, `%`, `^` (power, not yet implemented).

Example:
```
2 + 3 x 4;
(4 - 3) x 100 / (8 + 7) - 3e5;
4 % 2;
```

## Usage

### Requirements

- Python 3.10+
- [llvmlite](https://github.com/numba/llvmlite)

Install dependencies:
```sh
pip install llvmlite
```

### Running

Run the main compiler:
```sh
python main.py
```
This will read `tests/test.obs`, parse, compile, and output:
- AST as `debug/ast.json`
- LLVM IR as `debug/ir.obs`

### Debug Flags

Set these in `main.py`:
- `LEXER_DEBUG = True` — print tokens
- `PARSER_DEBUG = True` — dump AST
- `COMPILER_DEBUG = True` — dump LLVM IR

## File Descriptions

- [`AST.py`](AST.py): AST node classes and serialization.
- [`Compiler.py`](Compiler.py): LLVM IR code generation ([`Compiler`](Compiler.py)).
- [`Environment.py`](Environment.py): Variable environment ([`Environment`](Environment.py)).
- [`Lexer.py`](Lexer.py): Tokenizer ([`Lexer`](Lexer.py)).
- [`Parser.py`](Parser.py): Parser ([`Parser`](Parser.py)).
- [`Token.py`](Token.py): Token types, keywords, and lookup ([`TokenType`](Token.py), [`lookup_ident`](Token.py)).
- [`main.py`](main.py): Entry point, orchestrates compilation.

## Testing

Test files are in [`tests/`](tests/):
- [`test.obs`](tests/test.obs): Main test input.
- [`lexer.obs`](tests/lexer.obs): Lexer test.
- [`parser.obs`](tests/parser.obs): Parser test.
- [`compiler.obs`](tests/compiler.obs): Compiler test.

## Output

- [`debug/ast.json`](debug/ast.json): Last parsed AST (JSON).
- [`debug/ir.obs`](debug/ir.obs): Last generated LLVM IR.

## Extending

- Add new syntax: Update [`Token.py`](Token.py), [`Lexer.py`](Lexer.py), [`Parser.py`](Parser.py), and [`AST.py`](AST.py).
- Add new codegen: Update [`Compiler.py`](Compiler.py).

## License

MIT License (add your license here).

---

*This project is a learning compiler for a custom language, not intended for production use.*
