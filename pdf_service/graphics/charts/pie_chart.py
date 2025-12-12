# Arquivo: graphics/charts/pie_chart.py
# Geração de gráficos de pizza

import io
import re
import logging
import matplotlib.pyplot as plt
from ..matplotlib_utils import safe_matplotlib_figure
from ...core.exceptions import ChartGenerationError

def criar_grafico_pizza(titulo, dados_texto, cores_paleta):
    """
    Cria um gráfico de pizza a partir de dados textuais.
    
    Args:
        titulo (str): Título do gráfico
        dados_texto (str): Dados no formato "Label1: valor1, Label2: valor2"
        cores_paleta (dict): Paleta de cores do documento
        
    Returns:
        io.BytesIO: Buffer com imagem PNG do gráfico ou None se erro
        
    Example:
        dados = "Desktop: 60, Mobile: 30, Tablet: 10"
        buffer = criar_grafico_pizza("Dispositivos", dados, cores)
    """
    try:
        # Parse dos dados usando regex flexível
        matches = re.findall(r'([^:,]+?):\s*(\d+(?:[.,]\d+)?)%?\s*(?:,|$)', dados_texto + ',')
        if not matches: 
            matches = re.findall(r'([^:,]+?):\s*(\d+(?:[.,]\d+)?)%?', dados_texto)
        if not matches:
            matches = re.findall(r'([^:,]+?)\s*:\s*(\d+(?:[.,]\d+)?)%?', dados_texto)
        
        if not matches:
            error_msg = f"Não foi possível extrair dados para o gráfico de pizza '{titulo}' com o texto: '{dados_texto}'"
            logging.warning(error_msg)
            raise ChartGenerationError(error_msg)
        
        # Processar valores
        labels = []
        valores = []
        for nome, valor in matches:
            labels.append(nome.strip())
            try:
                valor_limpo = valor.replace(',', '.')
                valores.append(float(valor_limpo))
            except ValueError as e:
                error_msg = f"Erro na conversão do valor '{valor}' para float: {e}"
                logging.error(error_msg)
                raise ChartGenerationError(error_msg)
        
        # Criação do gráfico com context manager seguro
        with safe_matplotlib_figure(figsize=(7, 7)) as fig:
            ax = fig.add_subplot(111)
            
            # Definir cores baseadas na paleta
            if cores_paleta['principal'] == '#000000':  # Paleta preto e branco
                # Usar escala de cinzas em vez de cores coloridas
                escala_cinza = ['#2D2D2D', '#4A4A4A', '#6B6B6B', '#8C8C8C', '#ADADAD', '#C4C4C4', '#DBDBDB']
                colors = escala_cinza
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
            
            # Título
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
            
            plt.tight_layout()
            
            # Salva em buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='white')
            buf.seek(0)
            
            logging.info(f"Gráfico de pizza criado com sucesso: {titulo}")
            return buf
            
    except ChartGenerationError:
        raise  # Re-raise ChartGenerationError
    except Exception as e:
        error_msg = f"Erro inesperado ao criar gráfico de pizza: {e}"
        logging.error(error_msg, exc_info=True)
        raise ChartGenerationError(error_msg) from e
