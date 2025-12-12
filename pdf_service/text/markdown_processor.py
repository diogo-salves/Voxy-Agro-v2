# Arquivo: text/markdown_processor.py
# Conversão de Markdown para HTML compatível com ReportLab

import re
from .unicode_handler import corrigir_caracteres_especiais

def converter_markdown_para_html(texto):
    """
    Converte texto Markdown para HTML compatível com ReportLab.
    
    Suporta:
    - Títulos hierárquicos: 1), 1.1), 1.1.1)
    - Cabeçalhos Markdown: # ## ###
    - Listas numeradas: 1. 2. 3.
    - Texto em negrito: **texto**
    - Texto em itálico: *texto*
    - Separadores horizontais: ---
    - Listas com marcadores: - ou •
    
    Args:
        texto (str): Texto em formato Markdown
        
    Returns:
        str: HTML compatível com ReportLab
    """
    if not texto:
        return ""
    
    # Primeiro, corrige caracteres especiais
    texto = corrigir_caracteres_especiais(texto)
    
    linhas = texto.split('\n')
    linhas_processadas = []
    
    for linha in linhas:
        linha_limpa = linha.strip()
        
        # Separadores horizontais: ---
        if re.match(r'^-{3,}$', linha_limpa):
            linhas_processadas.append('[SEPARADOR_HORIZONTAL]')
            continue
        
        # Títulos hierárquicos: 1), 1.1), 1.1.1) etc
        match_titulo = re.match(r'^(\d+(?:\.\d+)*)\)\s+(.+)', linha_limpa)
        if match_titulo:
            numeracao = match_titulo.group(1)
            conteudo = match_titulo.group(2)
            nivel = numeracao.count('.') + 1
            linhas_processadas.append(f"[TITULO_NIVEL_{nivel}]{numeracao}) {conteudo}[/TITULO_NIVEL_{nivel}]")
            continue
        
        # Listas numeradas: 1., 2., 3. etc (apenas números simples)
        match_lista = re.match(r'^(\d+)\.\s+(.+)', linha_limpa)
        if match_lista:
            numero = match_lista.group(1)
            conteudo = match_lista.group(2)
            linhas_processadas.append(f"[ITEM_LISTA]{numero}. {conteudo}[/ITEM_LISTA]")
            continue
            
        # Cabeçalhos Markdown: # Título, ## Título
        elif re.match(r'^(#{1,6})\s+', linha_limpa):
            match = re.match(r'^(#{1,6})\s+(.+)', linha_limpa)
            nivel = len(match.group(1))
            conteudo = match.group(2)
            linhas_processadas.append(f"[TITULO_NIVEL_{nivel}]{conteudo}[/TITULO_NIVEL_{nivel}]")
        else:
            linhas_processadas.append(linha)

    texto_processado = '\n'.join(linhas_processadas)
    
    # Converte formatação inline
    texto_processado = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto_processado)  # Negrito
    texto_processado = re.sub(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)', r'<i>\1</i>', texto_processado)  # Itálico
    
    # Converte quebras de linha
    texto_processado = texto_processado.replace('\n', '<br/>')
    
    # Normaliza listas com marcadores
    texto_processado = re.sub(r'(<br/>\s*)+[-•]\s+', '<br/>• ', texto_processado)
    
    # Corrige início de lista
    if texto_processado.strip().startswith('- ') or texto_processado.strip().startswith('• '):
        texto_processado = '• ' + texto_processado.strip()[2:]
    
    return texto_processado

def extract_markdown_titles(texto):
    """
    Extrai todos os títulos de um texto Markdown.
    
    Args:
        texto (str): Texto Markdown
        
    Returns:
        list: Lista de tuplas (nivel, titulo)
    """
    if not texto:
        return []
    
    titulos = []
    linhas = texto.split('\n')
    
    for linha in linhas:
        linha_limpa = linha.strip()
        
        # Títulos hierárquicos: 1), 1.1), 1.1.1)
        match_titulo = re.match(r'^(\d+(?:\.\d+)*)\)\s+(.+)', linha_limpa)
        if match_titulo:
            numeracao = match_titulo.group(1)
            conteudo = match_titulo.group(2)
            nivel = numeracao.count('.') + 1
            titulos.append((nivel, f"{numeracao}) {conteudo}"))
            continue
        
        # Cabeçalhos Markdown: # ## ###
        match_markdown = re.match(r'^(#{1,6})\s+(.+)', linha_limpa)
        if match_markdown:
            nivel = len(match_markdown.group(1))
            conteudo = match_markdown.group(2)
            titulos.append((nivel, conteudo))
    
    return titulos

def markdown_to_plain_text(texto):
    """
    Converte Markdown para texto simples, removendo formatação.
    
    Args:
        texto (str): Texto Markdown
        
    Returns:
        str: Texto simples sem formatação
    """
    if not texto:
        return ""
    
    # Remove cabeçalhos Markdown
    texto = re.sub(r'^#{1,6}\s+(.+)', r'\1', texto, flags=re.MULTILINE)
    
    # Remove títulos hierárquicos
    texto = re.sub(r'^(\d+(?:\.\d+)*)\)\s+(.+)', r'\2', texto, flags=re.MULTILINE)
    
    # Remove formatação inline
    texto = re.sub(r'\*\*(.*?)\*\*', r'\1', texto)  # Negrito
    texto = re.sub(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)', r'\1', texto)  # Itálico
    
    # Remove separadores
    texto = re.sub(r'^-{3,}$', '', texto, flags=re.MULTILINE)
    
    # Normaliza espaçamento
    texto = re.sub(r'\n\s*\n', '\n\n', texto)  # Remove linhas vazias extras
    texto = texto.strip()
    
    return texto

def validate_markdown_syntax(texto):
    """
    Valida a sintaxe Markdown básica.
    
    Args:
        texto (str): Texto Markdown
        
    Returns:
        tuple: (is_valid: bool, errors: list)
    """
    if not texto:
        return True, []
    
    errors = []
    
    # Verifica formatação inline não fechada
    bold_count = len(re.findall(r'\*\*', texto))
    if bold_count % 2 != 0:
        errors.append("Formatação **negrito** não fechada")
    
    # Verifica itálico não fechado (mais complexo por causa do negrito)
    # Remove primeiro todo o negrito para verificar itálico
    texto_sem_bold = re.sub(r'\*\*(.*?)\*\*', r'\1', texto)
    italic_count = len(re.findall(r'(?<!\*)\*(?!\*)', texto_sem_bold))
    if italic_count % 2 != 0:
        errors.append("Formatação *itálico* não fechada")
    
    return len(errors) == 0, errors
