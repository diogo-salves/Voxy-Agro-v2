# Arquivo: graphics/matplotlib_utils.py
# Utilitários seguros para matplotlib

import logging
import matplotlib.pyplot as plt
from contextlib import contextmanager

@contextmanager
def safe_matplotlib_figure(*args, **kwargs):
    """
    Context manager que garante que figuras matplotlib sejam sempre fechadas.
    
    Evita memory leaks críticos que podem derrubar o servidor em produção.
    
    Args:
        *args, **kwargs: Argumentos passados para plt.figure()
        
    Yields:
        matplotlib.figure.Figure: Figura criada
        
    Example:
        with safe_matplotlib_figure(figsize=(10, 6)) as fig:
            ax = fig.add_subplot(111)
            ax.plot([1, 2, 3], [1, 4, 9])
            # Figura será fechada automaticamente
    """
    fig = None
    try:
        fig = plt.figure(*args, **kwargs)
        yield fig
    except Exception as e:
        logging.error(f"Erro durante criação de gráfico: {e}")
        raise
    finally:
        # SEMPRE fecha a figura, mesmo se houver erro
        if fig is not None:
            plt.close(fig)
            logging.debug(f"Figura matplotlib fechada corretamente (ID: {fig.number})")
        else:
            # Fallback de segurança: fecha todas as figuras
            plt.close('all')
            logging.warning("Fallback: todas as figuras matplotlib foram fechadas")

def setup_matplotlib_backend():
    """
    Configura o backend matplotlib para uso em servidor.
    
    Define o backend 'Agg' que não requer display gráfico.
    """
    import matplotlib
    matplotlib.use('Agg')
    logging.info("Backend matplotlib configurado para 'Agg' (headless)")

def cleanup_matplotlib():
    """
    Limpa todos os recursos matplotlib.
    
    Fecha todas as figuras abertas e limpa cache.
    """
    plt.close('all')
    plt.clf()
    plt.cla()
    logging.debug("Recursos matplotlib limpos")
