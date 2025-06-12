import re
import html
import os


token_specs = [
    ("COMENTARIO", r"//.*|/\*[\s\S]*?\*/"), # Changed to consume till end of line for // and non-greedy for /* */
    ("SKIP", r"[ \t\n]+"), # Moved to top for higher precedence
    ("TIPO", r"\b(inteiro|real|texto)\b"),
    ("SE", r"\bse\b"),
    ("SENAO", r"\bsenao\b"),
    ("ENQUANTO", r"\benquanto\b"),
    ("PROCEDIMENTO", r"\bprocedimento\b"),
    ("FUNCAO", r"\bfuncao\b"),
    ("RETORNA", r"\bretorna\b"),
    ("ID", r"\b[a-zA-Z_\u00C0-\u017F][a-zA-Z0-9_\u00C0-\u017F]*\b"),
    ("NUMERO", r"\b[0-9]+(?:\.[0-9]+)?\b"),
    ("STRING", r"\"[^\"]*\""),
    ("OP_ARIT", r"[+\-*/%]"),
    ("OP_LOGICO", r"(&&|\|\||!)"),
    ("OP_COMP", r"(==|!=|>=|<=|>|<)"),
    ("IGUAL", r"="),
    ("PONTO_VIRGULA", r";"),
    ("VIRGULA", r","),
    ("ABRE_PAREN", r"\("),
    ("FECHA_PAREN", r"\)"),
    ("ABRE_CHAVE", r"\{"),
    ("FECHA_CHAVE", r"\}"),

    ("MISMATCH", r"."),
]

tok_regex = "|".join(f"(?P<{name}>{regex})" for name, regex in token_specs)

tabela_simbolos = {}

def analise_lexica(codigo):
    tokens_gerados = []
    for match in re.finditer(tok_regex, codigo):
        tipo = match.lastgroup
        valor = match.group(tipo)

        if tipo == "SKIP" or tipo == "COMENTARIO":
            continue
        elif tipo == "MISMATCH":
            tokens_gerados.append(("ERRO_LEXICO", valor))
        else:
            tokens_gerados.append((tipo, valor))
            if tipo == "ID" and valor not in tabela_simbolos:
                tabela_simbolos[valor] = {"tipo": "indefinido", "valor": ""}
    return tokens_gerados

def salvar_html(caminho_arquivo=None):
    """
    Salva a tabela de símbolos em um arquivo HTML
    
    Args:
        caminho_arquivo: Caminho completo para o arquivo de saída. Se None, usa "tabela_simbolos.html" no diretório atual.
    """
    if caminho_arquivo is None:
        caminho_arquivo = "tabela_simbolos.html"
    
    # Garante que o diretório de saída existe
    os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
    
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write("<html><head><meta charset=\'UTF-8\'><title>Tabela de Símbolos</title></head><body>\n")
        f.write("<h2>Tabela de Símbolos</h2>\n")
        f.write("<table border=\'1\'><tr><th>Identificador</th><th>Tipo</th><th>Valor</th></tr>\n")
        for nome, info in tabela_simbolos.items():
            f.write(f"<tr><td>{html.escape(nome)}</td><td>{info['tipo']}</td><td>{html.escape(str(info['valor']))}</td></tr>\n")
        f.write("</table></body></html>\n")
    print(f"Tabela salva em {caminho_arquivo}!")

if __name__ == "__main__":
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        codigo_path = os.path.join(project_root, "examples", "codigo.txt")
        
        with open(codigo_path, "r", encoding="utf-8") as file:
            codigo_fonte = file.read()
            if not codigo_fonte.strip():
                print(f"⚠ O arquivo {codigo_path} está vazio!")
            else:
                tokens = analise_lexica(codigo_fonte)
                print("Tokens gerados:")
                for token in tokens:
                    print(token)
                
                output_dir = os.path.join(project_root, "output")
                os.makedirs(output_dir, exist_ok=True)
                tabela_path = os.path.join(output_dir, "tabela_simbolos.html")
                salvar_html(tabela_path)
    except FileNotFoundError as e:
        print(f"❌ Arquivo não encontrado: {e}")
