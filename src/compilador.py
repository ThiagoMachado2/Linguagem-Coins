#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import os
from analisador_lexico import analise_lexica, tabela_simbolos, salvar_html
from analisador_sintatico import Parser
from analisador_semantico import analise_semantica
from gerador_codigo import CodeGenerator

def main():
    """
    Função principal do compilador da Linguagem-Coins
    Executa todas as fases de compilação: léxica, sintática e semântica
    """
    try:
        # Define caminhos relativos para os arquivos
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        codigo_path = os.path.join(project_root, "examples", "codigo.txt")
        output_dir = os.path.join(project_root, "output")
        
        # Cria diretório de saída se não existir
        os.makedirs(output_dir, exist_ok=True)
        
        # Caminhos para arquivos de saída
        errors_log = os.path.join(output_dir, "errors.log")
        semantic_errors_log = os.path.join(output_dir, "semantic_errors.log")
        ast_json = os.path.join(output_dir, "ast.json")
        tabela_simbolos_html = os.path.join(output_dir, "tabela_simbolos.html")
        codigo_gerado_py = os.path.join(output_dir, "codigo_gerado.py")
        
        # Limpa os arquivos de log antes de cada execução
        with open(errors_log, "w", encoding="utf-8") as f:
            f.write("")
        with open(semantic_errors_log, "w", encoding="utf-8") as f:
            f.write("")

        # Lê o código fonte
        with open(codigo_path, "r", encoding="utf-8") as file:
            codigo_fonte = file.read()
            if not codigo_fonte.strip():
                print(f"⚠ O arquivo {codigo_path} está vazio!")
                return
            
            print("=== COMPILADOR LINGUAGEM-COINS ===")
            print(f"Lendo código fonte de: {codigo_path}")
            print("Iniciando análise do código fonte...\n")
            
            # Fase 1: Análise Léxica
            print("=== ANÁLISE LÉXICA ===")
            tokens, erros_lexicos = analise_lexica(codigo_fonte)
            if erros_lexicos:
                print(f"⚠ {len(erros_lexicos)} erros léxicos encontrados.")
                for erro in erros_lexicos:
                    print(f"  - {erro}")
                with open(errors_log, "a", encoding="utf-8") as f:
                    f.write("\n--- Erros Léxicos ---\n")
                    for erro in erros_lexicos:
                        f.write(erro + "\n")
            else:
                print("✅ Nenhum erro léxico encontrado.")
            print(f"✅ {len(tokens)} tokens gerados.")
            
            # Fase 2: Análise Sintática
            print("\n=== ANÁLISE SINTÁTICA ===")
            parser = Parser(tokens)
            ast = parser.parse()
            
            # Salva a AST em JSON
            with open(ast_json, "w", encoding="utf-8") as f:
                json.dump(ast, f, indent=4)
            print(f"✅ AST salva em {ast_json}")
            
            # Verifica erros sintáticos e os escreve no log
            if parser.errors:
                print(f"⚠ {len(parser.errors)} erros sintáticos encontrados. Verifique o arquivo {errors_log} para detalhes.")
                with open(errors_log, "a", encoding="utf-8") as f:
                    f.write("\n--- Erros Sintáticos ---\n")
                    for erro in parser.errors:
                        f.write(erro + "\n")
            else:
                print("✅ Nenhum erro sintático encontrado.")
            
            # Fase 3: Análise Semântica
            print("\n=== ANÁLISE SEMÂNTICA ===")
            resultado, erros, avisos = analise_semantica(ast, semantic_errors_log_path=semantic_errors_log)
            
            if erros:
                print(f"⚠ {len(erros)} erros semânticos encontrados:")
                for erro in erros:
                    print(f"  - {erro}")
            
            if avisos:
                print(f"⚠ {len(avisos)} avisos semânticos encontrados:")
                for aviso in avisos:
                    print(f"  - {aviso}")
            
            if not erros and not avisos:
                print("✅ Nenhum erro ou aviso semântico encontrado.")
            
            # Salva a tabela de símbolos em HTML APÓS a análise semântica
            # para garantir que os tipos e valores estejam atualizados
            salvar_html(tabela_simbolos_html)
            print(f"✅ Tabela de símbolos atualizada salva em {tabela_simbolos_html}")
            
            # Fase 4: Geração de Código (se não houver erros)
            if not parser.errors and not erros and not erros_lexicos:
                print("\n=== GERAÇÃO DE CÓDIGO ===")
                generator = CodeGenerator(ast)
                python_code = generator.generate()
                with open(codigo_gerado_py, "w", encoding="utf-8") as f:
                    f.write(python_code)
                print(f"✅ Código Python gerado e salvo em {codigo_gerado_py}")
            else:
                print("⚠ Geração de código ignorada devido a erros léxicos, sintáticos ou semânticos.")
            
            # Resumo final
            print("\n=== RESUMO DA COMPILAÇÃO ===")
            if not parser.errors and not erros and not erros_lexicos:
                print("✅ Compilação concluída com sucesso!")
            else:
                print(f"⚠ Compilação concluída com {len(erros_lexicos)} erros léxicos, {len(parser.errors)} erros sintáticos e {len(erros)} erros semânticos.")
                print(f"Verifique os arquivos {errors_log} e {semantic_errors_log} para detalhes.")
    
    except FileNotFoundError as e:
        print(f"❌ Arquivo não encontrado: {e}")
    except Exception as e:
        print(f"❌ Erro durante a compilação: {str(e)}")

if __name__ == "__main__":
    main()


