class CodeGenerator:
    def __init__(self, ast):
        self.ast = ast
        self.code = []
        self.indent_level = 0

    def generate(self):
        self.visit(self.ast)
        return "\n".join(self.code)

    def indent(self):
        return "    " * self.indent_level

    def visit(self, node):
        method_name = "visit_" + node["type"]
        visitor = getattr(self, method_name, self.generic_visit)
        visitor(node)

    def generic_visit(self, node):
        raise Exception("Nenhum método visit_" + node["type"] + " implementado.")

    def visit_Programa(self, node):
        for child_node in node["body"]:
            self.visit(child_node)

    def visit_Declaracao(self, node):
        for declaration in node["declarations"]:
            var_name = declaration["name"]
            var_type = declaration["type"]
            if var_type == "inteiro":
                self.code.append(f"{self.indent()}{var_name} = 0")
            elif var_type == "real":
                self.code.append(f"{self.indent()}{var_name} = 0.0")
            elif var_type == "texto":
                self.code.append(f"{self.indent()}{var_name} = \"\"")

    def visit_Atribuicao(self, node):
        var_name = node["variable"]
        value = self.visit_expression(node["value"])
        self.code.append(f"{self.indent()}{var_name} = {value}")

    def visit_BinaryExpression(self, node):
        left = self.visit_expression(node["left"])
        right = self.visit_expression(node["right"])
        operator = node["operator"]
        # Mapear operadores lógicos da linguagem Coins para Python
        if operator == "&&":
            operator = "and"
        elif operator == "||":
            operator = "or"
        return f"({left} {operator} {right})"

    def visit_UnaryExpression(self, node):
        operand = self.visit_expression(node["operand"])
        operator = node["operator"]
        # Mapear operadores lógicos da linguagem Coins para Python
        if operator == "!":
            operator = "not"
        return f"({operator} {operand})"

    def visit_Literal(self, node):
        if node["_type"] == "texto":
            return f"\"" + node["value"].replace("\"", "") + f"\"" # Remove aspas extras se já houver
        return str(node["value"])

    def visit_Identifier(self, node):
        return node["name"]

    def visit_Condicional(self, node):
        condition = self.visit_expression(node["condition"])
        self.code.append(f"{self.indent()}if {condition}:")
        self.indent_level += 1
        for consequent_node in node["consequent"]:
            self.visit(consequent_node)
        self.indent_level -= 1
        if "alternate" in node:
            self.code.append(f"{self.indent()}else:")
            self.indent_level += 1
            for alternate_node in node["alternate"]:
                self.visit(alternate_node)
            self.indent_level -= 1

    def visit_Repeticao(self, node):
        condition = self.visit_expression(node["condition"])
        self.code.append(f"{self.indent()}while {condition}:")
        self.indent_level += 1
        for body_node in node["body"]:
            self.visit(body_node)
        self.indent_level -= 1

    def visit_SubroutineDeclaration(self, node):
        sub_kind = node["kind"]
        name = node["name"]
        params = ", ".join([f"{p['name']}" for p in node["parameters"]])
        
        if sub_kind == "PROCEDIMENTO":
            self.code.append(f"\ndef {name}({params}):")
        elif sub_kind == "FUNCAO":
            self.code.append(f"\ndef {name}({params}):")
        
        self.indent_level += 1
        for body_node in node["body"]:
            self.visit(body_node)
        self.indent_level -= 1
        # Adicionar um \'pass\' se o corpo estiver vazio para evitar erro de sintaxe em Python
        if not node["body"]:
            self.code.append(f"{self.indent()}pass")

    def visit_ChamadaSubrotina(self, node):
        func_name = node["name"]
        args = ", ".join([self.visit_expression(arg) for arg in node["arguments"]])
        self.code.append(f"{self.indent()}{func_name}({args})")

    def visit_Retorno(self, node):
        if "value" in node:
            value = self.visit_expression(node["value"])
            self.code.append(f"{self.indent()}return {value}")
        else:
            self.code.append(f"{self.indent()}return")

    def visit_Comentario(self, node):
        # Adiciona o comentário como um comentário Python
        comment_text = node["value"]
        if node["kind"] == "COMENTARIO_LINHA":
            self.code.append(f"{self.indent()}# {comment_text.strip().lstrip('//').strip()}")
        elif node["kind"] == "COMENTARIO_BLOCO":
            # Para comentários de bloco, pode-se usar strings de múltiplas linhas em Python
            # Ou converter para múltiplas linhas de comentários de linha
            lines = comment_text.strip().lstrip('/*').rstrip('*/').strip().split('\n')
            for line in lines:
                self.code.append(f"{self.indent()}# {line.strip()}")

    def visit_expression(self, node):
        if node["type"] == "BinaryExpression":
            return self.visit_BinaryExpression(node)
        elif node["type"] == "UnaryExpression":
            return self.visit_UnaryExpression(node)
        elif node["type"] == "Literal":
            return self.visit_Literal(node)
        elif node["type"] == "Identifier":
            return self.visit_Identifier(node)
        elif node["type"] == "ChamadaSubrotina":
            # Chamadas de subrotina como parte de uma expressão (ex: em atribuição)
            func_name = node["name"]
            args = ", ".join([self.visit_expression(arg) for arg in node["arguments"]])
            return f"{func_name}({args})"
        else:
            raise Exception("Tipo de expressão desconhecido: " + node["type"])


