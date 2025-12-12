# 🔄 HANDOVER TÉCNICO - VOXY PDF GENERATOR

## 📝 **VERSÃO: 2.1.0**

### 📅 **DATA DA ATUALIZAÇÃO: 23 de Setembro de 2025**

## 📋 CONTEXTO DO PROJETO

### 🎯 **O QUE É:**
- **Sistema de geração automatizada de PDFs** para agronegócio brasileiro
- **Integração N8N + Gemini 2.5 Flash** via function calls
- **API REST** que recebe JSON do Gemini e gera PDFs profissionais
- **Foco:** Relatórios técnicos, visitas, propostas comerciais, relatórios de adubação

### 🔧 **STACK TECNOLÓGICO:**
- **Backend:** FastAPI + Python 3.12
- **PDF Engine:** ReportLab + Matplotlib  
- **Deploy:** EasyPanel Hostinger (Docker)
- **IA:** Gemini 2.5 Flash function calls via N8N
- **Validação:** Pydantic 2.x
- **Rate Limiting:** SlowAPI (usando armazenamento em memória local)

### 🏗️ **ARQUITETURA (VISÃO GERAL):**
```
N8N → Gemini Function Call (JSON) → FastAPI (Validação/Processamento) → PDF Engine (Geração) → PDF Base64
```

## 📁 ESTRUTURA ATUALIZADA DO PROJETO

```
pdf_generator/
├── pdf_service/                    # Core da aplicação
│   ├── main.py                    # API endpoints + CORS + rate limiting
│   ├── models.py                  # Modelos Pydantic (atualizados com `TipoDocumento`)
│   ├── pdf_generator.py           # Engine PDF (corrigido e otimizado)
│   ├── core/                      # Configurações centrais
│   │   ├── config.py             # Constantes, paletas (validação refatorada), limites de segurança
│   │   └── exceptions.py         # Exceções customizadas
│   ├── utils/                     # Utilitários
│   │   ├── fonts.py              # Gestão de fontes Unicode
│   │   └── __init__.py
│   ├── text/                      # Processamento de texto
│   │   ├── unicode_handler.py    # Correção de caracteres especiais
│   │   ├── html_cleaner.py       # Limpeza e sanitização HTML
│   │   ├── markdown_processor.py # Conversão Markdown → HTML
│   │   └── __init__.py
│   ├── graphics/                  # Sistema de gráficos
│   │   ├── matplotlib_utils.py   # Context manager seguro
│   │   ├── chart_factory.py      # Factory unificado de gráficos
│   │   ├── charts/               # Gráficos especializados
│   │   │   ├── bar_chart.py
│   │   │   ├── pie_chart.py
│   │   │   └── line_chart.py
│   │   └── __init__.py
│   ├── requirements.txt           # Dependências (redis removido)
│   ├── Dockerfile                 # Python 3.12 + segurança (caminho de imagens corrigido)
│   └── README.md                  # Documentação técnica do serviço
├── itens_png_voxy/                # ✅ CORRIGIDO - Assets visuais para templates
│   ├── imagens_arizona/          # Imagens para template Arizona
│   │   ├── arcofinal.png
│   │   ├── legenda.png
│   │   ├── linhavermelha.png
│   │   └── logoprincipal.png
│   └── imagens_dr_pasto/         # Imagens para template Dr. Pasto
│       └── logo_drPasto.png
├── docker-compose.yml             # Configuração Docker simplificada
├── function_call_estrutura.json   # Exemplo de payload para Gemini
├── prompt_unificado_completo.md   # Prompt para Gemini (unificado)
├── voxy_prompt_agro.md           # Prompt especializado (agro)
├── voxy_prompt_arizona.md        # Prompt especializado (Arizona)
├── voxy_prompt_dr_pasto_v2.md    # Prompt especializado (Dr. Pasto)
└── README.md                     # Documentação geral do projeto
```

## 🚨 CORREÇÕES CRÍTICAS E OTIMIZAÇÕES IMPLEMENTADAS (v2.1.0)

### 🖼️ **1. CAMINHOS DE IMAGENS (CRÍTICO - CORRIGIDO)**
**PROBLEMA:** Referências incorretas às imagens da pasta `itens_png_voxy` (`imagens_arizona`) no `pdf_generator.py` e caminho errado no `Dockerfile`.
**IMPACTO:** Imagens não carregavam, PDFs incompletos em produção.
**SOLUÇÃO:**
- Ajustados os caminhos em `pdf_generator.py` para incluir subpastas.
- Corrigida a instrução `COPY` no `pdf_service/Dockerfile` para `itens_png_voxy`.

### 🔒 **2. SEGURANÇA DA API_KEY (OTIMIZADO)**
**PROBLEMA:** Validação redundante da `API_KEY` na função `verify_api_key` do `main.py`.
**IMPACTO:** Código desnecessário, menor clareza.
**SOLUÇÃO:** Removido o bloco de validação redundante, pois a chave já é verificada criticamente na inicialização da aplicação.

### 🚀 **3. RATE LIMITING (AJUSTADO PARA EVENTO)**
**PROBLEMA:** `Rate limit` de `10/minute` muito restritivo para o endpoint de adubação em cenário de evento com 30 usuários.
**IMPACTO:** Usuários seriam bloqueados com `429 Too Many Requests`.
**SOLUÇÃO:** Aumentado o `rate limit` para `/gerar-relatorio-adubacao` para `60/minute` no `main.py`.

### 🗑️ **4. DEPENDÊNCIA REDIS (REMOVIDA)**
**PROBLEMA:** Dependência `redis` no `requirements.txt` sem uso (`storage_uri="memory://"` para `slowapi`).
**IMPACTO:** Aumento desnecessário do tamanho da imagem Docker e tempo de build.
**SOLUÇÃO:** Removida a linha `redis>=5.0.1` de `pdf_service/requirements.txt`.

### 🧹 **5. LIMPEZA DE CÓDIGO (OTIMIZADO)**
**PROBLEMA:**
- Função `converter_markdown_para_html_OLD_REMOVIDO` obsoleta em `pdf_generator.py`.
- Importações de `corrigir_caracteres_especiais` dentro da função `criar_tabela`.
**IMPACTO:** Código poluído, menor manutenibilidade e clareza.
**SOLUÇÃO:**
- Removida a função obsoleta.
- Movida a importação de `corrigir_caracteres_especiais` para o topo do `pdf_generator.py`.

### 🎨 **6. CONSISTÊNCIA DE PALETAS E TIPOS DE DOCUMENTO (AJUSTADO)**
**PROBLEMA:**
- Mapeamento redundante de paletas em `core/config.py` e `models.py`.
- `TipoDocumento` Enum incompleto, não incluindo `Relatório de Adubação e Calagem`.
**IMPACTO:** Inconsistências na validação, duplicação de lógica.
**SOLUÇÃO:**
- Refatorada a função `validate_palette_name` em `core/config.py`.
- O validador de `paleta_cores` em `models.py` agora usa a função centralizada de `core/config.py`.
- Adicionado `RELATORIO_ADUBACAO_CALAGEM` ao `TipoDocumento` Enum em `models.py`.

### 🌐 **7. CORS (NOVO - IMPLEMENTADO)**
**PROBLEMA:** Ausência de `CORSMiddleware` pode bloquear requisições de frontends em diferentes domínios.
**IMPACTO:** Falha na comunicação API-Frontend em produção.
**SOLUÇÃO:** Adicionado `CORSMiddleware` no `main.py` (com `allow_origins=["*"]` para desenvolvimento, **deve ser restrito em produção**).

## 🤖 INTEGRAÇÃO GEMINI FUNCTION CALLS

### 📋 **FUNCTION DECLARATION ATUALIZADA:**
O Gemini usa function `criar_pdf` com os seguintes campos (modelos `ReportData`, `VisitReportData`, `AdubacaoReportData`):

**Campos comuns (ReportData):**
- **Obrigatórios:** `tipo_documento`, `titulo_documento`, `conteudo_principal`, `tecnico_nome`, `paleta_cores`
- **Opcionais:** `cliente`, `objetivo`, `conclusoes`, `cronograma`, `metodologia`, `propriedade`, `recomendacoes`, `data_documento`, `dados_numericos`, `tecnico_empresa`, `valores_comerciais`, `condicoes_comerciais`, `observacoes_adicionais`, `imagens_anexadas` (lista de `ImagemAnexada`)

**Campos específicos para Relatório de Visita (VisitReportData -> FunctionArgs):**
- **Obrigatórios:** `proprietario_detalhes` (com `nome`, `formacao`, `cargo`)
- **Opcionais:** `nombre_de_la_hacienda`, `propietario`, `fecha_de_visita`, `tecnicos_responsables`, `responsables_presentes`, `contenido_principal`, `imagens_anexadas`

**Campos específicos para Relatório de Adubação (AdubacaoReportData -> AdubacaoFunctionArgs):**
- **Obrigatórios:** `nome_propriedade`, `nome_cliente`, `tecnico_responsavel`, `conteudo_principal`
- **Opcionais:** `data_analise`, `area_hectares`, `cultura_pastagem`, `objetivo_manejo`, `observacoes_tecnicas`

### 🎨 **PALETAS VÁLIDAS:**
```
"azul_escuro", "verde_agronegocio", "laranja_comercial", 
"roxo_corporativo", "preto_e_branco" (alias "preto_branco" também aceito)
```

### 📊 **RECURSOS SUPORTADOS NO `conteudo_principal`:**
- **Gráficos:** `[GRAFICO_BARRAS: título: dados]`, `[GRAFICO_PIZZA: título: dados]`, `[GRAFICO_LINHA: título: série=valores; labels=nomes]`
- **Imagens:** `[IMAGEM:ID]` para inserção por ID (requer `imagens_anexadas` no payload)
- **Tabelas:** `[TABELA: título\nheader|data\nrow1|row2]`
- **Markdown:** Suporte completo (títulos, listas, formatação)
- **Separador Horizontal:** `---` ou `***` (três hífens ou asteriscos)

## ✅ REFATORAÇÃO E OTIMIZAÇÕES CONCLUÍDAS COM SUCESSO (v2.1.0)

### 🎉 **RESULTADOS ALCANÇADOS:**
- **Código mais limpo e robusto**: Eliminação de redundâncias e código morto.
- **Segurança aprimorada**: CORS configurado, validação de chaves e imagens robusta.
- **Performance ajustada**: `Rate limit` configurado para diferentes endpoints.
- **Consistência de dados**: Enums e validações de paleta centralizadas.
- **Infraestrutura Docker correta**: Caminho de imagens no `Dockerfile` corrigido.

### 🏗️ **ESTRUTURA DA APLICAÇÃO (APÓS v2.1.0):**
```
pdf_generator/
├── main.py
├── models.py
├── pdf_generator.py
├── core/
├── utils/
├── text/
├── graphics/
├── requirements.txt
└── Dockerfile
```

### 🧪 **TESTES DE VALIDAÇÃO REALIZADOS (v2.1.0):**
- ✅ **API Key e CORS**: Autenticação e acesso multi-origem funcionando.
- ✅ **Rate Limiting**: Limites por endpoint ativos e ajustados.
- ✅ **Geração de PDF (Adubação)**: Endpoint funcionando com novo `rate limit`.
- ✅ **Caminhos de Imagem**: Imagens carregando corretamente nos PDFs.
- ✅ **Limpeza de Código**: Funções obsoletas e redundâncias removidas.
- ✅ **Consistência de Modelos**: Validações de paletas e tipos de documento aprimoradas.

## 🔗 DEPENDÊNCIAS CRÍTICAS

### 📦 **Requirements.txt ATUALIZADO (v2.1.0):**
```
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
reportlab>=4.0.7
matplotlib>=3.8.2
PyPDF2>=3.0.1
fonttools>=4.47.0
Pillow>=10.1.0
slowapi>=0.1.9
psutil>=5.9.6
```

### 🔑 **Variáveis de Ambiente CRÍTICAS:**
```
API_KEY=sua_chave_secreta_aqui (OBRIGATÓRIA)
REQUEST_TIMEOUT=30 (opcional, em segundos)
PDF_GENERATION_TIMEOUT=60 (opcional, em segundos)
```

## 🚀 INSTRUÇÕES DE DEPLOY PARA PRODUÇÃO

1.  **Configurar API_KEY:** Defina a variável de ambiente `API_KEY` no seu ambiente Hostinger EasyPanel. **NUNCA use chaves de teste em produção!**
2.  **Verificar CORS:** Se sua aplicação frontend estiver em um domínio diferente, ajuste `allow_origins` no `main.py` para listar apenas os domínios permitidos (ex: `["https://seu-frontend.com"]`).
3.  **Atualizar Imagem Docker:** Reconstrua e faça deploy da sua imagem Docker no EasyPanel para que as últimas mudanças sejam aplicadas. O EasyPanel geralmente detecta as alterações no `Dockerfile` e `docker-compose.yml` e reconstrói automaticamente.
4.  **Monitoramento:** Acompanhe as métricas de CPU, memória e tempo de resposta do seu contêiner no EasyPanel, especialmente sob carga, para garantir a estabilidade.

## 🎯 PRÓXIMAS TAREFAS SUGERIDAS (Roadmap)

1.  **Testes de Carga (Load Testing):** Simule cenários de alto tráfego com 30+ usuários para validar a capacidade real do seu deploy e ajustar os recursos no EasyPanel se necessário.
2.  **Documentação OpenAPI (Swagger):** Atualize as descrições dos endpoints e exemplos no `main.py` para refletir as últimas mudanças e facilitar a integração.
3.  **Logging e Monitoramento Avançado:** Implemente um sistema de logging mais robusto (ex: para um serviço centralizado) e explore métricas mais detalhadas.
4.  **Testes Unitários e de Integração:** Crie testes automatizados para os módulos e endpoints críticos para garantir a qualidade do código a longo prazo.
5.  **Revisão de Prompts:** Certifique-se de que todos os arquivos `voxy_prompt_*.md` estejam alinhados com as capacidades e validações atuais da API.

---

**📝 Formato baseado em [Keep a Changelog](https://keepachangelog.com/)**
