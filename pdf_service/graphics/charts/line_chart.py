# Arquivo: graphics/charts/line_chart.py
# Geração de gráficos de linha

import io
import re
import logging
import matplotlib.pyplot as plt
from ..matplotlib_utils import safe_matplotlib_figure
from ...core.exceptions import ChartGenerationError

def criar_grafico_linha(titulo, dados_texto, cores_paleta, unidade=None):
    """
    Cria um gráfico de linha a partir de dados textuais.

    Args:
        titulo (str): Título do gráfico
        dados_texto (str): Dados no formato "serie=valores; labels=nomes" ou "titulo: serie=valores; labels=nomes"
        cores_paleta (dict): Paleta de cores do documento
        unidade (str, optional): Unidade dos valores (ex: "kg", "%", "cabeças")

    Returns:
        io.BytesIO: Buffer com imagem PNG do gráfico ou None se erro

    Example:
        dados = "Vendas=10,20,30,40; labels=Jan,Fev,Mar,Abr"
        buffer = criar_grafico_linha("Vendas Mensais", dados, cores, unidade="R$")
    """
    try:
        # Detectar unidade automaticamente se não fornecida
        unidade_detectada = unidade
        is_percentual = '%' in dados_texto
        if is_percentual and not unidade_detectada:
            unidade_detectada = '%'

        partes = dados_texto.split(';')

        # Suporte para formato com título customizado
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
            error_msg = f"Formato inválido para gráfico de linha. Esperado 2 ou 3 partes, recebido {len(partes)}: {dados_texto}"
            logging.error(error_msg)
            raise ChartGenerationError(error_msg)

        # Parse da série: "nome=valores"
        serie_match = re.match(r'([^=]+)=([^;]+)', serie_parte)
        if not serie_match:
            error_msg = f"Erro ao fazer parse da série do gráfico de linha: {serie_parte}"
            logging.error(error_msg)
            raise ChartGenerationError(error_msg)

        serie_nome = serie_match.group(1).strip()
        valores_str = serie_match.group(2).strip()

        # Parse das labels: "labels=nomes"
        labels_match = re.match(r'([^=]+)=([^;]+)', labels_parte)
        if not labels_match:
            error_msg = f"Erro ao fazer parse das labels do gráfico de linha: {labels_parte}"
            logging.error(error_msg)
            raise ChartGenerationError(error_msg)

        labels_str = labels_match.group(2).strip()

        # Conversão de dados
        try:
            valores = [float(v.strip().replace(',', '.')) for v in valores_str.split(',')]
            labels = [l.strip() for l in labels_str.split(',')]
        except ValueError as e:
            error_msg = f"Erro na conversão de valores numéricos: {e}"
            logging.error(error_msg)
            raise ChartGenerationError(error_msg)

        # Validação de dados
        if len(valores) != len(labels):
            error_msg = f"Número de valores ({len(valores)}) não coincide com labels ({len(labels)}) no gráfico de linha."
            logging.error(error_msg)
            raise ChartGenerationError(error_msg)

        # Criação do gráfico com context manager seguro
        with safe_matplotlib_figure(figsize=(8, 5)) as fig:
            ax = fig.add_subplot(111)

            # Cor da linha baseada na paleta
            cor_linha = '#4299E1' if cores_paleta['principal'] in ['#000000', '#1A1A1A'] else cores_paleta['principal']

            # Plot da linha
            ax.plot(labels, valores,
                    color=cor_linha,
                    marker='o',
                    linewidth=2.5,
                    markersize=6,
                    alpha=0.9)

            # Adicionar área preenchida sob a linha para visual moderno
            ax.fill_between(range(len(labels)), valores, alpha=0.15, color=cor_linha)

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

            # Grid sutil
            ax.grid(True, linestyle='-', alpha=0.2, linewidth=0.5)
            ax.set_axisbelow(True)

            # Remove bordas superiores e direitas
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#E0E0E0')
            ax.spines['bottom'].set_color('#E0E0E0')

            # Anotações nos pontos com unidade
            for i, valor in enumerate(valores):
                # Formatar valor com unidade
                if unidade_detectada == '%':
                    valor_texto = f'{valor:.0f}%' if valor == int(valor) else f'{valor:.1f}%'
                elif unidade_detectada in ['R$', 'US$', '$']:
                    valor_texto = f'{unidade_detectada} {valor:,.0f}' if valor == int(valor) else f'{unidade_detectada} {valor:,.2f}'
                elif unidade_detectada:
                    valor_texto = f'{valor:.0f} {unidade_detectada}' if valor == int(valor) else f'{valor:.1f} {unidade_detectada}'
                else:
                    valor_texto = f'{valor:.0f}' if valor == int(valor) else f'{valor:.1f}'

                ax.annotate(valor_texto, (i, valor),
                           textcoords="offset points",
                           xytext=(0,10), ha='center',
                           fontsize=9, color='black')

            # Formatação dos eixos
            plt.xticks(rotation=0, fontsize=9)
            plt.yticks(fontsize=9)
            plt.tight_layout()

            # Salva em buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='white')
            buf.seek(0)

            logging.info(f"Gráfico de linha criado com sucesso: {titulo}")
            return buf
            
    except ChartGenerationError:
        raise  # Re-raise ChartGenerationError
    except Exception as e:
        error_msg = f"Erro inesperado ao criar gráfico de linha: {e}"
        logging.error(error_msg, exc_info=True)
        raise ChartGenerationError(error_msg) from e
