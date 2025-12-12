# Arquivo: core/exceptions.py
# Exceções customizadas do sistema de geração de PDF

class ImageSecurityError(Exception):
    """
    Exceção para problemas de segurança com imagens.
    Levantada quando imagens não passam na validação de segurança.
    """
    pass

class ImageProcessingTimeoutError(Exception):
    """
    Exceção para timeout no processamento de imagens.
    Levantada quando o processamento de uma imagem excede o tempo limite.
    """
    pass

class PDFGenerationError(Exception):
    """
    Exceção base para erros na geração de PDF.
    """
    pass

class ContentParsingError(PDFGenerationError):
    """
    Exceção para erros no parsing de conteúdo.
    Levantada quando há problemas na conversão de markdown/HTML.
    """
    pass

class ChartGenerationError(PDFGenerationError):
    """
    Exceção para erros na geração de gráficos.
    Levantada quando há problemas na criação de gráficos matplotlib.
    """
    pass
