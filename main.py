from Lexer import Lexer
from Parser import Parser
from Compiler import Compiler
from AST import Program
import json
import time

from llvmlite import ir
import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, c_float #

# debug flags
LEXER_DEBUG: bool = False
PARSER_DEBUG: bool = False
COMPILER_DEBUG: bool = False
RUN_CODE: bool = True

if __name__ == '__main__':
    with open("tests/test_if.obs", "r") as f:
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
        engine.finalize_object()

        entry = engine.get_function_address("main")
        cfunc = CFUNCTYPE(c_int)(entry)

        st = time.time()

        result = cfunc()

        et = time.time()

        print(f"RESULT: {result}")
        print(f"EXECUTION TIME: {et - st} seconds")
