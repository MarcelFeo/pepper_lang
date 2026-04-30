from Lexer import Lexer

code = open('tests/test_postfix.obs','r',encoding='utf-8').read()
lex = Lexer(code)

while True:
    tok = lex.next_token()
    print(tok)
    if tok.type.name == 'EOF':
        break
