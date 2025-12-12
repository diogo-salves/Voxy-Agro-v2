# Arquivo: core/config.py
# Configurações centralizadas e constantes do sistema

# ===============================
# CONSTANTES DE SEGURANÇA CRÍTICAS
# ===============================

# Limites de segurança para imagens
MAX_IMAGE_SIZE_MB = 5  # Máximo 5MB por imagem
MAX_IMAGE_COUNT = 20   # Máximo 20 imagens por documento
MAX_DECODE_SIZE_MB = 50  # Máximo 50MB total de dados decodificados
IMAGE_PROCESSING_TIMEOUT = 30  # Timeout de 30 segundos por imagem

# Formatos de imagem permitidos (magic bytes)
ALLOWED_IMAGE_FORMATS = {
    b'\x89PNG\r\n\x1a\n': 'PNG',
    b'\xff\xd8\xff': 'JPEG',
    b'GIF87a': 'GIF',
    b'GIF89a': 'GIF'
}

# Dimensões máximas permitidas
MAX_IMAGE_WIDTH = 4000   # pixels
MAX_IMAGE_HEIGHT = 4000  # pixels

# ===============================
# PALETAS DE CORES PROFISSIONAIS
# ===============================

COLOR_PALETTES = {
    'azul_escuro': {
        'principal': '#1A365D',
        'secundaria': '#2D3748',
        'destaque': '#4299E1',
        'fundo': '#F7FAFC',
        'zebra': '#EBF4FF',  # Azul bem claro (10% da cor principal)
        'escala': ['#1A365D', '#2C5282', '#2B6CB0', '#3182CE', '#4299E1', '#63B3ED', '#90CDF4']
    },
    'verde_agronegocio': {
        'principal': '#1B4332',
        'secundaria': '#2D5E3E',
        'destaque': '#40916C',
        'fundo': '#F1F8E9',
        'zebra': '#E8F5E9',  # Verde bem claro
        'escala': ['#1B4332', '#2D5E3E', '#40916C', '#52B788', '#74C69D', '#95D5B2', '#B7E4C7']
    },
    'laranja_comercial': {
        'principal': '#C05621',
        'secundaria': '#9C4221',
        'destaque': '#F6AD55',
        'fundo': '#FFFAF0',
        'zebra': '#FFF3E0',  # Laranja bem claro
        'escala': ['#9C4221', '#C05621', '#DD6B20', '#ED8936', '#F6AD55', '#FBD38D', '#FEEBC8']
    },
    'roxo_corporativo': {
        'principal': '#44337A',
        'secundaria': '#553C9A',
        'destaque': '#9F7AEA',
        'fundo': '#FAF5FF',
        'zebra': '#F3E8FF',  # Roxo bem claro
        'escala': ['#44337A', '#553C9A', '#6B46C1', '#7C3AED', '#9F7AEA', '#B794F4', '#D6BCFA']
    },
    'preto_e_branco': {
        'principal': '#1A1A1A',
        'secundaria': '#4A4A4A',
        'destaque': '#6B6B6B',
        'fundo': '#FAFAFA',
        'zebra': '#F5F5F5',  # Cinza bem claro
        'escala': ['#1A1A1A', '#3D3D3D', '#5F5F5F', '#828282', '#A5A5A5', '#C8C8C8', '#E0E0E0']
    }
}

# Paleta padrão
DEFAULT_COLOR_PALETTE = 'preto_e_branco'

# ===============================
# CONFIGURAÇÕES DE PDF
# ===============================

# Margens padrão (em pontos)
DEFAULT_MARGINS = 72

# Campos que devem ser ignorados no processamento de conteúdo
IGNORED_CONTENT_FIELDS = [
    'tipo_documento', 'titulo_documento', 'tecnico_nome', 
    'paleta_cores', 'cliente', 'propriedade', 
    'data_documento', 'imagens_anexadas'
]

# Ordem preferida para processamento de campos de conteúdo
CONTENT_FIELD_ORDER = [
    'conteudo_principal', 'recomendacoes', 'conclusoes'
]

# ===============================
# FUNÇÕES UTILITÁRIAS DE CONFIGURAÇÃO
# ===============================

def get_color_palette(palette_name: str) -> dict:
    """
    Retorna a paleta de cores especificada ou a padrão se não encontrar.
    
    Args:
        palette_name: Nome da paleta desejada
        
    Returns:
        dict: Dicionário com as cores da paleta
    """
    return COLOR_PALETTES.get(palette_name, COLOR_PALETTES[DEFAULT_COLOR_PALETTE])

def validate_palette_name(palette_name: str) -> str:
    """
    Valida e normaliza o nome da paleta.
    
    Args:
        palette_name: Nome da paleta a ser validado
        
    Returns:
        str: Nome da paleta normalizado ou padrão se inválido
    """
    if not palette_name:
        return DEFAULT_COLOR_PALETTE
    
    # Mapeamento de aliases específicos (ex: para compatibilidade com entrada do Gemini)
    aliases = {
        "preto_branco": "preto_e_branco"
    }
    
    # Tenta usar o alias, caso contrário usa o nome original
    normalized_name = aliases.get(palette_name, palette_name)
    
    # Verifica se o nome normalizado existe nas paletas disponíveis
    if normalized_name in COLOR_PALETTES:
        return normalized_name
    
    return DEFAULT_COLOR_PALETTE

def get_available_palettes() -> list:
    """
    Retorna lista de paletas disponíveis.
    
    Returns:
        list: Lista com nomes das paletas disponíveis
    """
    return list(COLOR_PALETTES.keys())
