# Arquivo: graphics/charts/bar_chart.py
# Geração de gráficos de barras

import io
import re
import logging
import matplotlib.pyplot as plt
from ..matplotlib_utils import safe_matplotlib_figure
from ...core.exceptions import ChartGenerationError

def criar_grafico_barras(titulo, dados_texto, cores_paleta, unidade=None):
    """
    Cria um gráfico de barras a partir de dados textuais.

    Args:
        titulo (str): Título do gráfico
        dados_texto (str): Dados no formato "Label1: valor1, Label2: valor2"
        cores_paleta (dict): Paleta de cores do documento
        unidade (str, optional): Unidade dos valores (ex: "kg", "%", "R$", "cabeças")

    Returns:
        io.BytesIO: Buffer com imagem PNG do gráfico ou None se erro

    Example:
        dados = "Vendas: 100, Marketing: 50, Operações: 75"
        buffer = criar_grafico_barras("Orçamento", dados, cores, unidade="R$")
    """
    try:
        # Detectar unidade automaticamente se não fornecida
        unidade_detectada = unidade
        is_percentual = '%' in dados_texto
        if is_percentual and not unidade_detectada:
            unidade_detectada = '%'

        # Parse dos dados usando regex flexível
        matches = re.findall(r'([^:,]+?):\s*(\d+(?:[.,]\d+)?)%?\s*(?:,|$)', dados_texto + ',')
        if not matches:
            matches = re.findall(r'([^:,]+?):\s*(\d+(?:[.,]\d+)?)%?', dados_texto)
        if not matches:
            matches = re.findall(r'([^:,]+?)\s*:\s*(\d+(?:[.,]\d+)?)%?', dados_texto)

        if not matches:
            error_msg = f"Não foi possível extrair dados para o gráfico de barras '{titulo}' com o texto: '{dados_texto}'"
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
        with safe_matplotlib_figure(figsize=(8, 5)) as fig:
            ax = fig.add_subplot(111)

            # Definir cores baseadas na paleta
            if cores_paleta['principal'] in ['#000000', '#1A1A1A']:  # Paleta preto e branco
                # Usar escala de cinzas em vez de cores coloridas
                escala_cinza = ['#2D2D2D', '#4A4A4A', '#6B6B6B', '#8C8C8C', '#ADADAD', '#C4C4C4', '#DBDBDB']
                colors_barras = escala_cinza * (len(valores) // len(escala_cinza) + 1)
            else:
                colors_barras = [
                    cores_paleta['principal'],
                    cores_paleta['secundaria'],
                    cores_paleta['destaque']
                ] * (len(valores) // 3 + 1)

            # Criar barras
            if len(valores) > 1:
                bars = ax.bar(labels, valores, color=colors_barras[:len(valores)], alpha=0.9, width=0.6)
            else:
                bars = ax.bar(labels, valores, color=colors_barras[0], alpha=0.9, width=0.6)

            # Configuração visual
            ax.set_title(titulo, fontsize=14, fontweight='bold', pad=20)

            # Label do eixo Y com unidade
            if unidade_detectada:
                if unidade_detectada == '%':
                    ax.set_ylabel('Percentual (%)', fontsize=10)
                elif unidade_detectada in ['R$', 'US$', '$']:
                    ax.set_ylabel(f'Valor ({unidade_detectada})', fontsize=10)
                else:
                    ax.set_ylabel(f'Quantidade ({unidade_detectada})', fontsize=10)
            else:
                ax.set_ylabel('Quantidade', fontsize=10)

            # Grid minimalista apenas no eixo Y
            ax.grid(axis='y', linestyle='-', alpha=0.2, linewidth=0.5)
            ax.set_axisbelow(True)

            # Remover bordas desnecessárias
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#E0E0E0')
            ax.spines['bottom'].set_color('#E0E0E0')

            # Valores sobre as barras com unidade
            for bar, valor in zip(bars, valores):
                height = bar.get_height()
                # Formatar valor com unidade
                if unidade_detectada == '%':
                    valor_texto = f'{valor:.0f}%' if valor == int(valor) else f'{valor:.1f}%'
                elif unidade_detectada in ['R$', 'US$', '$']:
                    valor_texto = f'{unidade_detectada} {valor:,.0f}' if valor == int(valor) else f'{unidade_detectada} {valor:,.2f}'
                elif unidade_detectada:
                    valor_texto = f'{valor:.0f} {unidade_detectada}' if valor == int(valor) else f'{valor:.1f} {unidade_detectada}'
                else:
                    valor_texto = f'{valor:.0f}' if valor == int(valor) else f'{valor:.1f}'

                ax.text(bar.get_x() + bar.get_width()/2., height + max(valores)*0.02,
                       valor_texto, ha='center', va='bottom', fontweight='normal', fontsize=9, color='black')

            # Formatação dos eixos
            plt.xticks(rotation=0, fontsize=9)
            plt.yticks(fontsize=9)
            plt.tight_layout()

            # Salva em buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='white')
            buf.seek(0)

            logging.info(f"Gráfico de barras criado com sucesso: {titulo}")
            return buf
            
    except ChartGenerationError:
        raise  # Re-raise ChartGenerationError
    except Exception as e:
        error_msg = f"Erro inesperado ao criar gráfico de barras: {e}"
        logging.error(error_msg, exc_info=True)
        raise ChartGenerationError(error_msg) from e
