import json
import sys
from analisador_lexico import analise_lexica, tabela_simbolos, salvar_html
from gerador_codigo import CodeGenerator

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.current_token = self.tokens[self.current_token_index] if self.tokens else None
        self.ast = {"type": "Programa", "body": []}
        self.scope_stack = [{}]
        self.current_function_return_type = None # Adicionado para rastrear o tipo de retorno da função atual
        self.errors = [] # Lista para armazenar erros

    def advance(self):
        self.current_token_index += 1
        if self.current_token_index < len(self.tokens):
            self.current_token = self.tokens[self.current_token_index]
        else:
            self.current_token = None

    def match(self, expected_type):
        if self.current_token and self.current_token[0] == expected_type:
            value = self.current_token[1]
            self.advance()
            return value
        else:
            self.error(f"Erro de sintaxe: Esperado {expected_type}, encontrado {self.current_token[0] if self.current_token else 'EOF'}")
            return None # Retorna None para permitir a continuação da análise

    def error(self, message):
        self.errors.append(message)
        with open("errors.log", "a", encoding="utf-8") as f:
            f.write(message + "\n")
        print(message, file=sys.stderr) # Imprime o erro no stderr

    def enter_scope(self):
        self.scope_stack.append({})

    def exit_scope(self):
        self.scope_stack.pop()

    def declare_variable(self, name, var_type):
        current_scope = self.scope_stack[-1]
        if name in current_scope:
            self.error(f"Erro semântico: Variável '{name}' já declarada neste escopo.")
        current_scope[name] = {"type": var_type, "kind": "variable"}
        tabela_simbolos[name] = {"tipo": var_type, "valor": ""}

    def declare_subroutine(self, name, sub_type, params, return_type=None):
        current_scope = self.scope_stack[-1]
        if name in current_scope:
            self.error(f"Erro semântico: {sub_type} '{name}' já declarada neste escopo.")
        current_scope[name] = {"type": sub_type, "kind": sub_type, "params": params, "return_type": return_type}
        tabela_simbolos[name] = {"tipo": sub_type, "valor": "", "params": params, "return_type": return_type}

    def get_symbol_info(self, name):
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        self.error(f"Erro semântico: Símbolo '{name}' não declarado.")
        return None # Retorna None para evitar erro em cascata

    def get_variable_type(self, name):
        symbol_info = self.get_symbol_info(name)
        if symbol_info and symbol_info["kind"] != "variable":
            self.error(f"Erro semântico: '{name}' não é uma variável.")
            return "unknown" # Retorna tipo desconhecido
        return symbol_info["type"] if symbol_info else "unknown"

    def check_type_compatibility(self, expected_type, actual_type, operation="atribuição"):
        if expected_type == "inteiro" and actual_type == "real":
            self.errors.append(f"Aviso semântico: Conversão implícita de real para inteiro em {operation}. Pode haver perda de dados.")
            return True
        elif expected_type == "real" and actual_type == "inteiro":
            return True
        elif expected_type == actual_type:
            return True
        else:
            self.error(f"Erro semântico: Incompatibilidade de tipos em {operation}. Esperado {expected_type}, encontrado {actual_type}.")
            return False

    def parse(self):
        self.programa()
        return self.ast

    def programa(self):
        while self.current_token:
            if self.current_token and self.current_token[0] == "TIPO":
                self.declaracoes()
            elif self.current_token and (self.current_token[0] == "PROCEDIMENTO" or self.current_token[0] == "FUNCAO"):
                self.subroutine_declaration()
            else:
                break
        self.comandos()

    def declaracoes(self):
        node = {"type": "Declaracao", "declarations": []}
        var_type = self.match("TIPO")
        if var_type is None: return # Adicionado para lidar com erros de match
        while True:
            var_name = self.match("ID")
            if var_name is None: break # Adicionado para lidar com erros de match
            self.declare_variable(var_name, var_type)
            node["declarations"].append({"name": var_name, "type": var_type})
            if self.current_token and self.current_token[0] == "VIRGULA":
                self.match("VIRGULA")
            else:
                break
        self.match("PONTO_VIRGULA")
        self.ast["body"].append(node)

    def comandos(self):
        while self.current_token and self.current_token[0] in ["ID", "SE", "ENQUANTO", "PROCEDIMENTO", "FUNCAO", "RETORNA"]:
            if self.current_token[0] == "ID":
                self.atribuicao()
            elif self.current_token[0] == "SE" or self.current_token[0] == "ENQUANTO":
                self.estrutura_controle()
            elif self.current_token and self.current_token[0] in ["PROCEDIMENTO", "FUNCAO"]:
                self.chamada_subrotina()
            elif self.current_token[0] == "RETORNA":
                self.retorno()

    def subroutine_declaration(self):
        node = {"type": "SubroutineDeclaration"}
        sub_type = self.match(self.current_token[0]) # PROCEDIMENTO ou FUNCAO
        if sub_type is None: return
        
        name = self.match("ID")
        if name is None: return
        node["name"] = name
        
        params = self.parse_parameters()
        if params is None: return
        node["parameters"] = params

        return_type = None
        if sub_type == "FUNCAO":
            if self.match("RETORNA") is None: return
            return_type = self.match("TIPO")
            if return_type is None: return
            node["return_type"] = return_type
        
        self.declare_subroutine(name, sub_type, params, return_type)

        if self.match("ABRE_CHAVE") is None: return
        self.enter_scope()
        # Set current function return type for return statement validation
        if sub_type == "FUNCAO":
            self.current_function_return_type = return_type

        node["body"] = []
        original_body = self.ast["body"]
        self.ast["body"] = node["body"]
        self.comandos()
        self.ast["body"] = original_body
        self.exit_scope()
        # Reset current function return type
        if sub_type == "FUNCAO":
            self.current_function_return_type = None

        if self.match("FECHA_CHAVE") is None: return
        self.ast["body"].append(node)

    def parse_parameters(self):
        params = []
        if self.match("ABRE_PAREN") is None: return None
        if self.current_token and self.current_token[0] == "TIPO":
            while True:
                param_type = self.match("TIPO")
                if param_type is None: return None
                param_name = self.match("ID")
                if param_name is None: return None
                params.append({"name": param_name, "type": param_type})
                self.declare_variable(param_name, param_type) # Declare parameters in the new scope
                if self.current_token and self.current_token[0] == "VIRGULA":
                    if self.match("VIRGULA") is None: return None
                else:
                    break
        if self.match("FECHA_PAREN") is None: return None
        return params

    def atribuicao(self):
        node = {"type": "Atribuicao"}
        var_name = self.match("ID")
        if var_name is None: return
        node["variable"] = var_name
        expected_type = self.get_variable_type(var_name)
        if expected_type == "unknown": return # Adicionado para lidar com erros de variável não declarada
        if self.match("IGUAL") is None: return
        value_node = self.expressao()
        if value_node is None: return
        actual_type = self.get_expression_type(value_node)
        self.check_type_compatibility(expected_type, actual_type)
        node["value"] = value_node
        if self.match("PONTO_VIRGULA") is None: return
        self.ast["body"].append(node)

    def estrutura_controle(self):
        if self.current_token and self.current_token[0] == "SE":
            self.condicional()
        elif self.current_token and self.current_token[0] == "ENQUANTO":
            self.repeticao()
        else:
            self.error("Erro de sintaxe: Esperado 'se' ou 'enquanto'")

    def condicional(self):
        node = {"type": "Condicional"}
        if self.match("SE") is None: return
        if self.match("ABRE_PAREN") is None: return
        condition_node = self.expressao()
        if condition_node is None: return
        condition_type = self.get_expression_type(condition_node)
        if condition_type not in ["inteiro", "real", "boolean"] and not (condition_node["type"] == "BinaryExpression" and condition_node["operator"] in ["==", "!=", ">", "<", ">=", "<=", "&&", "||", "!"]):
             self.errors.append(f"Aviso semântico: Condição de tipo inesperado: {condition_type}. Esperado tipo booleano ou numérico.")
             print(f"Aviso semântico: Condição de tipo inesperado: {condition_type}. Esperado tipo booleano ou numérico.", file=sys.stderr)
        node["condition"] = condition_node
        if self.match("FECHA_PAREN") is None: return
        if self.match("ABRE_CHAVE") is None: return
        self.enter_scope()
        node["consequent"] = []
        original_body = self.ast["body"]
        self.ast["body"] = node["consequent"]
        self.comandos()
        self.ast["body"] = original_body
        self.exit_scope()
        if self.match("FECHA_CHAVE") is None: return
        if self.current_token and self.current_token[0] == "SENAO":
            if self.match("SENAO") is None: return
            if self.match("ABRE_CHAVE") is None: return
            self.enter_scope()
            node["alternate"] = []
            original_body = self.ast["body"]
            self.ast["body"] = node["alternate"]
            self.comandos()
            self.ast["body"] = original_body
            self.exit_scope()
            if self.match("FECHA_CHAVE") is None: return
        self.ast["body"].append(node)

    def repeticao(self):
        node = {"type": "Repeticao"}
        if self.match("ENQUANTO") is None: return
        if self.match("ABRE_PAREN") is None: return
        condition_node = self.expressao()
        if condition_node is None: return
        condition_type = self.get_expression_type(condition_node)
        if condition_type not in ["inteiro", "real", "boolean"] and not (condition_node["type"] == "BinaryExpression" and condition_node["operator"] in ["==", "!=", ">", "<", ">=", "<=", "&&", "||", "!"]):
             self.errors.append(f"Aviso semântico: Condição de tipo inesperado: {condition_type}. Esperado tipo booleano ou numérico.")
             print(f"Aviso semântico: Condição de tipo inesperado: {condition_type}. Esperado tipo booleano ou numérico.", file=sys.stderr)
        node["condition"] = condition_node
        if self.match("FECHA_PAREN") is None: return
        if self.match("ABRE_CHAVE") is None: return
        self.enter_scope()
        node["body"] = []
        original_body = self.ast["body"]
        self.ast["body"] = node["body"]
        self.comandos()
        self.ast["body"] = original_body
        self.exit_scope()
        if self.match("FECHA_CHAVE") is None: return
        self.ast["body"].append(node)

    def expressao(self):
        node = self.termo()
        if node is None: return None
        while self.current_token and self.current_token[0] in ["OP_ARIT", "OP_LOGICO", "OP_COMP"]:
            operator = self.match(self.current_token[0])
            if operator is None: return None
            right = self.termo()
            if right is None: return None
            left_type = self.get_expression_type(node)
            right_type = self.get_expression_type(right)
            result_type = self.infer_type(left_type, right_type, operator)
            node = {"type": "BinaryExpression", "operator": operator, "left": node, "right": right, "_type": result_type}
        return node

    def termo(self):
        node = self.fator()
        if node is None: return None
        while self.current_token and self.current_token[0] in ["OP_ARIT", "OP_LOGICO", "OP_COMP"]:
            operator = self.match(self.current_token[0])
            if operator is None: return None
            right = self.fator()
            if right is None: return None
            left_type = self.get_expression_type(node)
            right_type = self.get_expression_type(right)
            result_type = self.infer_type(left_type, right_type, operator)
            node = {"type": "BinaryExpression", "operator": operator, "left": node, "right": right, "_type": result_type}
        return node

    def fator(self):
        if self.current_token and self.current_token[0] == "NUMERO":
            value = self.match("NUMERO")
            if value is None: return None
            if "." in value:
                return {"type": "Literal", "value": value, "_type": "real"}
            else:
                return {"type": "Literal", "value": value, "_type": "inteiro"}
        elif self.current_token and self.current_token[0] == "ID":
            value = self.match("ID")
            if value is None: return None
            var_type = self.get_variable_type(value)
            return {"type": "Identifier", "name": value, "_type": var_type}
        elif self.current_token and self.current_token[0] == "STRING":
            value = self.match("STRING")
            if value is None: return None
            return {"type": "Literal", "value": value, "_type": "texto"}
        elif self.current_token and self.current_token[0] == "ABRE_PAREN":
            if self.match("ABRE_PAREN") is None: return None
            node = self.expressao()
            if node is None: return None
            if self.match("FECHA_PAREN") is None: return None
            return node
        else:
            self.error(f"Erro de sintaxe: Esperado NUMERO, ID, STRING ou ABRE_PAREN, encontrado {self.current_token[0] if self.current_token else 'EOF'}")
            return None

    def get_expression_type(self, node):
        if node is None: return "unknown"
        if "_type" in node:
            return node["_type"]
        elif node["type"] == "Identifier":
            return self.get_variable_type(node["name"])
        elif node["type"] == "Literal":
            if isinstance(node["value"], str) and node["value"].startswith("\""):
                return "texto"
            elif "." in str(node["value"]):
                return "real"
            else:
                return "inteiro"
        elif node["type"] == "BinaryExpression":
            left_type = self.get_expression_type(node["left"])
            right_type = self.get_expression_type(node["right"])
            return self.infer_type(left_type, right_type, node["operator"])
        elif node["type"] == "ChamadaSubrotina":
            subroutine_info = self.get_symbol_info(node["name"])
            if subroutine_info and subroutine_info["kind"] == "FUNCAO":
                return subroutine_info["return_type"]
            else:
                return "void" # Procedures return void
        return "unknown"

    def infer_type(self, type1, type2, operator):
        if operator in ["+", "-", "*", "/"]:
            if type1 == "texto" or type2 == "texto":
                self.error(f"Erro semântico: Operação aritmética com tipo texto não permitida: {type1} {operator} {type2}")
                return "unknown"
            if type1 == "real" or type2 == "real":
                return "real"
            return "inteiro"
        elif operator in ["==", "!=", ">", "<", ">=", "<="]:
            if type1 in ["inteiro", "real"] and type2 in ["inteiro", "real"]:
                return "boolean"
            elif type1 == "texto" and type2 == "texto":
                return "boolean"
            else:
                self.error(f"Erro semântico: Operação de comparação inválida entre {type1} e {type2}")
                return "unknown"
        elif operator in ["&&", "||"]:
            if type1 == "boolean" and type2 == "boolean":
                return "boolean"
            else:
                self.error(f"Erro semântico: Operação lógica inválida entre {type1} e {type2}")
                return "unknown"
        elif operator == "!":
            if type1 == "boolean":
                return "boolean"
            else:
                self.error(f"Erro semântico: Operador lógico '!' inválido para o tipo {type1}")
                return "unknown"
        return "unknown"

    def chamada_subrotina(self):
        node = {"type": "ChamadaSubrotina"}
        sub_type = self.match(self.current_token[0]) # PROCEDIMENTO ou FUNCAO
        if sub_type is None: return
        
        name = self.match("ID")
        if name is None: return
        node["name"] = name

        subroutine_info = self.get_symbol_info(name)
        if subroutine_info is None: return
        if subroutine_info["kind"] not in ["PROCEDIMENTO", "FUNCAO"]:
            self.error(f"Erro semântico: '{name}' não é um procedimento ou função.")
            return

        if self.match("ABRE_PAREN") is None: return
        args = []
        if self.current_token and self.current_token[0] != "FECHA_PAREN":
            while True:
                arg_node = self.expressao()
                if arg_node is None: return
                args.append(arg_node)
                if self.current_token and self.current_token[0] == "VIRGULA":
                    if self.match("VIRGULA") is None: return
                else:
                    break
        if self.match("FECHA_PAREN") is None: return
        node["arguments"] = args

        # Semantic check for argument count and types
        if len(args) != len(subroutine_info["params"]):
            self.error(f"Erro semântico: Número incorreto de argumentos para '{name}'. Esperado {len(subroutine_info['params'])}, encontrado {len(args)}.")
        else:
            for i, param in enumerate(subroutine_info["params"]):
                arg_type = self.get_expression_type(args[i])
                self.check_type_compatibility(param["type"], arg_type, f"chamada de '{name}' para o parâmetro '{param['name']}'")

        if self.match("PONTO_VIRGULA") is None: return
        self.ast["body"].append(node)

    def retorno(self):
        node = {"type": "Retorno"}
        if self.match("RETORNA") is None: return
        
        if self.current_function_return_type is None:
            self.error("Erro semântico: 'retorna' fora de uma função.")
            return

        if self.current_token and self.current_token[0] != "PONTO_VIRGULA":
            value_node = self.expressao()
            if value_node is None: return
            actual_type = self.get_expression_type(value_node)
            self.check_type_compatibility(self.current_function_return_type, actual_type, "retorno de função")
            node["value"] = value_node
        elif self.current_function_return_type != "void": # Assuming 'void' for procedures or functions with no explicit return type
            self.error(f"Erro semântico: Função com tipo de retorno '{self.current_function_return_type}' espera um valor de retorno.")

        if self.match("PONTO_VIRGULA") is None: return
        self.ast["body"].append(node)


if __name__ == "__main__":
    try:
        # Limpa o arquivo de erros antes de cada execução
        with open("errors.log", "w", encoding="utf-8") as f:
            f.write("")

        with open("codigo.txt", "r", encoding="utf-8") as file:
            codigo_fonte = file.read()
            if not codigo_fonte.strip():
                print("⚠ O arquivo codigo.txt está vazio!")
            else:
                tokens = analise_lexica(codigo_fonte)
                print("Tokens gerados:")
                for token in tokens:
                    print(token)
                
                parser = Parser(tokens)
                ast = parser.parse()
                
                with open("ast.json", "w", encoding="utf-8") as f:
                    json.dump(ast, f, indent=4)
                print("AST salva em ast.json!")

                generator = CodeGenerator(ast)
                python_code = generator.generate()
                with open("codigo_gerado.py", "w", encoding="utf-8") as f:
                    f.write(python_code)
                print("Código Python gerado e salvo em codigo_gerado.py!")

                salvar_html()

                if not parser.errors:
                    print("✅ Análise concluída com sucesso, nenhum erro encontrado.")
                else:
                    print(f"❌ Análise concluída com {len(parser.errors)} erros. Verifique o arquivo errors.log para detalhes.")

    except FileNotFoundError:
        print("❌ Arquivo codigo.txt não encontrado!")


