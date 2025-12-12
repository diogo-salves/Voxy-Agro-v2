# Arquivo: graphics/chart_factory.py
# Factory para criação de gráficos

import logging
from .charts.bar_chart import criar_grafico_barras
from .charts.pie_chart import criar_grafico_pizza
from .charts.line_chart import criar_grafico_linha
from ..core.exceptions import ChartGenerationError

class ChartFactory:
    """
    Factory para criação de diferentes tipos de gráficos.
    
    Centraliza a lógica de criação e fornece interface unificada.
    """
    
    SUPPORTED_CHART_TYPES = {
        'barras': criar_grafico_barras,
        'pizza': criar_grafico_pizza,
        'linha': criar_grafico_linha,
        # Aliases
        'bar': criar_grafico_barras,
        'pie': criar_grafico_pizza,
        'line': criar_grafico_linha,
    }
    
    @classmethod
    def create_chart(cls, tipo_grafico, titulo, dados_texto, cores_paleta, unidade=None):
        """
        Cria um gráfico do tipo especificado.

        Args:
            tipo_grafico (str): Tipo do gráfico ('barras', 'pizza', 'linha')
            titulo (str): Título do gráfico
            dados_texto (str): Dados em formato texto
            cores_paleta (dict): Paleta de cores do documento
            unidade (str, optional): Unidade dos valores (ex: "kg", "%", "cabeças")

        Returns:
            io.BytesIO: Buffer com imagem PNG do gráfico

        Raises:
            ChartGenerationError: Se tipo não suportado ou erro na criação
        """
        tipo_normalizado = tipo_grafico.lower().strip()

        if tipo_normalizado not in cls.SUPPORTED_CHART_TYPES:
            supported_types = ', '.join(cls.SUPPORTED_CHART_TYPES.keys())
            error_msg = f"Tipo de gráfico '{tipo_grafico}' não suportado. Tipos disponíveis: {supported_types}"
            logging.error(error_msg)
            raise ChartGenerationError(error_msg)

        chart_creator = cls.SUPPORTED_CHART_TYPES[tipo_normalizado]

        try:
            # Passa unidade apenas para gráficos que suportam (barras, linha)
            if tipo_normalizado in ['barras', 'bar', 'linha', 'line']:
                return chart_creator(titulo, dados_texto, cores_paleta, unidade=unidade)
            else:
                return chart_creator(titulo, dados_texto, cores_paleta)
        except ChartGenerationError:
            raise  # Re-raise ChartGenerationError
        except Exception as e:
            error_msg = f"Erro inesperado ao criar gráfico {tipo_grafico}: {e}"
            logging.error(error_msg, exc_info=True)
            raise ChartGenerationError(error_msg) from e
    
    @classmethod
    def get_supported_types(cls):
        """
        Retorna lista de tipos de gráfico suportados.
        
        Returns:
            list: Lista de tipos suportados
        """
        return list(cls.SUPPORTED_CHART_TYPES.keys())
    
    @classmethod
    def is_supported_type(cls, tipo_grafico):
        """
        Verifica se um tipo de gráfico é suportado.
        
        Args:
            tipo_grafico (str): Tipo a verificar
            
        Returns:
            bool: True se suportado, False caso contrário
        """
        return tipo_grafico.lower().strip() in cls.SUPPORTED_CHART_TYPES

# Função de conveniência para compatibilidade com código existente
def criar_grafico(titulo, dados_texto, cores_paleta, tipo_grafico='barras', unidade=None):
    """
    Função de conveniência que mantém compatibilidade com o código existente.

    Args:
        titulo (str): Título do gráfico
        dados_texto (str): Dados em formato texto
        cores_paleta (dict): Paleta de cores
        tipo_grafico (str): Tipo do gráfico (padrão: 'barras')
        unidade (str, optional): Unidade dos valores (ex: "kg", "%", "cabeças")

    Returns:
        io.BytesIO: Buffer com imagem PNG do gráfico ou None se erro
    """
    try:
        return ChartFactory.create_chart(tipo_grafico, titulo, dados_texto, cores_paleta, unidade=unidade)
    except ChartGenerationError as e:
        logging.error(f"Erro na criação do gráfico: {e}")
        return None
    except Exception as e:
        logging.error(f"Erro inesperado na criação do gráfico: {e}", exc_info=True)
        return None
