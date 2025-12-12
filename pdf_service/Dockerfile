# Arquivo: Dockerfile (Versão Final e de Produção)

# 1. Usar uma imagem oficial do Python como imagem base
# ATUALIZADO: Python 3.12 (versão mais recente com todas as melhorias de performance e segurança)
FROM python:3.12-slim

# 2. Definir o diretório de trabalho dentro do container
WORKDIR /app

# 3. Copiar o arquivo de dependências para o container
COPY ./pdf_service/requirements.txt .

# 4. Instalar dependências do sistema e Python
# Otimizações de segurança e performance
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Dependências necessárias para compilação
    build-essential \
    libffi-dev \
    pkg-config \
    # Dependências para fontes e gráficos
    libfreetype6-dev \
    libpng-dev \
    libjpeg-dev \
    # Curl para healthcheck
    curl \
    # Limpeza de cache para reduzir tamanho da imagem
    && rm -rf /var/lib/apt/lists/* \
    # Atualizar pip para versão mais recente
    && pip install --no-cache-dir --upgrade pip setuptools wheel \
    # Instalar dependências Python
    && pip install --no-cache-dir -r requirements.txt \
    # Remover dependências de build para reduzir tamanho (opcional)
    && apt-get remove -y build-essential \
    && apt-get autoremove -y \
    && apt-get clean

# 5. Copiar o código da aplicação e as imagens estáticas
COPY ./pdf_service/ /app/pdf_service/
COPY ./itens_png_voxy/ /app/itens_png_voxy/

# 6. Criar usuário não-root para segurança
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app \
    && mkdir -p /tmp/matplotlib \
    && chmod 777 /tmp/matplotlib
USER appuser

# 7. Definir variáveis de ambiente para otimização
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MPLCONFIGDIR=/tmp/matplotlib \
    MPLBACKEND=Agg

# 8. Expor a porta que a aplicação vai rodar
EXPOSE 8000

# 9. Healthcheck para monitoramento
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# 10. Definir o comando para iniciar a aplicação
# Comando otimizado com configurações de produção
CMD ["python", "-m", "uvicorn", "pdf_service.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--log-level", "info"]