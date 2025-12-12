# Arquivo: models.py

from pydantic import BaseModel, Field, validator, constr
from typing import List, Optional, Dict, Any
from enum import Enum

# ===============================
# ENUMS DE VALIDAÇÃO CRÍTICOS
# ===============================

class PaletaCores(str, Enum):
    """
    Paletas de cores válidas para documentos.
    Previne erros silenciosos com paletas inexistentes.
    """
    AZUL_ESCURO = "azul_escuro"
    VERDE_AGRONEGOCIO = "verde_agronegocio"
    LARANJA_COMERCIAL = "laranja_comercial"
    ROXO_CORPORATIVO = "roxo_corporativo"
    PRETO_E_BRANCO = "preto_e_branco"

class TipoDocumento(str, Enum):
    """
    Tipos de documento válidos.
    Garante consistência na categorização.
    """
    RELATORIO_TECNICO = "Relatório Técnico"
    RELATORIO_VISITA = "Relatório de Visita"
    RELATORIO_PRODUCAO = "Relatório de Produção"
    RELATORIO_ANALISE = "Relatório de Análise"
    DOCUMENTO_TECNICO = "Documento Técnico"
    LAUDO_TECNICO = "Laudo Técnico"
    RELATORIO_ADUBACAO_CALAGEM = "Relatório de Adubação e Calagem"

# ===============================
# CONSTANTES DE VALIDAÇÃO
# ===============================

# Limites de tamanho para campos de texto
MAX_TITULO_LENGTH = 200
MAX_NOME_LENGTH = 100
MAX_CLIENTE_LENGTH = 100
MAX_PROPRIEDADE_LENGTH = 100
MAX_CONTEUDO_LENGTH = 50000  # 50KB de texto
MAX_LEGENDA_LENGTH = 500

# Modelo para os dados de uma imagem anexada
class ImagemAnexada(BaseModel):
    """
    Modelo validado para imagens anexadas.
    Inclui validações de segurança e integridade.
    """
    id: Optional[int] = Field(None, ge=0, le=999, description="ID numérico da imagem (0-999)")
    base64: constr(min_length=100, max_length=10_000_000) = Field(
        ..., 
        description="Dados da imagem em base64 (100 chars a 10MB)"
    )
    legenda: Optional[constr(max_length=MAX_LEGENDA_LENGTH)] = Field(
        "", 
        description=f"Legenda da imagem (máximo {MAX_LEGENDA_LENGTH} caracteres)"
    )
    
    @validator('base64')
    def validar_base64(cls, v):
        """Validação básica de formato base64"""
        if not v:
            raise ValueError("Base64 não pode estar vazio")
        
        # Verifica se contém apenas caracteres base64 válidos
        import re
        if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', v):
            raise ValueError("Formato base64 inválido")
        
        return v
    
    @validator('legenda')
    def validar_legenda(cls, v):
        """Validação de legenda"""
        if v and len(v.strip()) == 0:
            return ""  # Converte string vazia para string vazia limpa
        return v.strip() if v else ""

# Modelo para detalhes do proprietário/assinatura
class ProprietarioDetalhes(BaseModel):
    """
    Detalhes validados do proprietário/assinante.
    """
    nome: Optional[constr(min_length=2, max_length=MAX_NOME_LENGTH, strip_whitespace=True)] = Field(
        None,
        description=f"Nome completo da pessoa que assina (2-{MAX_NOME_LENGTH} caracteres)"
    )
    formacao: Optional[constr(min_length=2, max_length=100, strip_whitespace=True)] = Field(
        None,
        description="Formação acadêmica ou técnica (2-100 caracteres)"
    )
    numero: Optional[constr(max_length=50, strip_whitespace=True)] = Field(
        None,
        description="Número de contato do proprietário/assinante (máximo 50 caracteres)"
    )
    email: Optional[constr(max_length=100, strip_whitespace=True)] = Field(
        None,
        description="Email de contato do proprietário/assinante (máximo 100 caracteres)"
    )
    cargo: Optional[constr(max_length=100, strip_whitespace=True)] = Field(
        None,
        description="Cargo ou função do assinante (máximo 100 caracteres)"
    )

    class Config:
        extra = "ignore"  # Compatibilidade: ignora campos extras do Gemini

# Modelo principal para os dados do relatório que chegam na requisição
class ReportData(BaseModel):
    """
    Modelo otimizado para function calls do Gemini.
    Aceita TODOS os campos da function declaration.
    """
    # Campos obrigatórios da function declaration
    tipo_documento: str = Field(..., description="Tipo de documento")
    titulo_documento: str = Field(..., description="Título do documento")
    tecnico_nome: str = Field(..., description="Nome do técnico responsável")
    paleta_cores: str = Field(default="preto_e_branco", description="Paleta de cores")
    conteudo_principal: str = Field(..., description="Conteúdo principal do documento")
    
    # TODOS os campos opcionais da function declaration
    cliente: Optional[str] = None
    propriedade: Optional[str] = None
    data_documento: Optional[str] = None
    recomendacoes: Optional[str] = None
    conclusoes: Optional[str] = None
    objetivo: Optional[str] = None
    cronograma: Optional[str] = None
    metodologia: Optional[str] = None
    dados_numericos: Optional[str] = None
    tecnico_empresa: Optional[str] = None
    valores_comerciais: Optional[str] = None
    condicoes_comerciais: Optional[str] = None
    observacoes_adicionais: Optional[str] = None
    proprietario_detalhes: Optional[ProprietarioDetalhes] = None
    
    imagens_anexadas: Optional[List[ImagemAnexada]] = Field(
        default_factory=list,
        description="Lista de imagens anexadas"
    )

    # CONFIGURAÇÃO DE SEGURANÇA CRÍTICA
    class Config:
        # TEMPORÁRIO: Permite campos extras para compatibilidade com Gemini
        extra = "ignore"  # Ignora campos extras (mais seguro que "allow")
        # Permite que enums sejam enviados como strings
        use_enum_values = True
        # Validação rigorosa de tipos
        validate_assignment = True

    # Validadores customizados
    @validator('imagens_anexadas', pre=True)
    def converter_null_para_lista_vazia(cls, v):
        """Converte null para lista vazia"""
        if v is None:
            return []
        return v
    
    @validator('paleta_cores', pre=True)
    def validar_paleta_cores(cls, v):
        """Validação flexível de paleta - compatível com Gemini function calls"""
        if v is None:
            return "preto_e_branco"  # Padrão
        
        # Importa a função de validação centralizada
        from .core.config import validate_palette_name
        return validate_palette_name(v)

# Modelo para a resposta da API em caso de sucesso
class PDFResponse(BaseModel):
    filename: str = Field(..., description="Nome do arquivo PDF gerado.")
    pdf_base64: str

# Modelo para function_args (dados internos)
class FunctionArgs(BaseModel):
    """
    Argumentos validados para relatórios de visita.
    Modelo específico para integração com function calls.
    """
    nombre_de_la_hacienda: Optional[constr(max_length=MAX_PROPRIEDADE_LENGTH, strip_whitespace=True)] = Field(
        "", 
        description=f"Nome da fazenda ou propriedade (máximo {MAX_PROPRIEDADE_LENGTH} caracteres)"
    )
    propietario: Optional[constr(max_length=MAX_NOME_LENGTH, strip_whitespace=True)] = Field(
        "", 
        description=f"Nome do proprietário da fazenda (máximo {MAX_NOME_LENGTH} caracteres)"
    )
    fecha_de_visita: Optional[constr(max_length=50, strip_whitespace=True)] = Field(
        "", 
        description="Data da visita (ex: '20 de Agosto de 2025', máximo 50 caracteres)"
    )
    tecnicos_responsables: Optional[constr(max_length=200, strip_whitespace=True)] = Field(
        "", 
        description="Nome do(s) técnico(s) responsável(is) (máximo 200 caracteres)"
    )
    responsables_presentes: Optional[constr(max_length=200, strip_whitespace=True)] = Field(
        "", 
        description="Responsáveis presentes na visita (máximo 200 caracteres)"
    )
    
    # Campo principal que contém todo o conteúdo do relatório
    contenido_principal: Optional[constr(max_length=MAX_CONTEUDO_LENGTH, strip_whitespace=True)] = Field(
        "", 
        description=f"Conteúdo completo do relatório de visita (máximo {MAX_CONTEUDO_LENGTH} caracteres)"
    )
    
    # Detalhes para assinatura (obrigatório)
    proprietario_detalhes: ProprietarioDetalhes = Field(
        ..., 
        description="Detalhes obrigatórios da pessoa que assina o relatório"
    )
    
    imagens_anexadas: Optional[List[ImagemAnexada]] = Field(
        default_factory=list,
        description="Lista de imagens anexadas ao relatório"
    )
    
    class Config:
        extra = "ignore"  # Compatibilidade: ignora campos extras do Gemini
        validate_assignment = True  # Validação rigorosa
    
    @validator('imagens_anexadas', pre=True)
    def converter_null_para_lista_vazia(cls, v):
        """Converte null para lista vazia"""
        if v is None:
            return []
        return v
    
    @validator('contenido_principal')
    def validar_conteudo_principal(cls, v):
        """Validação do conteúdo principal"""
        if v and len(v.strip()) < 10:
            raise ValueError("Conteúdo principal deve ter pelo menos 10 caracteres")
        return v.strip() if v else ""

# Modelo principal que aceita o novo formato com function_args
class VisitReportData(BaseModel):
    """
    Modelo principal validado para relatórios de visita.
    Wrapper seguro para function_args vindos de IA.
    """
    function_args: FunctionArgs = Field(
        ..., 
        description="Argumentos validados do relatório de visita"
    )
    
    class Config:
        extra = "ignore"  # Compatibilidade: ignora campos extras do Gemini
        validate_assignment = True  # Validação rigorosa
        json_schema_extra = {
            "example": {
                "function_args": {
                    "nombre_de_la_hacienda": "Fazenda Santa Clara",
                    "propietario": "Sr. João da Silva", 
                    "fecha_de_visita": "15 de Setembro de 2024",
                    "tecnicos_responsables": "Dr. Carlos Andrade (Arizona)",
                    "responsables_presentes": "Sr. Mário (Gerente)",
                    "contenido_principal": "Introducción General de la Visita:\nVisita de rotina para acompanhar o lote de recria e ajustar a dieta de terminação.\n\nConclusión:\nRecomenda-se o reparo do portão do curral e agendar próxima visita em 60 dias.",
                    "proprietario_detalhes": {
                        "nome": "Dr. Carlos Andrade",
                        "formacao": "Médico Veterinário",
                        "cargo": "Técnico Arizona"
                    },
                    "imagens_anexadas": []
                }
            }
        }

# ===============================
# MODELOS PARA DOUTOR PASTO - RELATÓRIOS DE ADUBAÇÃO
# ===============================

# Modelo para argumentos do Doutor Pasto
class AdubacaoFunctionArgs(BaseModel):
    """
    Argumentos validados para relatórios de adubação e calagem.
    Modelo específico para integração com Doutor Pasto function calls.
    """
    nome_propriedade: constr(max_length=MAX_PROPRIEDADE_LENGTH, strip_whitespace=True) = Field(
        ..., 
        description=f"Nome da fazenda ou propriedade (máximo {MAX_PROPRIEDADE_LENGTH} caracteres)"
    )
    nome_cliente: constr(max_length=MAX_NOME_LENGTH, strip_whitespace=True) = Field(
        ..., 
        description=f"Nome completo do proprietário/cliente (máximo {MAX_NOME_LENGTH} caracteres)"
    )
    tecnico_responsavel: constr(max_length=MAX_NOME_LENGTH, strip_whitespace=True) = Field(
        ..., 
        description=f"Nome do técnico/engenheiro agrônomo responsável (máximo {MAX_NOME_LENGTH} caracteres)"
    )
    data_analise: Optional[constr(max_length=50, strip_whitespace=True)] = Field(
        "", 
        description="Data da análise no formato DD/MM/AAAA (máximo 50 caracteres)"
    )
    area_hectares: Optional[str] = Field(
        "", 
        description="Área em hectares da propriedade"
    )
    cultura_pastagem: Optional[constr(max_length=100, strip_whitespace=True)] = Field(
        "", 
        description="Espécie de capim/pastagem (máximo 100 caracteres)"
    )
    objetivo_manejo: Optional[constr(max_length=50, strip_whitespace=True)] = Field(
        "", 
        description="Objetivo: Implantação ou Manutenção (máximo 50 caracteres)"
    )
    
    # Campo principal que contém todo o relatório de adubação
    conteudo_principal: constr(max_length=MAX_CONTEUDO_LENGTH, strip_whitespace=True) = Field(
        ..., 
        description=f"Conteúdo completo do relatório de adubação e calagem (máximo {MAX_CONTEUDO_LENGTH} caracteres)"
    )
    
    observacoes_tecnicas: Optional[constr(max_length=2000, strip_whitespace=True)] = Field(
        "", 
        description="Observações técnicas adicionais (máximo 2000 caracteres)"
    )
    
    class Config:
        extra = "ignore"  # Compatibilidade: ignora campos extras do Gemini
        validate_assignment = True  # Validação rigorosa
    
    @validator('conteudo_principal')
    def validar_conteudo_principal(cls, v):
        """Validação do conteúdo principal"""
        if v and len(v.strip()) < 50:
            raise ValueError("Conteúdo principal deve ter pelo menos 50 caracteres")
        return v.strip() if v else ""
    
    @validator('area_hectares', pre=True)
    def converter_area_para_string(cls, v):
        """Converte números para string automaticamente"""
        if v is None:
            return ""
        if isinstance(v, (int, float)):
            return str(v)
        return str(v).strip() if v else ""

# Modelo principal para relatórios de adubação
class AdubacaoReportData(BaseModel):
    """
    Modelo principal validado para relatórios de adubação do Doutor Pasto.
    Wrapper seguro para function_args vindos de IA.
    """
    function_args: AdubacaoFunctionArgs = Field(
        ..., 
        description="Argumentos validados do relatório de adubação"
    )
    
    class Config:
        extra = "ignore"  # Compatibilidade: ignora campos extras do Gemini
        validate_assignment = True  # Validação rigorosa
        json_schema_extra = {
            "example": {
                "function_args": {
                    "nome_propriedade": "Fazenda Boa Esperança",
                    "nome_cliente": "Sr. José Silva", 
                    "tecnico_responsavel": "Eng. Agr. Dr. Pasto",
                    "data_analise": "20/09/2024",
                    "area_hectares": "50",
                    "cultura_pastagem": "Brachiaria brizantha cv. Marandu",
                    "objetivo_manejo": "Manutenção",
                    "conteudo_principal": "## DIAGNÓSTICO DO SOLO\n\nA análise revelou níveis baixos de fósforo...\n\n## RECOMENDAÇÕES DE CALAGEM\n\nAplicar 2.5 t/ha de calcário dolomítico...\n\n[TABELA: Recomendação de Fertilizantes\nNutriente|Dose (kg/ha)|Época\nNitrogênio|150|3 aplicações\nFósforo|80|Plantio]",
                    "observacoes_tecnicas": "Recomenda-se acompanhamento técnico durante a implementação das recomendações."
                }
            }
        }