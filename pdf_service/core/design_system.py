"""
Voxy Agro v2.0 - Design System
Sistema de design unificado para geração de PDFs profissionais
"""

# ===============================
# ESCALA TIPOGRÁFICA
# ===============================

# Escala tipográfica harmônica (1.125 - Major Third)
FONT_SCALE = {
    'xs': 9,
    'sm': 10,
    'base': 11,
    'lg': 12,
    'xl': 14,
    '2xl': 16,
    '3xl': 18,
    '4xl': 22
}

# ===============================
# ESCALA DE ESPAÇAMENTO
# ===============================

# Escala de espaçamento (base 6pt)
SPACING = {
    'xs': 6,
    'sm': 9,
    'md': 12,
    'lg': 18,
    'xl': 24,
    '2xl': 36
}

# ===============================
# CORES PARA GRÁFICOS
# ===============================

# Escala de cinzas para gráficos monocromáticos
GRAY_SCALE = ['#2D2D2D', '#4A4A4A', '#6B6B6B', '#8C8C8C', '#ADADAD', '#C4C4C4', '#DBDBDB']

# Cores para gráficos coloridos (fallback)
CHART_COLORS = ['#4299E1', '#48BB78', '#F6AD55', '#9F7AEA', '#F56565', '#38B2AC', '#ED64A6']

# ===============================
# CONFIGURAÇÕES DE IMAGEM
# ===============================

# Tamanhos de imagem (em polegadas)
IMAGE_SIZES = {
    'landscape': {'width': 5.5, 'height': 3.5},  # horizontal
    'portrait': {'width': 3.5, 'height': 5.0},   # vertical
    'square': {'width': 4.0, 'height': 4.0}      # quadrada
}

# ===============================
# RODAPÉ VOXY
# ===============================

# Texto padrão do rodapé Voxy
VOXY_FOOTER_TEXT = "Documento feito com ajuda do Voxy Agro"

# Estilo do rodapé Voxy
VOXY_FOOTER_STYLE = {
    'fontSize': 7,
    'color': '#999999',
    'alignment': 'CENTER'
}
