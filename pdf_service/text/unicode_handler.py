# Arquivo: text/unicode_handler.py
# Processamento e correção de caracteres especiais Unicode

def corrigir_caracteres_especiais(texto):
    """
    Corrige caracteres especiais que podem não renderizar corretamente em PDFs.
    
    Converte caracteres Unicode problemáticos para equivalentes HTML/texto
    que renderizam corretamente em ReportLab.
    
    Args:
        texto (str): Texto com possíveis caracteres especiais
        
    Returns:
        str: Texto com caracteres corrigidos
    """
    if not texto:
        return texto
    
    # Mapeamento de caracteres problemáticos
    substituicoes = {
        # Sobrescritos negativos
        '⁻¹': '<sup>-1</sup>',
        '⁻²': '<sup>-2</sup>', 
        '⁻³': '<sup>-3</sup>',
        '⁻⁴': '<sup>-4</sup>',
        
        # Sobrescritos positivos
        '¹': '<sup>1</sup>',
        '²': '<sup>2</sup>',
        '³': '<sup>3</sup>',
        '⁴': '<sup>4</sup>',
        
        # Subscritos químicos (conversão para subscript HTML)
        '₀': '<sub>0</sub>',
        '₁': '<sub>1</sub>',
        '₂': '<sub>2</sub>',
        '₃': '<sub>3</sub>',
        '₄': '<sub>4</sub>',
        '₅': '<sub>5</sub>',
        '₆': '<sub>6</sub>',
        '₇': '<sub>7</sub>',
        '₈': '<sub>8</sub>',
        '₉': '<sub>9</sub>',
        
        # Caracteres problemáticos comuns
        '■¹': '<sup>-1</sup>',
        '■²': '<sup>-2</sup>',
        '■³': '<sup>-3</sup>',
        
        # Correção específica para fórmulas químicas corrompidas
        'P■O■': 'P<sub>2</sub>O<sub>5</sub>',
        'K■O': 'K<sub>2</sub>O',
        'N■O■': 'N<sub>2</sub>O<sub>5</sub>',
        'Ca■': 'Ca<sub>2</sub>',
        'Mg■': 'Mg<sub>2</sub>',
        'SO■': 'SO<sub>4</sub>',
        
        '■': '',  # Remove quadrados brancos restantes
        
        # Símbolos matemáticos
        '≈': '~',  # Aproximadamente
        '≤': '<=', # Menor ou igual
        '≥': '>=', # Maior ou igual
        '±': '+/-', # Mais ou menos
        
        # Símbolos de graus e unidades
        '°C': '&deg;C',
        '°F': '&deg;F',
        '°': '&deg;',
        
        # Frações comuns
        '½': '1/2',
        '¼': '1/4',
        '¾': '3/4',
        
        # Símbolos especiais de agricultura
        'µ': 'u',  # Micro
        'α': 'alfa',
        'β': 'beta',
        'γ': 'gama',
    }
    
    for original, substituto in substituicoes.items():
        texto = texto.replace(original, substituto)
    
    return texto

def sanitize_text_for_pdf(texto):
    """
    Sanitiza texto para uso seguro em PDFs.
    
    Remove ou converte caracteres que podem causar problemas
    na renderização de PDFs.
    
    Args:
        texto (str): Texto a ser sanitizado
        
    Returns:
        str: Texto sanitizado
    """
    if not texto:
        return ""
    
    # Aplica correção de caracteres especiais
    texto = corrigir_caracteres_especiais(texto)
    
    # Remove caracteres de controle problemáticos
    import re
    
    # Remove caracteres de controle (exceto \n, \r, \t)
    texto = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', texto)
    
    # Normaliza quebras de linha
    texto = texto.replace('\r\n', '\n').replace('\r', '\n')
    
    return texto
