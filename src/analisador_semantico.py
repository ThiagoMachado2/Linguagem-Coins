import sys
import os
from analisador_lexico import tabela_simbolos

class AnalisadorSemantico:
    def __init__(self, errors_log_path=None, semantic_errors_log_path=None):
        self.errors = []
        self.warnings = []
        self.scope_stack = [{}]  # Pilha de escopos para controle de variáveis
        self.current_function = None  # Função atual sendo analisada
        self.current_function_return_type = None  # Tipo de retorno da função atual
        self.has_return = False  # Indica se a função atual tem retorno
        self.errors_log_path = errors_log_path or "errors.log"
        self.semantic_errors_log_path = semantic_errors_log_path or "semantic_errors.log"
        
        # Garante que os diretórios de saída existem (apenas se o caminho tiver um diretório)
        self._ensure_directory_exists(self.errors_log_path)
        self._ensure_directory_exists(self.semantic_errors_log_path)

    def _ensure_directory_exists(self, file_path):
        """Cria o diretório para um arquivo se necessário e se o diretório não for vazio"""
        directory = os.path.dirname(file_path)
        if directory:  # Verifica se o diretório não é vazio
            os.makedirs(directory, exist_ok=True)

    def error(self, message):
        """Registra um erro semântico"""
        self.errors.append(message)
        with open(self.errors_log_path, "a", encoding="utf-8") as f:
            f.write(f"ERRO SEMÂNTICO: {message}\n")
        print(f"ERRO SEMÂNTICO: {message}", file=sys.stderr)

    def warning(self, message):
        """Registra um aviso semântico"""
        self.warnings.append(message)
        with open(self.errors_log_path, "a", encoding="utf-8") as f:
            f.write(f"AVISO SEMÂNTICO: {message}\n")
        print(f"AVISO SEMÂNTICO: {message}", file=sys.stderr)

    def enter_scope(self):
        """Entra em um novo escopo"""
        self.scope_stack.append({})

    def exit_scope(self):
        """Sai do escopo atual"""
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()

    def declare_variable(self, name, var_type):
        """Declara uma variável no escopo atual"""
        current_scope = self.scope_stack[-1]
        if name in current_scope:
            self.error(f"Variável '{name}' já declarada neste escopo.")
            return False
        current_scope[name] = {"type": var_type, "kind": "variable"}
        
        # Atualiza a tabela de símbolos com o tipo correto
        tabela_simbolos[name] = {"tipo": var_type, "valor": ""}
        return True

    def update_variable_value(self, name, value):
        """Atualiza o valor de uma variável na tabela de símbolos"""
        if name in tabela_simbolos:
            # Converte o valor para string para exibição na tabela
            if isinstance(value, dict) and "value" in value:
                valor_str = str(value["value"])
            else:
                valor_str = str(value)
            
            tabela_simbolos[name]["valor"] = valor_str

    def declare_subroutine(self, name, sub_type, params, return_type=None):
        """Declara uma subrotina (procedimento ou função) no escopo atual"""
        current_scope = self.scope_stack[-1]
        if name in current_scope:
            self.error(f"{sub_type.capitalize()} '{name}' já declarado neste escopo.")
            return False
        current_scope[name] = {
            "type": sub_type, 
            "kind": sub_type, 
            "params": params, 
            "return_type": return_type
        }
        
        # Atualiza a tabela de símbolos com informações da subrotina
        params_info = [f"{p['name']}: {p['type']}" for p in params]
        params_str = ", ".join(params_info)
        valor_str = f"{sub_type}({params_str})"
        if return_type:
            valor_str += f" -> {return_type}"
            
        tabela_simbolos[name] = {
            "tipo": sub_type, 
            "valor": valor_str
        }
        return True

    def get_symbol_info(self, name):
        """Busca informações de um símbolo em todos os escopos"""
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        self.error(f"Símbolo '{name}' não declarado.")
        return None

    def get_variable_type(self, name):
        """Obtém o tipo de uma variável"""
        symbol_info = self.get_symbol_info(name)
        if symbol_info is None:
            return "unknown"
        if symbol_info["kind"] != "variable":
            self.error(f"'{name}' não é uma variável.")
            return "unknown"
        return symbol_info["type"]

    def check_type_compatibility(self, expected_type, actual_type, operation="atribuição"):
        """Verifica compatibilidade entre tipos"""
        if expected_type == "unknown" or actual_type == "unknown":
            return False
        
        if expected_type == actual_type:
            return True
        
        if expected_type == "real" and actual_type == "inteiro":
            return True
        
        if expected_type == "inteiro" and actual_type == "real":
            self.warning(f"Conversão implícita de real para inteiro em {operation}. Pode haver perda de dados.")
            return True
        
        self.error(f"Incompatibilidade de tipos em {operation}. Esperado {expected_type}, encontrado {actual_type}.")
        return False

    def infer_type(self, type1, type2, operator):
        """Infere o tipo resultante de uma operação binária"""
        if operator in ["+", "-", "*", "/", "%"]:
            if type1 == "texto" or type2 == "texto":
                self.error(f"Operação aritmética com tipo texto não permitida: {type1} {operator} {type2}")
                return "unknown"
            if type1 == "real" or type2 == "real":
                return "real"
            return "inteiro"
        
        elif operator in ["==", "!=", ">", "<", ">=", "<="]:
            if type1 in ["inteiro", "real"] and type2 in ["inteiro", "real"]:
                return "boolean"
            elif type1 == "texto" and type2 == "texto":
                if operator in [">", "<", ">=", "<="]:
                    self.warning(f"Comparação de ordem ({operator}) entre strings pode ter comportamento inesperado.")
                return "boolean"
            else:
                self.error(f"Operação de comparação inválida entre {type1} e {type2}")
                return "unknown"
        
        elif operator in ["&&", "||"]:
            if type1 == "boolean" and type2 == "boolean":
                return "boolean"
            else:
                self.error(f"Operação lógica inválida entre {type1} e {type2}")
                return "unknown"
        
        elif operator == "!":
            if type1 == "boolean":
                return "boolean"
            else:
                self.error(f"Operador lógico '!' inválido para o tipo {type1}")
                return "unknown"
        
        return "unknown"

    def analyze_ast(self, ast):
        """Analisa a AST completa"""
        if ast["type"] != "Programa":
            self.error("AST inválida: nó raiz deve ser do tipo 'Programa'")
            return False
        
        for node in ast["body"]:
            self.analyze_node(node)
        
        return len(self.errors) == 0

    def analyze_node(self, node):
        """Analisa um nó da AST"""
        if node is None:
            return
        
        node_type = node.get("type")
        
        if node_type == "Declaracao":
            self.analyze_declaration(node)
        elif node_type == "Atribuicao":
            self.analyze_assignment(node)
        elif node_type == "Condicional":
            self.analyze_conditional(node)
        elif node_type == "Repeticao":
            self.analyze_loop(node)
        elif node_type == "SubroutineDeclaration":
            self.analyze_subroutine_declaration(node)
        elif node_type == "ChamadaSubrotina":
            self.analyze_subroutine_call(node)
        elif node_type == "Retorno":
            self.analyze_return(node)
        elif node_type == "BinaryExpression":
            return self.analyze_binary_expression(node)
        elif node_type == "UnaryExpression": # Adicionado para tratar expressões unárias
            return self.analyze_unary_expression(node)
        elif node_type == "Identifier":
            return self.analyze_identifier(node)
        elif node_type == "Literal":
            return self.analyze_literal(node)
        elif node_type == "Comentario": # Comentários não precisam de análise semântica, mas são nós na AST
            pass

    def analyze_declaration(self, node):
        """Analisa declarações de variáveis"""
        for decl in node.get("declarations", []):
            self.declare_variable(decl["name"], decl["type"])

    def analyze_assignment(self, node):
        """Analisa atribuições"""
        var_name = node["variable"]
        var_type = self.get_variable_type(var_name)
        
        value = node["value"]
        value_type = self.analyze_expression(value)
        
        if self.check_type_compatibility(var_type, value_type):
            # Atualiza o valor na tabela de símbolos
            self.update_variable_value(var_name, value)

    def analyze_conditional(self, node):
        """Analisa estruturas condicionais"""
        condition_type = self.analyze_expression(node["condition"])
        
        if condition_type not in ["inteiro", "real", "boolean"]:
            self.error(f"Condição de tipo inesperado: {condition_type}. Esperado tipo booleano ou numérico.")
        
        self.enter_scope()
        for stmt in node.get("consequent", []):
            self.analyze_node(stmt)
        self.exit_scope()
        
        if "alternate" in node:
            self.enter_scope()
            for stmt in node["alternate"]:
                self.analyze_node(stmt)
            self.exit_scope()

    def analyze_loop(self, node):
        """Analisa estruturas de repetição"""
        condition_type = self.analyze_expression(node["condition"])
        
        if condition_type not in ["inteiro", "real", "boolean"]:
            self.error(f"Condição de tipo inesperado: {condition_type}. Esperado tipo booleano ou numérico.")
        
        self.enter_scope()
        for stmt in node.get("body", []):
            self.analyze_node(stmt)
        self.exit_scope()

    def analyze_subroutine_declaration(self, node):
        """Analisa declarações de subrotinas (procedimentos e funções)"""
        name = node["name"]
        sub_type = node["kind"] # Usar 'kind' do nó da AST
        params = node.get("parameters", [])
        return_type = node.get("return_type")
        
        # Registra a função atual para verificação de retorno
        old_function = self.current_function
        old_return_type = self.current_function_return_type
        old_has_return = self.has_return
        
        self.current_function = name
        self.current_function_return_type = return_type
        self.has_return = False
        
        # Declara a subrotina no escopo atual
        self.declare_subroutine(name, sub_type, params, return_type)
        
        # Entra em um novo escopo para os parâmetros e corpo
        self.enter_scope()
        
        # Declara os parâmetros no novo escopo
        for param in params:
            self.declare_variable(param["name"], param["type"])
        
        # Analisa o corpo da subrotina
        for stmt in node.get("body", []):
            self.analyze_node(stmt)
        
        # Verifica se funções têm retorno
        if sub_type == "FUNCAO" and not self.has_return and return_type is not None:
            self.error(f"Função '{name}' com tipo de retorno '{return_type}' não tem instrução de retorno.")
        
        # Restaura o contexto anterior
        self.current_function = old_function
        self.current_function_return_type = old_return_type
        self.has_return = old_has_return
        
        # Sai do escopo da subrotina
        self.exit_scope()

    def analyze_subroutine_call(self, node):
        """Analisa chamadas de subrotinas"""
        name = node["name"]
        args = node.get("arguments", [])
        
        # Busca informações da subrotina
        subroutine_info = self.get_symbol_info(name)
        if subroutine_info is None:
            return "unknown"
        
        # Verifica se é realmente uma subrotina
        if subroutine_info["kind"] not in ["PROCEDIMENTO", "FUNCAO"]:
            self.error(f"'{name}' não é um procedimento ou função.")
            return "unknown"
        
        # Verifica número de argumentos
        params = subroutine_info.get("params", [])
        if len(args) != len(params):
            self.error(f"Número incorreto de argumentos para '{name}'. Esperado {len(params)}, encontrado {len(args)}.")
        
        # Verifica tipos dos argumentos
        for i, (arg, param) in enumerate(zip(args, params)):
            arg_type = self.analyze_expression(arg)
            param_type = param["type"]
            self.check_type_compatibility(param_type, arg_type, f"argumento {i+1} de '{name}'")
        
        # Retorna o tipo de retorno para funções
        if subroutine_info["kind"] == "FUNCAO":
            return subroutine_info.get("return_type", "unknown")
        return "void"

    def analyze_return(self, node):
        """Analisa instruções de retorno"""
        # Verifica se está dentro de uma função
        if self.current_function is None:
            self.error("Instrução 'retorna' fora de uma função.")
            return
        
        # Marca que a função tem retorno
        self.has_return = True
        
        # Verifica o tipo do valor retornado
        if "value" in node:
            value_type = self.analyze_expression(node["value"])
            if self.current_function_return_type is None:
                self.error(f"Função '{self.current_function}' não deveria retornar valor.")
            else:
                self.check_type_compatibility(
                    self.current_function_return_type, 
                    value_type, 
                    f"retorno de '{self.current_function}'"
                )
        elif self.current_function_return_type is not None:
            self.error(f"Função '{self.current_function}' com tipo de retorno '{self.current_function_return_type}' espera um valor de retorno.")

    def analyze_binary_expression(self, node):
        """Analisa expressões binárias"""
        left_type = self.analyze_expression(node["left"])
        right_type = self.analyze_expression(node["right"])
        return self.infer_type(left_type, right_type, node["operator"])

    def analyze_unary_expression(self, node):
        """Analisa expressões unárias (ex: !booleano)"""
        operand_type = self.analyze_expression(node["operand"])
        return self.infer_type(operand_type, None, node["operator"])

    def analyze_identifier(self, node):
        """Analisa identificadores"""
        return self.get_variable_type(node["name"])

    def analyze_literal(self, node):
        """Analisa literais"""
        value = node["value"]
        if isinstance(value, str) and value.startswith('"'):
            return "texto"
        elif "." in str(value):
            return "real"
        else:
            return "inteiro"

    def analyze_expression(self, node):
        """Analisa expressões genéricas"""
        if node is None:
            return "unknown"
        
        node_type = node.get("type")
        
        if "_type" in node:
            return node["_type"]
        elif node_type == "BinaryExpression":
            return self.analyze_binary_expression(node)
        elif node_type == "UnaryExpression":
            return self.analyze_unary_expression(node)
        elif node_type == "Identifier":
            return self.analyze_identifier(node)
        elif node_type == "Literal":
            return self.analyze_literal(node)
        elif node_type == "ChamadaSubrotina":
            return self.analyze_subroutine_call(node)
        
        return "unknown"

# Função para executar a análise semântica
def analise_semantica(ast, semantic_errors_log_path=None):
    """Executa a análise semântica na AST fornecida"""
    # Define o caminho do arquivo de log
    if semantic_errors_log_path is None:
        semantic_errors_log_path = "semantic_errors.log"
    
    # Garante que o diretório de saída existe (apenas se o caminho tiver um diretório)
    directory = os.path.dirname(semantic_errors_log_path)
    if directory:  # Verifica se o diretório não é vazio
        os.makedirs(directory, exist_ok=True)

    # Limpa o arquivo de log semântico antes de cada execução
    with open(semantic_errors_log_path, "w", encoding="utf-8") as f:
        f.write("")

    analisador = AnalisadorSemantico(semantic_errors_log_path=semantic_errors_log_path)
    analisador.analyze_ast(ast)
    return True, analisador.errors, analisador.warnings


