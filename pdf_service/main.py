import base64
import logging
import os
import time
import asyncio
from fastapi import FastAPI, HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import ValidationError

from .models import ReportData, PDFResponse, VisitReportData, AdubacaoReportData
from .pdf_generator import create_pdf_from_data, preencher_pdf_template, ImageSecurityError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_KEY = os.getenv("API_KEY")

# Validação crítica de segurança na inicialização
if not API_KEY:
    raise ValueError("ERRO CRÍTICO: API_KEY não configurada. Defina a variável de ambiente API_KEY antes de iniciar o serviço.")

# ===============================
# CONFIGURAÇÃO DE RATE LIMITING
# ===============================

# Rate limiter para proteger contra ataques de DoS
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/hour"],  # Limite padrão: 100 requisições por hora por IP
    storage_uri="memory://"  # Usa memória local (para Redis use: redis://localhost:6379)
)

# Timeouts de segurança
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))  # 30 segundos por padrão
PDF_GENERATION_TIMEOUT = int(os.getenv("PDF_GENERATION_TIMEOUT", "60"))  # 60 segundos por padrão

api_description = """
A API de Geração de PDFs da Voxy é uma ferramenta para criar relatórios técnicos de forma automatizada. 🚀

**Principais Funcionalidades:**

*   **Relatórios de Visita (Template Fixo):** Use o endpoint `/gerar-relatorio-visita` para preencher o template padrão da Arizona Nutrição Animal com os dados de uma visita técnica. O layout é fixo, garantindo consistência.
*   **Relatórios Dinâmicos:** Use o endpoint `/gerar-pdf-dinamico` para criar relatórios completos do zero, com suporte para gráficos, tabelas e layouts customizados.

**Autenticação:**

Para usar qualquer um dos endpoints, você precisa fornecer uma chave de API.
Clique no botão **"Authorize"** abaixo e insira sua chave no formato: `Bearer SUA_CHAVE_AQUI`.
"""

app = FastAPI(
    title="Voxy - API de Geração de PDF",
    description=api_description,
    version="1.2.0"  # Atualizada com proteções de recursos
)

# Configurar rate limiting na aplicação
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ===============================
# CONFIGURAÇÃO DE CORS (Cross-Origin Resource Sharing)
# ===============================
# ATENÇÃO: Para produção, defina 'allow_origins' para os domínios específicos
# que consomem sua API, ex: ["https://seusite.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens para desenvolvimento/teste
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ===============================
# MIDDLEWARE DE TIMEOUT E SEGURANÇA
# ===============================

@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """
    Middleware que implementa timeout global para todas as requisições.
    Protege contra requisições que demoram muito e podem travar o servidor.
    """
    start_time = time.time()
    
    try:
        # Timeout específico para endpoints de PDF (mais tempo)
        if request.url.path in ["/gerar-pdf-dinamico", "/gerar-relatorio-visita"]:
            timeout = PDF_GENERATION_TIMEOUT
        else:
            timeout = REQUEST_TIMEOUT
        
        # Executa a requisição com timeout
        response = await asyncio.wait_for(call_next(request), timeout=timeout)
        
        # Log apenas de requisições importantes (não healthchecks)
        process_time = time.time() - start_time
        
        if request.url.path != "/":
            logging.info(f"Requisição {request.url.path} processada em {process_time:.2f}s")
        
        return response
        
    except asyncio.TimeoutError:
        process_time = time.time() - start_time
        client_ip = get_remote_address(request)
        logging.error(f"TIMEOUT: Requisição de {client_ip} para {request.url.path} excedeu {timeout}s (processou por {process_time:.2f}s)")
        
        raise HTTPException(
            status_code=408,
            detail=f"Requisição excedeu o tempo limite de {timeout} segundos. "
                   f"Tente novamente com dados menores ou contate o suporte."
        )
    except Exception as e:
        process_time = time.time() - start_time
        logging.error(f"Erro no middleware após {process_time:.2f}s: {e}")
        raise

auth_scheme = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(auth_scheme)):
    """
    Verificação robusta da API Key com validação de segurança.
    Agora é impossível a API ficar aberta por erro de configuração.
    """
    # Esta verificação é redundante pois já validamos na inicialização,
    # mas mantemos para dupla segurança
    
    if not credentials or not credentials.credentials:
        logging.warning("Tentativa de acesso sem credenciais fornecidas")
        raise HTTPException(
            status_code=401,
            detail="Credenciais de autenticação obrigatórias. Forneça o header Authorization: Bearer <sua_chave>"
        )
    
    if credentials.credentials != API_KEY:
        logging.warning(f"Tentativa de acesso com API Key inválida: {credentials.credentials[:8]}...")
        raise HTTPException(
            status_code=403,
            detail="Chave de API inválida. Verifique suas credenciais."
        )
    
    return credentials.credentials

@app.get("/", summary="Verificação de Saúde", description="Endpoint básico para verificar se o serviço está online.")
def read_root():
    """Endpoint de verificação de saúde."""
    return {"status": "ok", "message": "PDF Generation Service is running."}

@app.get("/health/resources", 
         summary="Monitoramento de Recursos", 
         description="Endpoint para verificar o uso de recursos do sistema.")
def check_resources():
    """
    Endpoint de monitoramento de recursos.
    Retorna informações sobre uso de memória, CPU e limites configurados.
    """
    import psutil
    import sys
    
    try:
        # Informações do processo atual
        process = psutil.Process()
        
        # Uso de memória
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        # Uso de CPU
        cpu_percent = process.cpu_percent(interval=1)
        
        # Informações do sistema
        system_memory = psutil.virtual_memory()
        system_cpu = psutil.cpu_percent(interval=1)
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "process": {
                "pid": process.pid,
                "memory": {
                    "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                    "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                    "percent": round(memory_percent, 2)
                },
                "cpu_percent": round(cpu_percent, 2),
                "threads": process.num_threads(),
                "connections": len(process.connections()),
                "open_files": len(process.open_files())
            },
            "system": {
                "memory": {
                    "total_gb": round(system_memory.total / 1024 / 1024 / 1024, 2),
                    "available_gb": round(system_memory.available / 1024 / 1024 / 1024, 2),
                    "percent_used": system_memory.percent
                },
                "cpu_percent": system_cpu
            },
            "limits": {
                "docker_memory_limit": "1536MB",
                "docker_cpu_limit": "1.5 cores",
                "max_processes": 200,
                "max_files": 2048,
                "request_timeout": REQUEST_TIMEOUT,
                "pdf_generation_timeout": PDF_GENERATION_TIMEOUT
            },
            "rate_limits": {
                "pdf_dinamico": "20/minute per IP",
                "relatorio_visita": "15/minute per IP",
                "default": "100/hour per IP"
            }
        }
        
    except Exception as e:
        logging.error(f"Erro ao verificar recursos: {e}")
        return {
            "status": "error",
            "message": f"Erro ao verificar recursos: {str(e)}",
            "timestamp": time.time()
        }

@app.post("/gerar-pdf-dinamico", 
          response_model=PDFResponse, 
          summary="Gera um Relatório em PDF a partir de um HTML",
          description="Recebe os dados do relatório em JSON e retorna o arquivo PDF codificado em base64.",
          dependencies=[Security(verify_api_key)])
@limiter.limit("20/minute")  # PROTEÇÃO: Máximo 20 PDFs por minuto por IP
async def generate_report(request: Request, report_data: ReportData):
    try:
        data_dict = report_data.dict()

        for key, value in data_dict.items():
            if value is None:
                if key in ['cliente', 'propriedade', 'data_documento', 'recomendacoes', 'conclusoes']:
                    data_dict[key] = ''
                elif key == 'imagens_anexadas':
                    data_dict[key] = []
        
        logging.info(f"Iniciando geração de PDF para: {data_dict.get('titulo_documento')}")
        
        pdf_bytes = create_pdf_from_data(data_dict)

        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        propriedade = data_dict.get('propriedade', 'voxy')
        filename = f"relatorio_{propriedade.replace(' ', '_').lower()}.pdf"

        logging.info(f"PDF gerado com sucesso: {filename}")

        return PDFResponse(filename=filename, pdf_base64=pdf_base64)

    except ImageSecurityError as e:
        logging.error(f"VIOLAÇÃO DE SEGURANÇA - Imagem rejeitada: {e}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Validação de segurança das imagens falhou: {str(e)}"
        )
    except AttributeError as e:
        logging.error(f"Erro de atributo na geração do PDF - Dados inválidos: {e}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Dados inválidos recebidos. Verifique se todos os campos obrigatórios estão preenchidos: {str(e)}"
        )
    except ValueError as e:
        if "Parse error" in str(e):
            logging.error(f"Erro de parsing de HTML na geração do PDF: {e}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail=f"Conteúdo HTML malformado detectado. Verifique se há tags não fechadas no texto: {str(e)}"
            )
        else:
            logging.error(f"Erro de valor na geração do PDF: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Erro de validação: {str(e)}"
            )
    except TypeError as e:
        if "not iterable" in str(e):
            logging.error(f"Erro de tipo (campo não iterável) na geração do PDF: {e}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail=f"Campo inválido detectado. Verifique se todos os campos de lista estão corretos: {str(e)}"
            )
        else:
            logging.error(f"Erro de tipo na geração do PDF: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Erro de tipo: {str(e)}"
            )
    except Exception as e:
        logging.critical(f"Erro inesperado e crítico na geração do PDF: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ocorreu um erro interno ao gerar o PDF: {str(e)}"
        )

@app.post("/gerar-relatorio-visita", 
          response_model=PDFResponse, 
          summary="Cria um Relatório de Visita (Template Arizona)",
          description="Recebe os dados da visita em JSON, preenche o template visual da Arizona Nutrição Animal e retorna o PDF pronto. Ideal para relatórios de rotina.",
          dependencies=[Security(verify_api_key)],
          tags=["Relatórios de Visita"])
@limiter.limit("15/minute")  # PROTEÇÃO: Máximo 15 relatórios de visita por minuto por IP
async def generate_visit_report(request: Request, report_data: VisitReportData):
    try:
        # Extrai os dados de function_args
        data_dict = report_data.function_args.dict()
        
        logging.info(f"Iniciando preenchimento de PDF para: {data_dict.get('nombre_de_la_hacienda')}")
        
        pdf_bytes = preencher_pdf_template(data_dict)

        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        propriedade = data_dict.get('nombre_de_la_hacienda', 'visita')
        filename = f"relatorio_visita_{propriedade.replace(' ', '_').lower()}.pdf"

        logging.info(f"PDF de visita gerado com sucesso: {filename}")

        return PDFResponse(filename=filename, pdf_base64=pdf_base64)

    except ImageSecurityError as e:
        logging.error(f"VIOLAÇÃO DE SEGURANÇA - Imagem rejeitada no template: {e}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Validação de segurança das imagens falhou: {str(e)}"
        )
    except Exception as e:
        logging.critical(f"Erro inesperado na geração do relatório de visita: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ocorreu um erro interno ao gerar o relatório de visita: {str(e)}"
        )

@app.post("/gerar-relatorio-adubacao", 
          response_model=PDFResponse, 
          summary="Cria um Relatório de Adubação e Calagem (Doutor Pasto)",
          description="Recebe os dados de recomendação de adubação em JSON, processa as informações técnicas do Doutor Pasto e retorna o PDF profissional. Ideal para relatórios de fertilidade do solo e correção de pastagens.",
          dependencies=[Security(verify_api_key)],
          tags=["Relatórios de Adubação"])
@limiter.limit("60/minute")  # PROTEÇÃO: Máximo 60 relatórios de adubação por minuto por IP para o evento
async def generate_adubacao_report(request: Request, report_data: AdubacaoReportData):
    try:
        # Extrai os dados de function_args
        data_dict = report_data.function_args.dict()
        
        logging.info(f"Iniciando geração de relatório de adubação para: {data_dict.get('nome_propriedade')}")
        
        # Processa observacoes_tecnicas: converte todo o texto para negrito
        observacoes_original = data_dict.get('observacoes_tecnicas', '')
        if observacoes_original and observacoes_original.strip():
            # Adiciona ** no início e fim para deixar todo o texto em negrito
            observacoes_formatadas = f"**{observacoes_original.strip()}**"
        else:
            observacoes_formatadas = ''
        
        # Converte dados para formato compatível com create_pdf_from_data
        pdf_data = {
            'tipo_documento': 'Relatório de Adubação e Calagem',
            'titulo_documento': f"RELATÓRIO TÉCNICO DE ADUBAÇÃO - {data_dict.get('nome_propriedade', 'PROPRIEDADE')}",
            'cliente': data_dict.get('nome_cliente', ''),
            'propriedade': data_dict.get('nome_propriedade', ''),
            'data_documento': data_dict.get('data_analise', ''),
            'tecnico_nome': data_dict.get('tecnico_responsavel', ''),
            'paleta_cores': 'preto_e_branco',  # Padrão para relatórios de adubação
            'conteudo_principal': data_dict.get('conteudo_principal', ''),
            'recomendacoes': observacoes_formatadas,  # Campo formatado em negrito
            'conclusoes': f"Área: {data_dict.get('area_hectares', 'N/A')} ha | Cultura: {data_dict.get('cultura_pastagem', 'N/A')} | Objetivo: {data_dict.get('objetivo_manejo', 'N/A')}",
            'imagens_anexadas': []  # Sem imagens para relatórios de adubação
        }

        pdf_bytes = create_pdf_from_data(pdf_data)

        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        propriedade = data_dict.get('nome_propriedade', 'adubacao')
        filename = f"relatorio_adubacao_{propriedade.replace(' ', '_').lower()}.pdf"

        logging.info(f"PDF de adubação gerado com sucesso: {filename}")

        return PDFResponse(filename=filename, pdf_base64=pdf_base64)

    except Exception as e:
        logging.critical(f"Erro inesperado na geração do relatório de adubação: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ocorreu um erro interno ao gerar o relatório de adubação: {str(e)}"
        )
