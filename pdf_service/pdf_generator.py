import io
import base64
import re
import logging
from datetime import datetime
import os
import time
import threading
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, Frame, PageTemplate, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfWriter, PdfReader

# Imports dos novos módulos refatorados
from .core.config import (
    MAX_IMAGE_SIZE_MB, MAX_IMAGE_COUNT, MAX_DECODE_SIZE_MB, IMAGE_PROCESSING_TIMEOUT,
    ALLOWED_IMAGE_FORMATS, MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT,
    COLOR_PALETTES, get_color_palette, IGNORED_CONTENT_FIELDS, CONTENT_FIELD_ORDER
)
from .core.exceptions import ImageSecurityError, ImageProcessingTimeoutError
from .utils.fonts import registrar_fontes_unicode
from .text.unicode_handler import corrigir_caracteres_especiais
from .text.html_cleaner import limpar_html_malformado, limpeza_agressiva_html
from .text.markdown_processor import converter_markdown_para_html
from .graphics.chart_factory import criar_grafico
from .graphics.matplotlib_utils import safe_matplotlib_figure

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ===============================
# CONSTANTES E EXCEÇÕES AGORA IMPORTADAS DOS MÓDULOS REFATORADOS
# ===============================
# As constantes e exceções foram movidas para:
# - core/config.py: Constantes de segurança e paletas
# - core/exceptions.py: Exceções customizadas

def timeout_operation(func, timeout_seconds, *args, **kwargs):
    """
    Executa uma operação com timeout usando threading (compatível com Windows).
    
    Args:
        func: Função para executar
        timeout_seconds: Timeout em segundos
        *args, **kwargs: Argumentos para a função
        
    Returns:
        Resultado da função
        
    Raises:
        ImageProcessingTimeoutError: Se a operação exceder o timeout
    """
    result = [None]
    exception = [None]
    
    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout_seconds)
    
    if thread.is_alive():
        # Thread ainda está executando - timeout
        raise ImageProcessingTimeoutError(f"Operação excedeu timeout de {timeout_seconds}s")
    
    if exception[0]:
        raise exception[0]
    
    return result[0]

def validate_image_security(base64_data, image_id=None):
    """
    Validação completa de segurança para imagens.
    
    Implementa TODAS as validações de segurança necessárias:
    - Tamanho máximo do base64
    - Formato de imagem válido (magic bytes)
    - Dimensões da imagem
    - Proteção contra ataques
    
    Args:
        base64_data (str): Dados da imagem em base64
        image_id (str, optional): ID da imagem para logs
        
    Returns:
        bytes: Dados da imagem decodificados e validados
        
    Raises:
        ImageSecurityError: Se a imagem não passar nas validações
    """
    image_ref = f"ID:{image_id}" if image_id else "sequencial"
    
    try:
        # 1. VALIDAÇÃO DE TAMANHO DO BASE64
        base64_size_mb = len(base64_data) / (1024 * 1024)
        if base64_size_mb > MAX_IMAGE_SIZE_MB:
            raise ImageSecurityError(
                f"Imagem {image_ref} muito grande: {base64_size_mb:.2f}MB. "
                f"Máximo permitido: {MAX_IMAGE_SIZE_MB}MB"
            )
        
        # 2. DECODIFICAÇÃO SEGURA COM TIMEOUT
        logging.info(f"Validando imagem {image_ref} ({base64_size_mb:.2f}MB)")
        
        try:
            img_bytes = base64.b64decode(base64_data, validate=True)
        except Exception as e:
            raise ImageSecurityError(f"Dados base64 inválidos na imagem {image_ref}: {e}")
        
        # 3. VALIDAÇÃO DE TAMANHO DECODIFICADO
        decoded_size_mb = len(img_bytes) / (1024 * 1024)
        if decoded_size_mb > MAX_DECODE_SIZE_MB:
            raise ImageSecurityError(
                f"Imagem {image_ref} decodificada muito grande: {decoded_size_mb:.2f}MB. "
                f"Máximo permitido: {MAX_DECODE_SIZE_MB}MB"
            )
        
        # 4. VALIDAÇÃO DE FORMATO (MAGIC BYTES)
        format_detected = None
        for magic_bytes, format_name in ALLOWED_IMAGE_FORMATS.items():
            if img_bytes.startswith(magic_bytes):
                format_detected = format_name
                break
        
        if not format_detected:
            # Mostra os primeiros bytes para debug (seguro)
            first_bytes = img_bytes[:16].hex() if len(img_bytes) >= 16 else img_bytes.hex()
            raise ImageSecurityError(
                f"Formato de imagem não suportado na imagem {image_ref}. "
                f"Formatos permitidos: PNG, JPEG, GIF. "
                f"Magic bytes detectados: {first_bytes}"
            )
        
        # 5. VALIDAÇÃO PROFUNDA COM PIL (COM TIMEOUT)
        def validate_pil_image():
            img_buffer = io.BytesIO(img_bytes)
            with PILImage.open(img_buffer) as pil_img:
                # Verifica dimensões
                width, height = pil_img.size
                if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
                    raise ImageSecurityError(
                        f"Imagem {image_ref} muito grande: {width}x{height}px. "
                        f"Máximo permitido: {MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT}px"
                    )
                
                # Verifica se a imagem não está corrompida
                pil_img.verify()
                
                return width, height
        
        # Executa validação PIL com timeout (compatível Windows)
        width, height = timeout_operation(validate_pil_image, IMAGE_PROCESSING_TIMEOUT)
        
        logging.info(
            f"Imagem {image_ref} validada com sucesso: "
            f"{format_detected}, {width}x{height}px, {decoded_size_mb:.2f}MB"
        )
        
        return img_bytes
        
    except ImageProcessingTimeoutError:
        logging.error(f"Timeout ao processar imagem {image_ref}")
        raise ImageSecurityError(f"Timeout no processamento da imagem {image_ref}")
    
    except ImageSecurityError:
        # Re-raise security errors
        raise
    
    except Exception as e:
        logging.error(f"Erro inesperado ao validar imagem {image_ref}: {e}")
        raise ImageSecurityError(f"Erro na validação da imagem {image_ref}: {e}")

def validate_images_batch(imagens_anexadas):
    """
    Valida um lote de imagens aplicando limites globais.
    
    Args:
        imagens_anexadas (list): Lista de imagens para validar
        
    Returns:
        list: Lista de imagens validadas
        
    Raises:
        ImageSecurityError: Se o lote não passar nas validações
    """
    if not isinstance(imagens_anexadas, list):
        raise ImageSecurityError("Lista de imagens deve ser um array")
    
    # VALIDAÇÃO DE QUANTIDADE
    if len(imagens_anexadas) > MAX_IMAGE_COUNT:
        raise ImageSecurityError(
            f"Muitas imagens enviadas: {len(imagens_anexadas)}. "
            f"Máximo permitido: {MAX_IMAGE_COUNT} imagens por documento"
        )
    
    if len(imagens_anexadas) == 0:
        return []
    
    logging.info(f"Validando lote de {len(imagens_anexadas)} imagens...")
    
    validated_images = []
    total_size_mb = 0
    
    for i, img_data in enumerate(imagens_anexadas):
        if not isinstance(img_data, dict) or 'base64' not in img_data:
            raise ImageSecurityError(f"Imagem {i} tem formato inválido")
        
        image_id = img_data.get('id', i)
        
        # Valida cada imagem individualmente
        validated_bytes = validate_image_security(img_data['base64'], image_id)
        
        # Adiciona à contagem total
        size_mb = len(validated_bytes) / (1024 * 1024)
        total_size_mb += size_mb
        
        # Verifica limite total
        if total_size_mb > MAX_DECODE_SIZE_MB:
            raise ImageSecurityError(
                f"Tamanho total das imagens muito grande: {total_size_mb:.2f}MB. "
                f"Máximo permitido: {MAX_DECODE_SIZE_MB}MB total"
            )
        
        validated_images.append({
            **img_data,
            '_validated_bytes': validated_bytes,
            '_size_mb': size_mb
        })
    
    logging.info(f"Lote validado com sucesso: {len(validated_images)} imagens, {total_size_mb:.2f}MB total")
    return validated_images

# Context manager safe_matplotlib_figure movido para graphics/matplotlib_utils.py

# Função registrar_fontes_unicode movida para utils/fonts.py

# Função corrigir_caracteres_especiais movida para text/unicode_handler.py

# Função converter_markdown_para_html movida para text/markdown_processor.py

# Funções limpar_html_malformado() e limpeza_agressiva_html() já estão importadas de text/html_cleaner.py (linha 30)



def criar_grafico_linha(titulo, dados_texto, cores_paleta):
    try:
        import re
        
        partes = dados_texto.split(';')
        
        if len(partes) == 3:
            titulo_customizado = partes[0].strip()
            if titulo_customizado:
                titulo = titulo_customizado
            serie_parte = partes[1].strip()
            labels_parte = partes[2].strip()
        elif len(partes) == 2:
            serie_parte = partes[0].strip()
            labels_parte = partes[1].strip()
        else:
            logging.error(f"Formato inválido para gráfico de linha. Esperado 2 ou 3 partes, recebido {len(partes)}: {dados_texto}")
            return None
            
        serie_match = re.match(r'([^=]+)=([^;]+)', serie_parte)
        if not serie_match:
            logging.error(f"Erro ao fazer parse da série do gráfico de linha: {serie_parte}")
            return None
            
        serie_nome = serie_match.group(1).strip()
        valores_str = serie_match.group(2).strip()
        
        labels_match = re.match(r'([^=]+)=([^;]+)', labels_parte)
        if not labels_match:
            logging.error(f"Erro ao fazer parse das labels do gráfico de linha: {labels_parte}")
            return None
            
        labels_str = labels_match.group(2).strip()
        
        valores = [float(v.strip().replace(',', '.')) for v in valores_str.split(',')]
        labels = [l.strip() for l in labels_str.split(',')]
        
        if len(valores) != len(labels):
            logging.error(f"Número de valores ({len(valores)}) não coincide com labels ({len(labels)}) no gráfico de linha.")
            return None
        
        # Usando context manager para garantir que NUNCA vaze memória
        with safe_matplotlib_figure(figsize=(8, 5)) as fig:
            ax = fig.add_subplot(111)
            
            cor_linha = '#4299E1' if cores_paleta['principal'] == '#000000' else cores_paleta['principal']
            
            ax.plot(labels, valores, 
                    color=cor_linha, 
                    marker='o', 
                    linewidth=2.5, 
                    markersize=6,
                    alpha=0.9)
            
            ax.set_title(titulo, fontsize=14, fontweight='bold', pad=20)
            ax.set_ylabel('Valores', fontsize=10)
            
            ax.grid(True, linestyle='-', alpha=0.2, linewidth=0.5)
            ax.set_axisbelow(True)
            
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#E0E0E0')
            ax.spines['bottom'].set_color('#E0E0E0')
            
            for i, valor in enumerate(valores):
                ax.annotate(f'{valor}', (i, valor), 
                           textcoords="offset points", 
                           xytext=(0,10), ha='center', 
                           fontsize=9, color='black')
            
            plt.xticks(rotation=0, fontsize=9)
            plt.yticks(fontsize=9)
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='white')
            buf.seek(0)
            logging.info(f"Gráfico de linha criado com context manager: {titulo}")
            return buf
        
    except Exception as e:
        logging.error(f"Erro ao criar gráfico de linha: {e}", exc_info=True)
        # Context manager já fechou a figura automaticamente
        return None

def criar_grafico(titulo, dados_texto, cores_paleta, tipo_grafico='barras'):
    try:
        
        # Para gráfico de linha, usa formato diferente: "Serie1=val1,val2,val3; Meses=Jan,Fev"
        if tipo_grafico.lower() == 'linha':
            return criar_grafico_linha(titulo, dados_texto, cores_paleta)
        
        # Regex para parsing de dados do gráfico
        matches = re.findall(r'([^:,]+?):\s*(\d+(?:[.,]\d+)?)%?\s*(?:,|$)', dados_texto + ',')
        if not matches: 
            matches = re.findall(r'([^:,]+?):\s*(\d+(?:[.,]\d+)?)%?', dados_texto)
        if not matches:
            matches = re.findall(r'([^:,]+?)\s*:\s*(\d+(?:[.,]\d+)?)%?', dados_texto)
        if not matches:
            logging.warning(f"Não foi possível extrair dados para o gráfico '{titulo}' com o texto: '{dados_texto}'")
            return None
        
        # Processar valores
        labels = []
        valores = []
        for nome, valor in matches:
            labels.append(nome.strip())
            valor_limpo = valor.replace(',', '.')
            valores.append(float(valor_limpo))
        
        # Tamanho diferente para cada tipo de gráfico
        figsize = (7, 7) if tipo_grafico.lower() == 'pizza' else (8, 5)
        
        # Usando context manager para garantir que NUNCA vaze memória
        with safe_matplotlib_figure(figsize=figsize) as fig:
            ax = fig.add_subplot(111)
            
            if tipo_grafico.lower() == 'pizza':
                # Gráfico de Pizza com configurações melhoradas - Cores Voxy
                # Cores especiais para paleta preto e branco
                if cores_paleta['principal'] == '#000000':  # Paleta preto e branco
                    colors = [
                        '#4299E1',  # Azul Voxy
                        '#F6AD55',  # Laranja Voxy
                        '#40916C',  # Verde Voxy
                        '#9F7AEA',  # Roxo Voxy
                        '#E53E3E',  # Vermelho
                        '#38B2AC',  # Teal
                        '#ED64A6',  # Rosa
                        '#A0AEC0',  # Cinza (como fallback)
                    ]
                else:
                    colors = [
                        cores_paleta['principal'], 
                        cores_paleta['secundaria'], 
                        cores_paleta['destaque'], 
                        cores_paleta['fundo'],
                        '#95A5A6', '#E74C3C', '#F39C12', '#27AE60', '#8E44AD'  # cores complementares
                    ]
                
                # Configurar o gráfico pizza com estilo minimalista
                wedges, texts, autotexts = ax.pie(
                    valores, 
                    labels=labels, 
                    autopct='%1.1f%%', 
                    colors=colors[:len(valores)], 
                    startangle=90,
                    explode=[0.02] * len(valores),  # Separação mínima entre fatias
                    shadow=False,                   # Sem sombra para estilo minimalista
                    textprops={'fontsize': 10, 'fontweight': 'normal'}
                )
                
                ax.set_title(titulo, fontsize=14, fontweight='bold', pad=20)
                
                # Estilo para textos dos percentuais - cores claras para melhor visibilidade
                for autotext in autotexts:
                    # Para paleta preto e branco, usa texto branco
                    if cores_paleta['principal'] == '#000000':
                        autotext.set_color('white')
                    else:
                        autotext.set_color('white')  # Branco funciona bem na maioria das paletas
                    autotext.set_fontweight('bold')  # Negrito para melhor contraste
                    autotext.set_fontsize(10)
                    
                # Estilo minimalista para rótulos
                for text in texts:
                    text.set_fontsize(9)
                    text.set_fontweight('normal')
                
            else:
                # Gráfico de Barras com estilo minimalista
                # Cores especiais para paleta preto e branco
                if cores_paleta['principal'] == '#000000':  # Paleta preto e branco
                    colors_barras = [
                        '#4299E1', '#F6AD55', '#40916C', '#9F7AEA', 
                        '#E53E3E', '#38B2AC', '#ED64A6', '#A0AEC0'
                    ] * (len(valores) // 8 + 1)
                else:
                    colors_barras = [cores_paleta['principal'], cores_paleta['secundaria'], cores_paleta['destaque']] * (len(valores) // 3 + 1)
                
                if len(valores) > 1:
                    bars = ax.bar(labels, valores, color=colors_barras[:len(valores)], alpha=0.9, width=0.6)
                else:
                    bars = ax.bar(labels, valores, color=colors_barras[0], alpha=0.9, width=0.6)
                
                ax.set_title(titulo, fontsize=14, fontweight='bold', pad=20)
                ax.set_ylabel('Valores', fontsize=10)
                
                # Grid minimalista apenas no eixo Y
                ax.grid(axis='y', linestyle='-', alpha=0.2, linewidth=0.5)
                ax.set_axisbelow(True)
                
                # Remover bordas desnecessárias
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_color('#E0E0E0')
                ax.spines['bottom'].set_color('#E0E0E0')
                
                # Valores sobre as barras com estilo minimalista
                for bar, valor in zip(bars, valores):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + max(valores)*0.02, 
                           f'{valor}', ha='center', va='bottom', fontweight='normal', fontsize=9, color='black')
                
                plt.xticks(rotation=0, fontsize=9)
                plt.yticks(fontsize=9)
            
            plt.tight_layout()
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='white')
            buf.seek(0)
            logging.info(f"Gráfico {tipo_grafico} criado com context manager: {titulo}")
            return buf
        
    except Exception as e:
        logging.error(f"Erro ao criar gráfico {tipo_grafico}: {e}", exc_info=True)
        # Context manager já fechou a figura automaticamente
        return None

def criar_tabela(table_string, cores_paleta, total_width):
    try:
        table_string_normalized = re.sub(r'<br\s*/?>', '\n', table_string.strip())
        linhas = [linha.strip() for linha in table_string_normalized.split('\n') if linha.strip()]
        if len(linhas) < 2: 
            logging.warning(f"Dados insuficientes para criar tabela a partir de: {table_string}")
            return None

        titulo_tabela, *dados_tabela_str = linhas
        
        dados_tabela = []
        for linha in dados_tabela_str:
            # Dividir por | e limpar espaços, removendo células vazias no início/fim
            celulas = [cell.strip() for cell in linha.split('|')]
            # Remover células vazias no início e fim (comuns quando linha começa/termina com |)
            while celulas and not celulas[0]:
                celulas.pop(0)
            while celulas and not celulas[-1]:
                celulas.pop()
            if celulas:
                dados_tabela.append(celulas)
        
        if not dados_tabela: 
            logging.warning(f"Nenhuma linha de dados válida encontrada para a tabela: {titulo_tabela}")
            return None
        
        num_colunas = len(dados_tabela[0])
        col_widths = [total_width / num_colunas] * num_colunas
        cell_style = ParagraphStyle('cell_style', parent=getSampleStyleSheet()['Normal'], alignment=TA_LEFT)
        header_style = ParagraphStyle('header_style', parent=getSampleStyleSheet()['Normal'], alignment=TA_CENTER, fontName='Helvetica-Bold')
        header_row = [Paragraph(f'<b>{corrigir_caracteres_especiais(cell)}</b>', header_style) for cell in dados_tabela[0]]
        dados_tabela_formatada = [header_row]
        for row in dados_tabela[1:]:
            dados_tabela_formatada.append([Paragraph(limpar_html_malformado(corrigir_caracteres_especiais((cell or '').replace('\n', ' '))), cell_style) for cell in row])
        t = Table(dados_tabela_formatada, colWidths=col_widths, repeatRows=1)
        
        # Cor do zebra striping baseada na paleta (ou fallback para cinza)
        zebra_color = cores_paleta.get('zebra', '#F5F5F5')

        # Estilo clean para Dr. Pasto / preto e branco
        if cores_paleta.get('principal') in ['#000000', '#1A1A1A']:
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#cccccc')),
                ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.HexColor('#eeeeee')),
            ])
        else:
            # Estilo moderno para relatórios coloridos
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(cores_paleta['principal'])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor(cores_paleta['destaque'])),
                ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.HexColor('#E0E0E0')),
            ])

        # Zebra striping com cor da paleta
        for i in range(1, len(dados_tabela_formatada)):
            if i % 2 == 0:
                style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor(zebra_color))
        t.setStyle(style)
        logging.info(f"Tabela criada: {titulo_tabela}")
        titulo_style = ParagraphStyle('TituloTabela', fontName='Helvetica-Bold', fontSize=12, spaceBefore=15, spaceAfter=10, textColor=colors.HexColor(cores_paleta['principal']))
        return [Paragraph(titulo_tabela, titulo_style), t]
    except Exception as e:
        logging.error(f"Erro ao criar tabela: {e}", exc_info=True)
        return [Paragraph(limpar_html_malformado((table_string or '').replace('\n', '<br/>')), ParagraphStyle('TextoNormal'))]


def parse_conteudo(texto, estilos, cores, total_width, imagens_disponiveis):
    elementos = []
    
    imagens_por_id = {}
    imagens_sequenciais = []
    
    for img in imagens_disponiveis:
        if 'id' in img and img['id'] is not None:
            # Nova lógica: imagem com ID
            imagens_por_id[str(img['id'])] = img
        else:
            # Lógica antiga: imagem sem ID (para manter compatibilidade)
            imagens_sequenciais.append(img)
    
    padrao_geral = r'(\[GRÁFICO_BARRAS:[^\]]+\]|\[GRAFICO_BARRAS:[^\]]+\]|\[GRÁFICO PIZZA:[^\]]+\]|\[GRAFICO PIZZA:[^\]]+\]|\[GRÁFICO_PIZZA:[^\]]+\]|\[GRAFICO_PIZZA:[^\]]+\]|\[GRÁFICO DE BARRAS:[^\]]+\]|\[GRAFICO DE BARRAS:[^\]]+\]|\[GRÁFICO DE PIZZA:[^\]]+\]|\[GRAFICO DE PIZZA:[^\]]+\]|\[GRÁFICO_LINHA:[^\]]+\]|\[GRAFICO_LINHA:[^\]]+\]|\[GRÁFICO DE LINHA:[^\]]+\]|\[GRAFICO DE LINHA:[^\]]+\]|\[TABELA:[\s\S]*?\]|\[IMAGEM(?::\d+)?\])'
    partes = re.split(padrao_geral, texto)

    for parte in partes:
        if not parte or parte.isspace(): continue

        if parte.startswith('[IMAGEM'):
            match_id = re.match(r'\[IMAGEM:(\d+)\]', parte)
            
            if match_id:
                img_id = match_id.group(1)
                if img_id in imagens_por_id:
                    img_data = imagens_por_id[img_id]
                    try:
                        # USA OS BYTES JÁ VALIDADOS (segurança garantida)
                        if '_validated_bytes' in img_data:
                            img_bytes = img_data['_validated_bytes']
                            logging.info(f"Usando imagem pré-validada ID {img_id} ({img_data.get('_size_mb', 0):.2f}MB)")
                        else:
                            # Fallback para compatibilidade (não deveria acontecer)
                            logging.warning(f"Imagem ID {img_id} não foi pré-validada, validando agora...")
                            img_bytes = validate_image_security(img_data['base64'], img_id)
                        
                        # Detectar orientação da imagem para tamanho adaptativo
                        with PILImage.open(io.BytesIO(img_bytes)) as pil_img:
                            w, h = pil_img.size
                            if w > h:  # Paisagem
                                img_width, img_height = 5.5*inch, 3.5*inch
                            else:  # Retrato
                                img_width, img_height = 3.5*inch, 5*inch

                        img_buffer = io.BytesIO(img_bytes)
                        elementos.append(Spacer(1, 0.2 * inch))
                        elementos.append(Image(img_buffer, width=img_width, height=img_height, kind='proportional'))

                        # Adiciona legenda se existir
                        if img_data.get('legenda'):
                            legenda_style = ParagraphStyle('Legenda', fontSize=9, alignment=TA_CENTER, textColor=colors.gray, spaceAfter=12)
                            elementos.append(Paragraph(f"<i>{img_data['legenda']}</i>", legenda_style))

                        elementos.append(Spacer(1, 0.2 * inch))
                        logging.info(f"Imagem com ID {img_id} inserida no documento com segurança.")
                    except Exception as e:
                        logging.error(f"Erro ao processar imagem com ID {img_id}: {e}")
                else:
                    logging.warning(f"Imagem com ID {img_id} referenciada no texto mas não encontrada na lista de anexos.")
            elif parte == '[IMAGEM]':
                if imagens_sequenciais:
                    img_data = imagens_sequenciais.pop(0)
                    try:
                        # USA OS BYTES JÁ VALIDADOS (segurança garantida)
                        if '_validated_bytes' in img_data:
                            img_bytes = img_data['_validated_bytes']
                            logging.info(f"Usando imagem sequencial pré-validada ({img_data.get('_size_mb', 0):.2f}MB)")
                        else:
                            # Fallback para compatibilidade (não deveria acontecer)
                            logging.warning("Imagem sequencial não foi pré-validada, validando agora...")
                            img_bytes = validate_image_security(img_data['base64'])
                        
                        # Detectar orientação da imagem para tamanho adaptativo
                        with PILImage.open(io.BytesIO(img_bytes)) as pil_img:
                            w, h = pil_img.size
                            if w > h:  # Paisagem
                                img_width, img_height = 5.5*inch, 3.5*inch
                            else:  # Retrato
                                img_width, img_height = 3.5*inch, 5*inch

                        img_buffer = io.BytesIO(img_bytes)
                        elementos.append(Spacer(1, 0.2 * inch))
                        elementos.append(Image(img_buffer, width=img_width, height=img_height, kind='proportional'))

                        # Adiciona legenda se existir
                        if img_data.get('legenda'):
                            legenda_style = ParagraphStyle('Legenda', fontSize=9, alignment=TA_CENTER, textColor=colors.gray, spaceAfter=12)
                            elementos.append(Paragraph(f"<i>{img_data['legenda']}</i>", legenda_style))

                        elementos.append(Spacer(1, 0.2 * inch))
                        logging.info("Imagem sequencial inserida com segurança (modo de compatibilidade).")
                    except Exception as e:
                        logging.error(f"Erro ao processar imagem sequencial: {e}")
                else:
                    logging.warning("Tag [IMAGEM] encontrada, mas não há mais imagens sequenciais disponíveis.")
        
        elif any(tag in parte.upper() for tag in ['[GRÁFICO', '[GRAFICO']):
            parte_upper = parte.upper()
            if 'BARRA' in parte_upper:
                tipo_grafico = 'barras'
            elif 'PIZZA' in parte_upper or 'TORTA' in parte_upper:
                tipo_grafico = 'pizza'
            elif 'LINHA' in parte_upper:
                tipo_grafico = 'linha'
            else:
                tipo_grafico = 'barras'  # padrão
            
            match = re.search(r'\[(?:GRÁFICO|GRAFICO)[^:]*:\s*([^:]+):\s*(.*)\]', parte)
                
            if match:
                titulo, dados = match.groups()
                
                img_buffer = criar_grafico(titulo.strip(), dados.strip(), cores, tipo_grafico)
                if img_buffer:
                    if tipo_grafico == 'pizza':
                        elementos.append(Image(img_buffer, width=4.5*inch, height=3*inch))
                    else:
                        elementos.append(Image(img_buffer, width=5.5*inch, height=3.5*inch))
                    elementos.append(Spacer(1, 0.2*inch))
                    logging.info(f"Gráfico {tipo_grafico} '{titulo.strip()}' inserido no documento.")
                else:
                    logging.error(f"Falha ao criar gráfico {tipo_grafico}: '{titulo.strip()}' com dados: '{dados.strip()}'")
                    elementos.append(Paragraph(f"[ERRO: Gráfico não pôde ser criado - {titulo.strip()}]", estilos['TextoNormal']))
        elif parte.startswith('[TABELA:'):
            match = re.search(r'\[TABELA:\s*([\s\S]*?)\]', parte)
            if match:
                tabela_elementos = criar_tabela(match.group(1).strip(), cores, total_width)
                if tabela_elementos:
                    elementos.extend(tabela_elementos)
        else:
            blocos = re.split(r'\n\s*\n', parte.strip())
            
            for bloco in blocos:
                if not bloco or bloco.isspace():
                    continue

                bloco_html = converter_markdown_para_html(bloco)
                
                if '[SEPARADOR_HORIZONTAL]' in bloco_html:
                    from reportlab.platypus import HRFlowable
                    elementos.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor(cores['secundaria']), spaceAfter=0.2*inch, spaceBefore=0.2*inch))
                    bloco_html = bloco_html.replace('[SEPARADOR_HORIZONTAL]', '')
                    if not bloco_html.strip() or bloco_html.strip() == '<br/>':
                        continue
                
                # Registra fonte Unicode
                fonte_unicode = registrar_fontes_unicode()
                fonte_bold = f'{fonte_unicode}-Bold' if fonte_unicode != 'Helvetica' else 'Helvetica-Bold'
                
                # Processa títulos hierárquicos
                for nivel in range(1, 7):
                    padrao_titulo = f'\\[TITULO_NIVEL_{nivel}\\](.*?)\\[/TITULO_NIVEL_{nivel}\\]'
                    matches = re.findall(padrao_titulo, bloco_html)
                    for match in matches:
                        estilo_nome = f'TituloNivel{nivel}'
                        if estilo_nome not in estilos:
                            if nivel == 1:
                                # Título principal - grande e destacado
                                estilos[estilo_nome] = ParagraphStyle(
                                    estilo_nome,
                                    fontName=fonte_bold,
                                    fontSize=18,
                                    textColor=colors.HexColor(cores['principal']),
                                    spaceAfter=16,
                                    spaceBefore=28,
                                    leading=22,
                                    leftIndent=0,
                                    borderPadding=0,
                                )
                            elif nivel == 2:
                                # Título de seção - destaque forte com borda lateral
                                estilos[estilo_nome] = ParagraphStyle(
                                    estilo_nome,
                                    fontName=fonte_bold,
                                    fontSize=14,
                                    textColor=colors.HexColor(cores['principal']),
                                    spaceAfter=12,
                                    spaceBefore=22,
                                    leading=18,
                                    leftIndent=0,
                                    borderLeftWidth=3,
                                    borderLeftColor=colors.HexColor(cores['destaque']),
                                    borderPadding=(8, 0, 8, 12),  # top, right, bottom, left
                                    backColor=colors.HexColor('#F8F9FA'),  # Fundo sutil
                                )
                            elif nivel == 3:
                                # Subtítulo - menor mas ainda destacado
                                estilos[estilo_nome] = ParagraphStyle(
                                    estilo_nome,
                                    fontName=fonte_bold,
                                    fontSize=12,
                                    textColor=colors.HexColor(cores['principal']),
                                    spaceAfter=10,
                                    spaceBefore=16,
                                    leading=16,
                                    leftIndent=8,
                                )
                            else:
                                # Níveis menores
                                estilos[estilo_nome] = ParagraphStyle(
                                    estilo_nome,
                                    fontName=fonte_bold,
                                    fontSize=11,
                                    textColor=colors.HexColor(cores['secundaria']),
                                    spaceAfter=8,
                                    spaceBefore=12,
                                    leading=14,
                                    leftIndent=16,
                                )

                        titulo_limpo = match.strip()
                        elementos.append(Paragraph(f'<b>{titulo_limpo}</b>', estilos[estilo_nome]))
                        bloco_html = re.sub(padrao_titulo, '', bloco_html)
                
                # Processa itens de lista
                padrao_lista = r'\[ITEM_LISTA\](.*?)\[/ITEM_LISTA\]'
                matches_lista = re.findall(padrao_lista, bloco_html)
                for match in matches_lista:
                    if 'ItemLista' not in estilos:
                        estilos['ItemLista'] = ParagraphStyle(
                            'ItemLista',
                            fontName=fonte_unicode,
                            fontSize=11,
                            textColor=colors.black,
                            spaceAfter=6,
                            spaceBefore=2,
                            leading=14,
                            leftIndent=20,
                            bulletIndent=10
                        )
                    
                    item_limpo = match.strip()
                    elementos.append(Paragraph(item_limpo, estilos['ItemLista']))
                    bloco_html = re.sub(padrao_lista, '', bloco_html)
                
                texto_limpo = limpar_html_malformado(bloco_html)
                texto_limpo = re.sub(r'^(<br/>)+', '', texto_limpo)
                texto_limpo = re.sub(r'(<br/>)+$', '', texto_limpo)
                
                if '<b>' in texto_limpo and '</b>' not in texto_limpo:
                    texto_limpo = limpeza_agressiva_html(texto_limpo)
                
                if texto_limpo.strip() and texto_limpo.strip() != '<br/>':
                    elementos.append(Paragraph(texto_limpo, estilos['TextoNormal']))
                    elementos.append(Spacer(1, 0.1 * inch))
            
    return elementos

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITENS_PNG_DIR = os.path.join(BASE_DIR, 'itens_png_voxy') # Corrigido para itens_png_voxy

# Novos diretórios para as subpastas de imagens
IMAGENS_ARIZONA_DIR = os.path.join(ITENS_PNG_DIR, 'imagens_arizona')
IMAGENS_DR_PASTO_DIR = os.path.join(ITENS_PNG_DIR, 'imagens_dr_pasto')

LOGO_PRINCIPAL_PATH = os.path.join(IMAGENS_ARIZONA_DIR, 'logoprincipal.png')
LINHA_VERMELHA_PATH = os.path.join(IMAGENS_ARIZONA_DIR, 'linhavermelha.png')
ARCO_FINAL_PATH = os.path.join(IMAGENS_ARIZONA_DIR, 'arcofinal.png')
LEGENDA_PATH = os.path.join(IMAGENS_ARIZONA_DIR, 'legenda.png')

def draw_arizona_template(canvas, doc):
    canvas.saveState()
    width, height = A4

    try:
        arc_width = 16 * cm
        arc_height = 10 * cm
        arc_y_position = 2.5 * cm
        arc_x_position = -3.8 * cm 
        canvas.drawImage(ARCO_FINAL_PATH, arc_x_position, arc_y_position, width=arc_width, height=arc_height, preserveAspectRatio=True, mask='auto')

        legenda_width = 12 * cm
        legenda_height = 2 * cm
        legenda_x_position = (width - legenda_width) / 2
        legenda_y_position = 0.5 * cm
        canvas.drawImage(LEGENDA_PATH, legenda_x_position, legenda_y_position, width=legenda_width, height=legenda_height, preserveAspectRatio=True, mask='auto')

    except Exception as e:
        logging.warning(f"Não foi possível desenhar o rodapé do template: {e}")

    try:
        logo_width = 4 * cm
        logo_height = 2 * cm
        logo_x = width - doc.rightMargin - logo_width
        logo_y = height - 2.5 * cm
        canvas.drawImage(LOGO_PRINCIPAL_PATH, logo_x, logo_y, width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')

        line_width_new = 13 * cm
        line_height = 1.5
        line_x_new = (logo_x + logo_width) - line_width_new
        line_y = logo_y - (0.1 * cm)
        canvas.drawImage(LINHA_VERMELHA_PATH, line_x_new, line_y, width=line_width_new, height=line_height, preserveAspectRatio=False)

    except Exception as e:
        logging.warning(f"Não foi possível desenhar o cabeçalho do template: {e}")

    canvas.restoreState()


def draw_footer_and_logo(canvas, doc, rodape_text, logo_base64, cores):
    canvas.saveState()

    width, height = A4
    y_position = 15

    # Logo do usuário no canto ESQUERDO (se houver)
    logo_width = 0.6 * inch
    logo_height = 0.6 * inch

    if logo_base64:
        try:
            logo_x = doc.leftMargin  # Esquerda
            logo_bytes = base64.b64decode(logo_base64)
            logo_buffer = io.BytesIO(logo_bytes)
            logo_image = Image(logo_buffer, width=logo_width, height=logo_height, kind='proportional')
            logo_image.drawOn(canvas, logo_x, y_position)
        except Exception as e:
            logging.error(f"Erro ao desenhar o logo no rodapé: {e}")

    # Texto Voxy CENTRALIZADO
    voxy_text = "Documento feito com ajuda do Voxy Agro"
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor('#999999'))
    text_width = canvas.stringWidth(voxy_text, "Helvetica", 7)
    center_x = (width - text_width) / 2
    canvas.drawString(center_x, y_position + 5, voxy_text)

    canvas.restoreState()


def draw_footer_dr_pasto(canvas, doc, rodape_text, cores):
    """
    Rodapé simples para Dr. Pasto sem logo no rodapé.
    """
    canvas.saveState()

    width, height = A4
    y_position = 15

    # Texto Voxy CENTRALIZADO
    voxy_text = "Documento feito com ajuda do Voxy Agro"
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor('#999999'))
    text_width = canvas.stringWidth(voxy_text, "Helvetica", 7)
    center_x = (width - text_width) / 2
    canvas.drawString(center_x, y_position + 5, voxy_text)

    canvas.restoreState()


def create_pdf_from_data(data: dict):
    imagens_anexadas = data.get('imagens_anexadas', [])
    if not isinstance(imagens_anexadas, list):
        logging.warning("Campo 'imagens_anexadas' não era uma lista e foi corrigido para uma lista vazia.")
        imagens_anexadas = []
    
    # VALIDAÇÃO CRÍTICA DE SEGURANÇA - TODAS AS IMAGENS
    try:
        imagens_anexadas = validate_images_batch(imagens_anexadas)
        logging.info(f"Validação de segurança concluída para {len(imagens_anexadas)} imagens")
    except ImageSecurityError as e:
        logging.error(f"FALHA DE SEGURANÇA: {e}")
        raise ValueError(f"Validação de segurança das imagens falhou: {e}")

    # Detecta se é relatório Dr. Pasto
    is_dr_pasto = (data.get('tipo_documento', '').lower().find('adubação') != -1 or 
                   data.get('tecnico_nome', '').lower().find('dr. pasto') != -1)

    # Paletas agora vêm do módulo de configuração - Dr. Pasto sempre preto e branco
    if is_dr_pasto:
        paleta_escolhida = 'preto_e_branco'
    else:
        paleta_escolhida = data.get('paleta_cores', 'preto_e_branco')
    cores = get_color_palette(paleta_escolhida)

    page_width, page_height = A4
    margins = 72
    effective_width = page_width - 2 * margins

    # Configurações agora vêm do módulo de configuração
    campos_ignorar = IGNORED_CONTENT_FIELDS
    ordem_preferida = CONTENT_FIELD_ORDER
    
    texto_consolidado = []
    campos_processados = set()

    for campo in ordem_preferida:
        if data.get(campo) and isinstance(data[campo], str):
            texto_consolidado.append(data[campo])
            campos_processados.add(campo)
    
    for campo, valor in data.items():
        if (campo not in campos_ignorar and campo not in campos_processados and isinstance(valor, str) and valor.strip()):
            texto_consolidado.append(valor)

    texto_final = "\n\n<br/><br/>\n\n".join(texto_consolidado)

    logo_base64 = None
    imagens_restantes = []

    match_logo = re.search(r'\[LOGO:(\d+)\]', texto_final)
    if match_logo:
        logo_id_str = match_logo.group(1)
        texto_final = texto_final.replace(match_logo.group(0), '', 1)
        
        logo_encontrado = False
        for img in imagens_anexadas:
            if not logo_encontrado and 'id' in img and str(img.get('id')) == logo_id_str:
                logo_base64 = img.get('base64')
                logo_encontrado = True
                logging.info(f"Imagem com ID {logo_id_str} identificada como logo via tag.")
            else:
                imagens_restantes.append(img)
        
        if not logo_encontrado:
            logging.warning(f"Tag [LOGO:{logo_id_str}] encontrada, mas imagem com este ID não existe na lista de anexos.")
            imagens_restantes = imagens_anexadas
    else:
        imagens_restantes = imagens_anexadas

    doc_buffer = io.BytesIO()
    doc = SimpleDocTemplate(doc_buffer, pagesize=A4, rightMargin=margins, leftMargin=margins, topMargin=margins, bottomMargin=margins)
    
    data_hora = datetime.now().strftime("%d/%m/%Y às %H:%M")
    
    # Rodapé diferente para Dr. Pasto
    if is_dr_pasto:
        rodape_text = f"Documento gerado em {data_hora} | DR PASTO - {data.get('tipo_documento', 'documento')} | Responsável: {data.get('tecnico_nome', 'Sistema')}"
    else:
        rodape_text = f"Documento gerado em {data_hora} | Voxy.agro - {data.get('tipo_documento', 'documento')} | Responsável: {data.get('tecnico_nome', 'Sistema')}"

    if is_dr_pasto:
        on_page_handler = lambda canvas, doc: draw_footer_dr_pasto(canvas, doc, rodape_text, cores)
    else:
        on_page_handler = lambda canvas, doc: draw_footer_and_logo(canvas, doc, rodape_text, logo_base64, cores)

    main_frame = Frame(margins, margins, effective_width, page_height - 2*margins, id='main_frame')
    template = PageTemplate(id='main_template', frames=[main_frame], onPage=on_page_handler)
    doc.addPageTemplates([template])
    
    story = []
    
    # Registra fonte Unicode
    fonte_unicode = registrar_fontes_unicode()
    fonte_bold = f'{fonte_unicode}-Bold' if fonte_unicode != 'Helvetica' else 'Helvetica-Bold'
    
    # Estilos diferentes para Dr. Pasto
    if is_dr_pasto:
        styles = {
            'TituloPrincipal': ParagraphStyle('TituloPrincipal', fontName=fonte_bold, fontSize=18, textColor=colors.HexColor(cores['principal']), alignment=TA_CENTER, leading=22, spaceAfter=20, spaceBefore=30),
            'TituloSecao': ParagraphStyle('TituloSecao', fontName=fonte_bold, fontSize=16, textColor=colors.HexColor(cores['principal']), spaceAfter=18, spaceBefore=24, borderBottomWidth=2, borderBottomColor=colors.HexColor(cores['destaque']), paddingBottom=8),
            'TextoNormal': ParagraphStyle('TextoNormal', fontName=fonte_unicode, fontSize=11, alignment=TA_JUSTIFY, spaceAfter=14, spaceBefore=6, leading=16),
            'TituloSubsecao': ParagraphStyle('TituloSubsecao', fontName=fonte_bold, fontSize=14, textColor=colors.HexColor(cores['principal']), spaceAfter=12, spaceBefore=18, leading=18),
        }
    else:
        # Estilo minimalista v2.0 - tipografia forte, sem fundo colorido
        styles = {
            'TituloPrincipal': ParagraphStyle('TituloPrincipal', fontName=fonte_bold, fontSize=24, textColor=colors.HexColor(cores['principal']), alignment=TA_LEFT, leading=30, spaceAfter=8),
            'TituloSecao': ParagraphStyle('TituloSecao', fontName=fonte_bold, fontSize=16, textColor=colors.HexColor(cores['principal']), spaceAfter=18, spaceBefore=24, borderBottomWidth=2, borderBottomColor=colors.HexColor(cores['destaque']), paddingBottom=8),
            'TextoNormal': ParagraphStyle('TextoNormal', fontName=fonte_unicode, fontSize=11, alignment=TA_JUSTIFY, spaceAfter=14, spaceBefore=6, leading=16),
            'TituloSubsecao': ParagraphStyle('TituloSubsecao', fontName=fonte_bold, fontSize=14, textColor=colors.HexColor(cores['principal']), spaceAfter=12, spaceBefore=18, leading=18),
        }

    # Para Dr. Pasto: Logo centralizada no topo
    if is_dr_pasto:
        try:
            # Carrega logo do Dr. Pasto
            logo_path = os.path.join(IMAGENS_DR_PASTO_DIR, 'logo_drPasto.png')
            if os.path.exists(logo_path):
                logo_img = Image(logo_path, width=2*inch, height=2*inch, kind='proportional')
                logo_img.hAlign = 'CENTER'
                story.append(logo_img)
                story.append(Spacer(1, 0.3 * inch))
                logging.info("Logo Dr. Pasto adicionada com sucesso")
            else:
                logging.warning(f"Logo Dr. Pasto não encontrada em: {logo_path}")
        except Exception as e:
            logging.error(f"Erro ao carregar logo Dr. Pasto: {e}")

    story.append(Paragraph(data.get('titulo_documento', 'Relatório Técnico'), styles['TituloPrincipal']))

    # Para Dr. Pasto: Adiciona subtítulo com metodologia
    if is_dr_pasto:
        subtitle_style = ParagraphStyle('SubtituloMetodologia',
                                       fontName=fonte_unicode,
                                       fontSize=12,
                                       textColor=colors.HexColor(cores['secundaria']),
                                       alignment=TA_CENTER,
                                       leading=14,
                                       spaceAfter=20,
                                       spaceBefore=8)
        story.append(Paragraph("Metodologia do Professor Dr. Leandro Barbero", subtitle_style))

    # Design minimalista v2.0: linha divisora após título
    if not is_dr_pasto:
        # Linha divisora colorida
        from reportlab.platypus import HRFlowable
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor(cores['destaque']), spaceBefore=4, spaceAfter=16))
    else:
        story.append(Spacer(1, 0.2 * inch))

    # Para Dr. Pasto: Não mostrar campos de usuário
    if not is_dr_pasto:
        # Design minimalista: informações em grid horizontal
        info_items = []
        if data.get('propriedade'): info_items.append(f"<b>Propriedade:</b> {data['propriedade']}")
        if data.get('cliente'): info_items.append(f"<b>Cliente:</b> {data['cliente']}")
        if data.get('data_documento'): info_items.append(f"<b>Data:</b> {data['data_documento']}")
        if data.get('tecnico_nome'): info_items.append(f"<b>Técnico:</b> {data['tecnico_nome']}")

        if info_items:
            # Estilo minimalista: texto cinza, sem borda, sem fundo
            info_style = ParagraphStyle(
                'InfoMinimalista',
                fontName=fonte_unicode,
                fontSize=10,
                textColor=colors.HexColor(cores['secundaria']),
                leading=16,
                spaceAfter=20
            )
            # Separar itens com pipe (|) para visual horizontal
            info_text = "  •  ".join(info_items)
            story.append(Paragraph(limpar_html_malformado(info_text), info_style))

    if texto_final.strip():
        elementos = parse_conteudo(texto_final, styles, cores, effective_width, imagens_restantes)
        story.extend(elementos)

    # ===== SEÇÃO DE ASSINATURA DO TÉCNICO v2.0 =====
    # Usa proprietario_detalhes se disponível, senão usa dados do técnico do documento
    detalhes = data.get('proprietario_detalhes', {})
    tecnico_nome = detalhes.get('nome') if detalhes else data.get('tecnico_nome')
    tecnico_telefone = detalhes.get('numero') if detalhes else None
    tecnico_email = detalhes.get('email') if detalhes else None
    tecnico_cargo = detalhes.get('cargo') or detalhes.get('formacao') if detalhes else None

    # Só mostra seção de assinatura se tiver pelo menos o nome do técnico
    if tecnico_nome:
        from reportlab.platypus import HRFlowable, KeepTogether

        # Lista de elementos da assinatura (para manter juntos na mesma página)
        assinatura_elementos = []

        assinatura_elementos.append(Spacer(1, 1*cm))

        # Linha divisora antes da assinatura
        assinatura_elementos.append(HRFlowable(width="40%", thickness=1, color=colors.HexColor(cores['destaque']), spaceBefore=0, spaceAfter=16, hAlign='CENTER'))

        # Estilo para nome do técnico (destaque)
        nome_style = ParagraphStyle(
            'NomeTecnico',
            fontName=fonte_bold,
            fontSize=14,
            textColor=colors.HexColor(cores['principal']),
            alignment=TA_CENTER,
            spaceAfter=4,
            leading=18
        )
        assinatura_elementos.append(Paragraph(tecnico_nome, nome_style))

        # Estilo para informações de contato
        contato_style = ParagraphStyle(
            'ContatoTecnico',
            fontName=fonte_unicode,
            fontSize=10,
            textColor=colors.HexColor(cores['secundaria']),
            alignment=TA_CENTER,
            spaceAfter=2,
            leading=14
        )

        # Cargo/formação (se existir)
        if tecnico_cargo:
            assinatura_elementos.append(Paragraph(tecnico_cargo, contato_style))

        # Telefone e email em uma linha (se existirem)
        contato_items = []
        if tecnico_telefone:
            contato_items.append(f"📞 {tecnico_telefone}")
        if tecnico_email:
            contato_items.append(f"✉️ {tecnico_email}")

        if contato_items:
            assinatura_elementos.append(Paragraph("  •  ".join(contato_items), contato_style))

        # KeepTogether garante que todos os elementos da assinatura fiquem na mesma página
        story.append(KeepTogether(assinatura_elementos))
            
    doc.build(story, onLaterPages=on_page_handler)
    
    pdf_bytes = doc_buffer.getvalue()
    doc_buffer.close()
    return pdf_bytes


def preencher_pdf_template(data: dict):
    try:
        imagens_anexadas = data.get('imagens_anexadas', [])
        if not isinstance(imagens_anexadas, list):
            logging.warning("Campo 'imagens_anexadas' não era uma lista e foi corrigido para uma lista vazia.")
            imagens_anexadas = []
        
        # VALIDAÇÃO CRÍTICA DE SEGURANÇA - TODAS AS IMAGENS
        try:
            imagens_anexadas = validate_images_batch(imagens_anexadas)
            logging.info(f"Validação de segurança concluída para {len(imagens_anexadas)} imagens (template)")
        except ImageSecurityError as e:
            logging.error(f"FALHA DE SEGURANÇA NO TEMPLATE: {e}")
            raise ValueError(f"Validação de segurança das imagens falhou: {e}")

        # Paletas agora vêm do módulo de configuração
        paleta_escolhida = data.get('paleta_cores', 'preto_e_branco')
        cores_padrao = get_color_palette(paleta_escolhida)
            
        buffer = io.BytesIO()
        page_width, page_height = A4
        right_margin, left_margin = 2*cm, 2*cm
        effective_width = page_width - right_margin - left_margin

        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=right_margin, leftMargin=left_margin,
                                topMargin=4*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        
        # Registra fonte Unicode
        fonte_unicode = registrar_fontes_unicode()
        fonte_bold = f'{fonte_unicode}-Bold' if fonte_unicode != 'Helvetica' else 'Helvetica-Bold'

        styles['BodyText'].fontName = fonte_unicode
        styles['BodyText'].fontSize = 9
        styles['BodyText'].leading = 12
        styles['BodyText'].alignment = TA_JUSTIFY

        styles.add(ParagraphStyle(name='SectionTitle',
                                  fontName=fonte_bold,
                                  fontSize=9,
                                  leading=12,
                                  alignment=TA_LEFT,
                                  spaceBefore=0.6*cm,
                                  spaceAfter=0.2*cm))
        styles.add(ParagraphStyle(name='HeaderInfo',
                                  fontName=fonte_unicode,
                                  fontSize=9,
                                  leading=12,
                                  spaceAfter=2,
                                  alignment=TA_LEFT))
        
        # Cria estilos customizados
        custom_styles = {
            'TextoNormal': ParagraphStyle('TextoNormal', parent=styles['BodyText']),
            'TituloSubsecao': ParagraphStyle('TituloSubsecao', parent=styles['SectionTitle'])
        }

        story = []

        info_data = {
            "Fecha de la visita:": data.get('fecha_de_visita'),
            "Lugar:": data.get('nombre_de_la_hacienda'),
            "Responsable:": data.get('tecnicos_responsables'),
            "Presentes:": data.get('responsables_presentes'),
            "Propietario:": data.get('propietario')
        }
        
        info_texts = []
        for label, value in info_data.items():
            if value:
                info_texts.append(f"<b>{label}</b> {value}")
        
        if info_texts:
            story.append(Paragraph("<br/>".join(info_texts), styles['HeaderInfo']))

        # Processa o conteúdo principal
        if data.get('contenido_principal') and isinstance(data['contenido_principal'], str) and data['contenido_principal'].strip():
            # Cria um dicionário de estilos modificável
            estilos_modificaveis = {
                'TextoNormal': custom_styles['TextoNormal'],
                'TituloSubsecao': custom_styles['TituloSubsecao'],
                'SectionTitle': styles['SectionTitle'],
                'HeaderInfo': styles['HeaderInfo'],
                'BodyText': styles['BodyText']
            }
            elementos_conteudo = parse_conteudo(data['contenido_principal'], estilos_modificaveis, cores_padrao, effective_width, imagens_anexadas)
            story.extend(elementos_conteudo)

        # Adiciona seção de assinatura
        if data.get('proprietario_detalhes'):
            detalhes = data['proprietario_detalhes']
            
            # Espaçamento antes da assinatura
            story.append(Spacer(1, 1*cm))
            
            # Estilo para assinatura
            assinatura_style = ParagraphStyle(
                'AssinaturaStyle',
                fontName=fonte_unicode,
                fontSize=11,
                alignment=TA_CENTER,
                spaceAfter=8,
                leading=16
            )
            
            # Adiciona os elementos da assinatura
            story.append(Paragraph("Atenciosamente!", assinatura_style))
            story.append(Spacer(1, 0.5*cm))
            
            # Nome em negrito
            nome_style = ParagraphStyle(
                'NomeStyle',
                parent=assinatura_style,
                fontName=fonte_bold,
                fontSize=12
            )
            story.append(Paragraph(detalhes.get('nome', ''), nome_style))
            
            # Formação e cargo
            story.append(Paragraph(detalhes.get('formacao', ''), assinatura_style))
            story.append(Paragraph(detalhes.get('cargo', ''), assinatura_style))

        doc.build(story, onFirstPage=draw_arizona_template, onLaterPages=draw_arizona_template)

        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    except Exception as e:
        logging.error(f"Erro ao gerar o PDF com template Arizona: {e}", exc_info=True)
        raise
