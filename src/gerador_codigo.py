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
        # Declarações em Python não precisam de tipo explícito
        # Apenas inicializamos as variáveis para garantir que existam
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
        return f"({left} {operator} {right})"

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

    def visit_ChamadaSubrotina(self, node):
        func_name = node["name"]
        args = ", ".join([self.visit_expression(arg) for arg in node["arguments"]])
        self.code.append(f"{self.indent()}{func_name}({args})")

    def visit_expression(self, node):
        if node["type"] == "BinaryExpression":
            return self.visit_BinaryExpression(node)
        elif node["type"] == "Literal":
            return self.visit_Literal(node)
        elif node["type"] == "Identifier":
            return self.visit_Identifier(node)
        else:
            self.error("Tipo de expressão desconhecido: " + node["type"])



