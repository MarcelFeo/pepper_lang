from Lexer import Lexer
from Parser import Parser
from Compiler import Compiler
from AST import Program
import json
import time

from llvmlite import ir
import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, c_float, c_char_p
import ctypes

# debug flags
LEXER_DEBUG: bool = False
PARSER_DEBUG: bool = False
COMPILER_DEBUG: bool = True
RUN_CODE: bool = True

if __name__ == '__main__':
    with open("tests/test_prefix.obs", "r") as f:
        code: str = f.read()

    if LEXER_DEBUG:
        print("<<<  LEXER DEBUG >>>")
        debug_lex: Lexer = Lexer(source=code)
        while debug_lex.current_char is not None:
            print(debug_lex.next_token())

    l: Lexer = Lexer(source=code)
    p: Parser = Parser(lexer=l)

    program: Program = p.parse_program()
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
    c.compile(node=program)

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
