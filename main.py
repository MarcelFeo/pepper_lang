from Lexer import Lexer
from Parser import Parser
from Compiler import Compiler
from AST import Program
import json
import time
import re
import os

from argparse import ArgumentParser, Namespace

from llvmlite import ir
import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, c_float, c_char_p
import ctypes

def parse_arguments() -> Namespace:
    arg_parser = ArgumentParser(
        description="PepperLang v0.0.3-alpha"
    )

    arg_parser.add_argument("file_path", type=str, help="Path your entry point pepper file (ex: main.pep)")
    arg_parser.add_argument("--debug", action="store_true", help="Prints internal debug information")

    return arg_parser.parse_args()

# debug flags
LEXER_DEBUG: bool = False
PARSER_DEBUG: bool = False
COMPILER_DEBUG: bool = False
RUN_CODE: bool = True

PROD_DEBUG: bool = False

if __name__ == '__main__':
    args = parse_arguments()

    if args.debug:
        PROD_DEBUG = True

    file_path: str = "tests/default.pep"
    if args.file_path:
        file_path = args.file_path

    with open(file_path, "r") as f:
        code: str = f.read()

    # expand local imports of the form: import "file.pep";
    def _expand_imports(src: str, base_dir: str, _seen: set | None = None) -> str:
        if _seen is None:
            _seen = set()

        pattern = re.compile(r'^\s*import\s*"([^"]+)"\s*;\s*$', re.MULTILINE)

        def _repl(m: re.Match) -> str:
            fname = m.group(1)
            full = os.path.normpath(os.path.join(base_dir, fname))
            if full in _seen:
                return ""
            _seen.add(full)
            try:
                with open(full, 'r') as fh:
                    inner = fh.read()
            except Exception as e:
                print(f"COULD NOT OPEN IMPORT FILE {full}: {e}")
                return ""

            return _expand_imports(inner, os.path.dirname(full), _seen)

        return pattern.sub(lambda m: _repl(m), src)

    code = _expand_imports(code, os.path.dirname(os.path.abspath("tests/test_import.pep")))

    if LEXER_DEBUG:
        print("<<<  LEXER DEBUG >>>")
        debug_lex: Lexer = Lexer(source=code)
        while debug_lex.current_char is not None:
            print(debug_lex.next_token())

    l: Lexer = Lexer(source=code)
    p: Parser = Parser(lexer=l)

    parse_st: float = time.time()
    program: Program = p.parse_program()
    parse_et: float = time.time()

    if len(p.errors) > 0:
        for err in p.errors:
            print(err)
        exit(1)

    if PARSER_DEBUG:
        print("<<<  PARSER DEBUG  >>>")

        with open("debug/ast.json", "w") as f:
            json.dump(program.json(), f,indent=4)

        print("WROTE AST TO debug/ast.json SUCCESSFULLY!!!")

    c: Compiler = Compiler()

    compiler_st: float = time.time()
    c.compile(node=program)
    compiler_et: float = time.time()

    # output steps
    module: ir.Module = c.module
    module.triple = llvm.get_default_triple()

    if COMPILER_DEBUG:
        with open("debug/ir.obs", "w") as f:
            f.write(str(module))

    if RUN_CODE:
        # llvm.initialize() is no longer necessary (and now raises a
        # deprecation exception).  LLVM is initialized automatically by
        # llvmlite.binding on import, so we only need to set up the
        # native target and asm printer.
        # https://github.com/numba/llvmlite/issues/... (deprecation note)
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        try:
            llvm_ir_parser = llvm.parse_assembly(str(module))
            llvm_ir_parser.verify()
        except Exception as e:
            print(e)
            raise

        target_machine = llvm.Target.from_default_triple().create_target_machine()

        engine = llvm.create_mcjit_compiler(llvm_ir_parser, target_machine)
        # register a Python wrapper for printf so the JIT can resolve it
        def _py_printf(fmt, val):
            try:
                s = ctypes.cast(fmt, ctypes.c_char_p).value.decode('utf-8')
            except Exception:
                s = fmt
            try:
                out = s % val
            except Exception:
                out = s
            print(out, end='')
            return len(out)

        py_printf_c = CFUNCTYPE(c_int, c_char_p, c_int)(_py_printf)
        llvm.add_symbol("printf", ctypes.cast(py_printf_c, ctypes.c_void_p).value)

        engine.finalize_object()

        entry = engine.get_function_address("main")

        # Select appropriate ctypes return type based on compiled `main` signature
        main_fn = module.get_global('main')
        ret_type = main_fn.function_type.return_type
        if isinstance(ret_type, ir.FloatType):
            cfunc = CFUNCTYPE(c_float)(entry)
        else:
            cfunc = CFUNCTYPE(c_int)(entry)

        st = time.time()

        result = cfunc()

        et = time.time()

        if PROD_DEBUG:
            print(f"RESULT: {result}")
            print(f"PARSE TIME: {parse_et - parse_st:.6f} seconds")
            print(f"COMPILE TIME: {compiler_et - compiler_st:.6f} seconds")
            print(f"EXECUTION TIME: {et - st:.6f} seconds")
