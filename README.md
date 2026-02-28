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
# Obsidian — a small experimental language and compiler

Obsidian is a compact, educational compiler project written in Python that
demonstrates a simple front-end (lexer + parser → AST) and a back-end that
emits LLVM IR using `llvmlite`.  The goal is to be a clear learning codebase
for language tooling and code generation experiments.

**Status:** actively developed; tests and examples are included.

**Key ideas:**
- Small, explicit AST representation (`AST.py`).
- Hand-written recursive-descent parser (`Parser.py`).
- LLVM IR generation via `llvmlite` (`Compiler.py`).
- Minimal runtime: functions, local variables and arithmetic.

**Repository layout**

- `AST.py` — AST node classes and JSON serialization helpers.
- `Lexer.py` — tokenizer that maps source text to `Token` values.
- `Parser.py` — builds the AST from tokens (recursive-descent).
- `Token.py` — token types, keywords and utility lookup.
- `Compiler.py` — lowers AST to `llvmlite.ir` (LLVM IR) and provides
    a small runtime harness in `main.py` for JIT execution.
- `Environment.py` — symbol table / variable environment for codegen.
- `main.py` — example runner that parses, compiles and optionally runs
    the generated code.
- `tests/` — small sample inputs used by the project.
- `debug/` — generated artifacts (AST JSON, IR) produced when running.

Language overview
-----------------

The language is intentionally small. Current features include:

- Function declarations (keywords `fn` and `fun` are accepted).
- Local variable declarations with explicit types.
- Integer and float literals.
- Basic binary arithmetic: `+`, `-`, `.` (multiply), `/`, `%`, and `^` (power planned).
- `return` statements inside functions.

Syntax examples
---------------

Function with a local variable and a return:

```
fun main(): int {
        let a$int -> 4;
        return a;
}
```

Variable declarations support two flavors (legacy alternatives exist in
tests):

```
let x$int -> 10;        # canonical
make y$int equal 15 now # alternative keyword forms
```

Tokens and keywords
-------------------

See `Token.py` for the full token set. Keywords include `let`, `fn`/`fun`, and
`return`. Types currently recognized are `int` and `float` (mapped to i32 and
float in LLVM IR).

Requirements
------------

- Python 3.10+
- `llvmlite` (install with pip)

Quick setup
-----------

Install the only external dependency:

```bash
pip install llvmlite
```

Running the compiler
--------------------

The repository includes `main.py`, an example entry point. By default it
parses `tests/test_fun.obs`, compiles it to LLVM IR and can JIT-run the
function via `llvmlite.binding`.

Basic run (from repository root):

```bash
python main.py
```

The `main.py` script contains debug flags at the top that control behavior:

- `LEXER_DEBUG` — print tokens from the lexer.
- `PARSER_DEBUG` — dump AST JSON to `debug/ast.json`.
- `COMPILER_DEBUG` — write the generated IR to `debug/ir.obs`.
- `RUN_CODE` — whether to JIT-execute the compiled function.

When `PARSER_DEBUG` is enabled the tool writes a human-readable AST JSON to
`debug/ast.json` which is convenient for understanding parser output.

Extending the language
----------------------

To add new syntax you typically need to change these components:

1. `Token.py` — add new token kinds or keywords.
2. `Lexer.py` — recognize the new token(s) in `next_token()`.
3. `AST.py` — add AST nodes for new constructs and JSON serialization.
4. `Parser.py` — implement parsing rules and register prefix/infix handlers.
5. `Compiler.py` — implement codegen for the new AST nodes.

Testing and examples
--------------------

Simple input files for testing live in the `tests/` directory. Use them as
starting points when adding features.

Development notes
-----------------

- The project is intentionally explicit and easy to follow — it is a learning
    playground rather than a production compiler.
- Function parameter parsing is currently minimal (parameters are skipped).
    If you want full parameter support, update `Parser.__parse_function_statement`
    and wire parameter types into `Compiler.__visit_function_statement`.
- LLVM initialization is handled by `llvmlite.binding` automatically; avoid
    calling `llvm.initialize()` directly (it's deprecated).

Contributing
------------

Contributions and suggestions are welcome. If you add features, please
provide tests under `tests/` and update this README with language changes.

License
-------

This project is provided for learning and experimentation. No license is
specified — add one if you plan to share or reuse this code externally.
