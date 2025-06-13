import json
import sys
import os

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.current_token = self.tokens[self.current_token_index] if self.tokens else None
        self.ast = {"type": "Programa", "body": []}
        self.errors = []

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
            return None

    def error(self, message):
        self.errors.append(message)

    def parse(self):
        self.programa()
        return self.ast

    def programa(self):
        while self.current_token and self.current_token[0] != "EOF":
            initial_token_index = self.current_token_index
            
            if self.current_token[0] == "TIPO":
                self.declaracoes()
            elif self.current_token[0] in ["PROCEDIMENTO", "FUNCAO"]:
                self.subroutine_declaration()
            elif self.current_token[0] == "SE" or self.current_token[0] == "ENQUANTO":
                self.estrutura_controle()
            elif self.current_token[0] == "RETORNA":
                self.retorno()
            elif self.current_token[0] == "ID":
                next_token_index = self.current_token_index + 1
                if next_token_index < len(self.tokens) and self.tokens[next_token_index][0] == "IGUAL":
                    self.atribuicao()
                elif next_token_index < len(self.tokens) and self.tokens[next_token_index][0] == "ABRE_PAREN":
                    self.chamada_subrotina()
                else:
                    self.error(f"Erro de sintaxe: Comando inesperado após ID '{self.current_token[1]}' ({self.current_token[0]}). Esperado '=' ou '(' para atribuição/chamada.")
                    self.advance() # Avança para tentar recuperar
                    self.synchronize()
            elif self.current_token[0] == "COMENTARIO":
                self.ast["body"].append({"type": "Comentario", "value": self.current_token[1], "kind": self.current_token[2]})
                self.advance()
            else:
                self.error(f"Erro de sintaxe: Token inesperado '{self.current_token[1]}' ({self.current_token[0]}) no início de uma declaração ou comando. Tentando recuperar...")
                self.advance() # Avança para evitar loop infinito
                self.synchronize()
            
            # Prevent infinite loop if no tokens are consumed
            if self.current_token_index == initial_token_index and self.current_token is not None:
                self.advance()
                self.synchronize()

    def comandos(self):
        while self.current_token and self.current_token[0] not in ["FECHA_CHAVE", "EOF"]:
            initial_token_index = self.current_token_index
            
            if self.current_token[0] == "TIPO":
                self.declaracoes()
            elif self.current_token[0] in ["PROCEDIMENTO", "FUNCAO"]:
                self.subroutine_declaration()
            elif self.current_token[0] == "SE" or self.current_token[0] == "ENQUANTO":
                self.estrutura_controle()
            elif self.current_token[0] == "RETORNA":
                self.retorno()
            elif self.current_token[0] == "ID":
                next_token_index = self.current_token_index + 1
                if next_token_index < len(self.tokens) and self.tokens[next_token_index][0] == "IGUAL":
                    self.atribuicao()
                elif next_token_index < len(self.tokens) and self.tokens[next_token_index][0] == "ABRE_PAREN":
                    self.chamada_subrotina()
                else:
                    self.error(f"Erro de sintaxe: Comando inesperado após ID '{self.current_token[1]}' ({self.current_token[0]}). Esperado '=' ou '(' para atribuição/chamada.")
                    self.advance() # Avança para tentar recuperar
                    self.synchronize()
            elif self.current_token[0] == "COMENTARIO":
                self.ast["body"].append({"type": "Comentario", "value": self.current_token[1], "kind": self.current_token[2]})
                self.advance()
            else:
                self.error(f"Erro de sintaxe: Token inesperado '{self.current_token[1]}' ({self.current_token[0]}) dentro de um bloco de comandos. Tentando recuperar...")
                self.advance() # Avança para evitar loop infinito
                self.synchronize()
            
            # Prevent infinite loop if no tokens are consumed
            if self.current_token_index == initial_token_index and self.current_token is not None:
                self.advance()
                self.synchronize()

    def synchronize(self):
        sync_tokens = [
            "PONTO_VIRGULA", "ABRE_CHAVE", "FECHA_CHAVE", 
            "TIPO", "PROCEDIMENTO", "FUNCAO", "SE", "ENQUANTO", "RETORNA",
            "EOF" 
        ]
        while self.current_token and self.current_token[0] not in sync_tokens:
            self.advance()
        if self.current_token and self.current_token[0] == "PONTO_VIRGULA":
            self.advance()

    def declaracoes(self):
        node = {"type": "Declaracao", "declarations": []}
        var_type = self.match("TIPO")
        if var_type is None: 
            self.synchronize()
            return
        while True:
            var_name = self.match("ID")
            if var_name is None: 
                self.synchronize()
                return 
            node["declarations"].append({"name": var_name, "type": var_type})
            if self.current_token and self.current_token[0] == "VIRGULA":
                self.match("VIRGULA")
            else:
                break
        if self.match("PONTO_VIRGULA") is None: 
            self.synchronize()
            return
        self.ast["body"].append(node)

    def subroutine_declaration(self):
        node = {"type": "SubroutineDeclaration"}
        sub_type_token = self.current_token[0]
        sub_type = self.match(sub_type_token)
        if sub_type is None: 
            self.synchronize()
            return
        node["kind"] = sub_type
        
        name = self.match("ID")
        if name is None: 
            self.synchronize()
            return
        node["name"] = name
        
        params = self.parse_parameters()
        if params is None: 
            self.synchronize()
            return
        node["parameters"] = params

        return_type = None
        if sub_type == "FUNCAO":
            if self.match("RETORNA") is None: 
                self.synchronize()
                return
            return_type = self.match("TIPO")
            if return_type is None: 
                self.synchronize()
                return
            node["return_type"] = return_type
        
        if self.match("ABRE_CHAVE") is None: 
            self.synchronize()
            return

        node["body"] = []
        original_body = self.ast["body"]
        self.ast["body"] = node["body"]
        self.comandos()
        self.ast["body"] = original_body

        if sub_type == "FUNCAO":
            pass

        if self.match("FECHA_CHAVE") is None: 
            self.synchronize()
            return
        self.ast["body"].append(node) # Adicionado esta linha para incluir a sub-rotina na AST principal

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
                if self.current_token and self.current_token[0] == "VIRGULA":
                    if self.match("VIRGULA") is None: return None
                else:
                    break
        if self.match("FECHA_PAREN") is None: return None
        return params

    def atribuicao(self):
        node = {"type": "Atribuicao"}
        var_name = self.match("ID")
        if var_name is None: 
            self.synchronize()
            return
        node["variable"] = var_name
        if self.match("IGUAL") is None: 
            self.synchronize()
            return
        value_node = self.expressao()
        if value_node is None: 
            self.synchronize()
            return
        node["value"] = value_node
        if self.match("PONTO_VIRGULA") is None: 
            self.synchronize()
            return
        self.ast["body"].append(node)

    def estrutura_controle(self):
        if self.current_token and self.current_token[0] == "SE":
            self.condicional()
        elif self.current_token and self.current_token[0] == "ENQUANTO":
            self.repeticao()
        else:
            self.error("Erro de sintaxe: Esperado 'se' ou 'enquanto'")
            self.synchronize()

    def condicional(self):
        node = {"type": "Condicional"}
        if self.match("SE") is None: 
            self.synchronize()
            return
        if self.match("ABRE_PAREN") is None: 
            self.synchronize()
            return
        condition_node = self.expressao()
        if condition_node is None: 
            self.synchronize()
            return
        node["condition"] = condition_node
        if self.match("FECHA_PAREN") is None: 
            self.synchronize()
            return
        if self.match("ABRE_CHAVE") is None: 
            self.synchronize()
            return
        node["consequent"] = []
        original_body = self.ast["body"]
        self.ast["body"] = node["consequent"]
        self.comandos()
        self.ast["body"] = original_body
        if self.match("FECHA_CHAVE") is None: 
            self.synchronize()
            return
        if self.current_token and self.current_token[0] == "SENAO":
            if self.match("SENAO") is None: 
                self.synchronize()
                return
            if self.match("ABRE_CHAVE") is None: 
                self.synchronize()
                return
            node["alternate"] = []
            original_body = self.ast["body"]
            self.ast["body"] = node["alternate"]
            self.comandos()
            self.ast["body"] = original_body
            if self.match("FECHA_CHAVE") is None: 
                self.synchronize()
                return
        self.ast["body"].append(node)

    def repeticao(self):
        node = {"type": "Repeticao"}
        if self.match("ENQUANTO") is None: 
            self.synchronize()
            return
        if self.match("ABRE_PAREN") is None: 
            self.synchronize()
            return
        condition_node = self.expressao()
        if condition_node is None: 
            self.synchronize()
            return
        node["condition"] = condition_node
        if self.match("FECHA_PAREN") is None: 
            self.synchronize()
            return
        if self.match("ABRE_CHAVE") is None: 
            self.synchronize()
            return
        node["body"] = []
        original_body = self.ast["body"]
        self.ast["body"] = node["body"]
        self.comandos()
        self.ast["body"] = original_body
        if self.match("FECHA_CHAVE") is None: 
            self.synchronize()
            return
        self.ast["body"].append(node)

    def expressao(self):
        return self.logica_ou()

    def logica_ou(self):
        node = self.logica_e()
        while self.current_token and self.current_token[1] == "||":
            operator = self.match("OP_LOGICO")
            if operator is None: return None
            right = self.logica_e()
            if right is None: return None
            node = {"type": "BinaryExpression", "operator": operator, "left": node, "right": right}
        return node

    def logica_e(self):
        node = self.comparacao()
        while self.current_token and self.current_token[1] == "&&":
            operator = self.match("OP_LOGICO")
            if operator is None: return None
            right = self.comparacao()
            if right is None: return None
            node = {"type": "BinaryExpression", "operator": operator, "left": node, "right": right}
        return node

    def comparacao(self):
        node = self.aritmetica()
        while self.current_token and self.current_token[0] == "OP_COMP":
            operator = self.match("OP_COMP")
            if operator is None: return None
            right = self.aritmetica()
            if right is None: return None
            node = {"type": "BinaryExpression", "operator": operator, "left": node, "right": right}
        return node

    def aritmetica(self):
        node = self.termo()
        while self.current_token and self.current_token[1] in ["+", "-"]:
            operator = self.match("OP_ARIT")
            if operator is None: return None
            right = self.termo()
            if right is None: return None
            node = {"type": "BinaryExpression", "operator": operator, "left": node, "right": right}
        return node

    def termo(self):
        node = self.fator()
        while self.current_token and self.current_token[1] in ["*", "/", "%"]:
            operator = self.match("OP_ARIT")
            if operator is None: return None
            right = self.fator()
            if right is None: return None
            node = {"type": "BinaryExpression", "operator": operator, "left": node, "right": right}
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
            name = self.current_token[1]
            self.advance() # Advance for ID
            if self.current_token and self.current_token[0] == "ABRE_PAREN":
                return self.chamada_subrotina_expressao(name)
            else:
                return {"type": "Identifier", "name": name}
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
        elif self.current_token and self.current_token[0] == "OP_LOGICO" and self.current_token[1] == "!":
            operator = self.match("OP_LOGICO")
            if operator is None: return None
            operand = self.fator()
            if operand is None: return None
            return {"type": "UnaryExpression", "operator": operator, "operand": operand}
        else:
            self.error(f"Erro de sintaxe: Esperado NUMERO, ID, STRING, ABRE_PAREN ou '!', encontrado {self.current_token[0] if self.current_token else 'EOF'}")
            self.advance() # Advance on unexpected token
            return None

    def chamada_subrotina(self):
        node = {"type": "ChamadaSubrotina"}
        name = self.match("ID")
        if name is None: 
            self.synchronize()
            return
        node["name"] = name
        
        args = self.parse_arguments()
        if args is None: 
            self.synchronize()
            return
        
        node["arguments"] = args
        
        if self.match("PONTO_VIRGULA") is None: 
            self.synchronize()
            return
        self.ast["body"].append(node)

    def chamada_subrotina_expressao(self, name):
        node = {"type": "ChamadaSubrotina"}
        node["name"] = name
        
        args = self.parse_arguments()
        if args is None: return None
        node["arguments"] = args
        
        return node

    def parse_arguments(self):
        args = []
        if self.match("ABRE_PAREN") is None: return None
        if self.current_token and self.current_token[0] != "FECHA_PAREN":
            while True:
                arg_node = self.expressao()
                if arg_node is None: return None
                args.append(arg_node)
                if self.current_token and self.current_token[0] == "VIRGULA":
                    if self.match("VIRGULA") is None: return None
                else:
                    break
        if self.match("FECHA_PAREN") is None: return None
        return args

    def retorno(self):
        node = {"type": "Retorno"}
        if self.match("RETORNA") is None: 
            self.synchronize()
            return
        if self.current_token and self.current_token[0] != "PONTO_VIRGULA":
            value_node = self.expressao()
            if value_node is None: 
                self.synchronize()
                return
            node["value"] = value_node
        
        if self.match("PONTO_VIRGULA") is None: 
            self.synchronize()
            return
        self.ast["body"].append(node)


