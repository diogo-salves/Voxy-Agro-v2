# Arquivo: text/html_cleaner.py
# Limpeza e sanitização de HTML malformado

import re
import logging

def limpar_html_malformado(texto):
    """
    Limpa e corrige HTML malformado para uso em PDFs.
    
    Corrige problemas comuns como:
    - Tags não fechadas
    - Tags duplicadas
    - Tags <para> desnecessárias
    - Caracteres especiais não escapados
    
    Args:
        texto (str): Texto HTML possivelmente malformado
        
    Returns:
        str: HTML limpo e corrigido
    """
    if not texto:
        return ""
    
    # Remove tags <para> desnecessárias
    texto = re.sub(r'</?para>', '', texto)
    
    # Corrige tags <b> malformadas
    texto = re.sub(r'<b>(?!.*</b>.*$)', '<b>', texto)
    texto = re.sub(r'<b>([^<]*)<b>', r'<b>\1</b>', texto)
    texto = re.sub(r'<b>([^<]*)$', r'<b>\1</b>', texto)
    
    # Corrige outras tags malformadas
    texto = re.sub(r'<i>(?!.*</i>)', '<i>', texto)
    texto = re.sub(r'<i>([^<]*)<i>', r'<i>\1</i>', texto)
    texto = re.sub(r'<u>(?!.*</u>)', '<u>', texto)
    texto = re.sub(r'<u>([^<]*)<u>', r'<u>\1</u>', texto)
    
    # Escapa caracteres especiais (&), mas preserva tags HTML válidas
    texto = texto.replace('&', '&amp;')
    # Não escapa < e > pois já temos HTML válido
    
    # Remove tags <b> não fechadas no final
    if texto.endswith('<b>'):
        texto = texto[:-3]
    
    return texto

def limpeza_agressiva_html(texto):
    """
    Realiza limpeza agressiva de HTML quando a limpeza normal falha.
    
    Remove todas as tags HTML quando detecta problemas irrecuperáveis.
    
    Args:
        texto (str): Texto HTML problemático
        
    Returns:
        str: Texto limpo (possivelmente sem HTML)
    """
    if not texto:
        return ""
    
    # Remove tags <para> desnecessárias
    texto = re.sub(r'</?para>', '', texto)
    
    # Remove tags <b> malformadas no final
    texto = re.sub(r'<b>([^<]*)$', r'\1', texto)
    
    # Remove tags vazias
    texto = re.sub(r'<b>\s*</b>', '', texto)
    
    # Se ainda há tags <b> não fechadas, remove todas as tags
    if '<b>' in texto and '</b>' not in texto:
        logging.warning("HTML irrecuperável detectado, removendo todas as tags")
        texto = re.sub(r'<[^>]+>', '', texto)
    
    return texto

def sanitize_html_for_reportlab(texto):
    """
    Sanitiza HTML especificamente para uso com ReportLab.
    
    ReportLab tem limitações específicas de HTML que precisam ser respeitadas.
    
    Args:
        texto (str): Texto HTML
        
    Returns:
        str: HTML compatível com ReportLab
    """
    if not texto:
        return ""
    
    # Primeiro, aplica limpeza padrão
    texto = limpar_html_malformado(texto)
    
    # Tags suportadas pelo ReportLab: b, i, u, br, sup, sub
    # Remove tags não suportadas mas preserva o conteúdo
    tags_nao_suportadas = ['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'em']
    
    for tag in tags_nao_suportadas:
        # Remove tags de abertura e fechamento, mas preserva conteúdo
        texto = re.sub(f'<{tag}[^>]*>', '', texto, flags=re.IGNORECASE)
        texto = re.sub(f'</{tag}>', '', texto, flags=re.IGNORECASE)
    
    # Converte tags similares para suportadas
    texto = re.sub(r'<strong>', '<b>', texto, flags=re.IGNORECASE)
    texto = re.sub(r'</strong>', '</b>', texto, flags=re.IGNORECASE)
    texto = re.sub(r'<em>', '<i>', texto, flags=re.IGNORECASE)
    texto = re.sub(r'</em>', '</i>', texto, flags=re.IGNORECASE)
    
    return texto

def validate_html_structure(texto):
    """
    Valida se a estrutura HTML está correta.
    
    Args:
        texto (str): Texto HTML
        
    Returns:
        tuple: (is_valid: bool, errors: list)
    """
    if not texto:
        return True, []
    
    errors = []
    
    # Verifica tags não fechadas
    tags_abertas = re.findall(r'<(\w+)[^>]*>', texto)
    tags_fechadas = re.findall(r'</(\w+)>', texto)
    
    for tag in tags_abertas:
        if tag.lower() not in ['br']:  # br é self-closing
            if tags_abertas.count(tag) > tags_fechadas.count(tag):
                errors.append(f"Tag <{tag}> não fechada")
    
    # Verifica caracteres não escapados
    if '&' in texto and not ('&amp;' in texto or '&lt;' in texto or '&gt;' in texto):
        unescaped_amps = re.findall(r'&(?!amp;|lt;|gt;|deg;|sup;)', texto)
        if unescaped_amps:
            errors.append("Caracteres & não escapados encontrados")
    
    return len(errors) == 0, errors
