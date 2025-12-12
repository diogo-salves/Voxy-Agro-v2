# Arquivo: utils/fonts.py
# Gerenciamento de fontes Unicode para PDFs

import logging
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def registrar_fontes_unicode():
    """
    Registra fontes com suporte Unicode completo.
    
    Tenta registrar fontes na seguinte ordem de preferência:
    1. DejaVu Sans (melhor suporte Unicode)
    2. Liberation Sans (fallback)
    3. Helvetica (fallback padrão)
    
    Returns:
        str: Nome da fonte registrada com sucesso
    """
    try:
        from reportlab.pdfbase.pdfmetrics import registerFontFamily
        
        # Tenta registrar DejaVu Sans (melhor suporte Unicode)
        try:
            pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
            registerFontFamily('DejaVuSans', normal='DejaVuSans', bold='DejaVuSans-Bold')
            return 'DejaVuSans'
        except:
            pass
            
        # Fallback para Liberation Sans
        try:
            pdfmetrics.registerFont(TTFont('LiberationSans', 'LiberationSans-Regular.ttf'))
            pdfmetrics.registerFont(TTFont('LiberationSans-Bold', 'LiberationSans-Bold.ttf'))
            registerFontFamily('LiberationSans', normal='LiberationSans', bold='LiberationSans-Bold')
            return 'LiberationSans'
        except:
            pass
            
    except Exception as e:
        logging.warning(f"Não foi possível registrar fontes Unicode: {e}")
    
    return 'Helvetica'  # Fallback padrão

def get_font_bold_variant(font_name: str) -> str:
    """
    Retorna o nome da variante bold de uma fonte.
    
    Args:
        font_name: Nome da fonte base
        
    Returns:
        str: Nome da fonte bold correspondente
    """
    if font_name == 'Helvetica':
        return 'Helvetica-Bold'
    else:
        return f'{font_name}-Bold'
