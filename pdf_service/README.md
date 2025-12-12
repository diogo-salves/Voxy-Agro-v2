# Voxy PDF Generation Service

API REST especializada para geração automatizada de relatórios técnicos profissionais para o **agronegócio brasileiro**. Integrada com **Gemini 2.5 Flash** via function calls, construída com FastAPI, ReportLab e Matplotlib para criar documentos de alta qualidade.

## 🚀 Funcionalidades

- ✅ **Integração com Gemini 2.5 Flash** - Function calls automáticas
- ✅ **Dois tipos de relatório**: Dinâmicos personalizáveis + Template Arizona fixo
- ✅ **Gráficos automáticos** - Barras, pizza e linha com dados inteligentes
- ✅ **5 paletas profissionais** - Azul escuro, verde agronegócio, laranja comercial, roxo corporativo, preto e branco
- ✅ **Sistema inteligente de imagens** - Inserção por ID com posicionamento flexível
- ✅ **Processamento Markdown** - Conteúdo estruturado para PDF profissional
- ✅ **Autenticação por API Key** - Segurança empresarial
- ✅ **Suporte a CORS** - Integração flexível com frontends
- ✅ **Rate Limiting** - Proteção contra sobrecarga de requisições
- ✅ **Logs detalhados** - Monitoramento e rastreamento de operações

## 📋 Pré-requisitos

- Python 3.12+
- pip (gerenciador de pacotes Python)

## 🛠️ Instalação

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd pdf_service
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Execute a aplicação
```bash
uvicorn main:app --reload
```

A API estará disponível em: `http://localhost:8000`

## 🐳 Executando com Docker

### 1. Construa a imagem
```bash
docker build -t voxy-pdf-service .
```

### 2. Execute o container
```bash
docker run -p 8000:8000 voxy-pdf-service
```

## 📚 Endpoints da API

### Base URL: `http://localhost:8000`

| Método | Endpoint | Descrição | Autenticação |
|--------|----------|-----------|--------------|
| GET | `/` | Verificação de saúde da API | ❌ |
| POST | `/gerar-pdf-dinamico` | Relatórios customizáveis do zero | ✅ |
| POST | `/gerar-relatorio-visita` | Template fixo Arizona Nutrição Animal com suporte a gráficos | ✅ |

### 🎯 Diferenças entre os Endpoints

**`/gerar-pdf-dinamico`:**
- Relatórios completamente personalizáveis
- Suporte a gráficos, tabelas e layouts customizados
- Ideal para análises técnicas diversas

**`/gerar-relatorio-visita`:**
- Template visual fixo da Arizona Nutrição Animal
- Layout padronizado com logo e elementos visuais
- Ideal para relatórios de rotina e visitas técnicas

## 📖 Documentação da API

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔧 Exemplos de Uso

### 1. Relatório Dinâmico (Personalizado)

```bash
curl -X POST "http://localhost:8000/gerar-pdf-dinamico" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SUA_CHAVE_SECRETA_AQUI" \
  -d '{
    "tipo_documento": "Relatório Técnico de Produtividade",
    "titulo_documento": "Análise Zootécnica - Fazenda Santa Clara",
    "tecnico_nome": "Dr. João Silva - CRMV 12345",
    "paleta_cores": "preto_e_branco",
    "conteudo_principal": "## ANÁLISE ZOOTÉCNICA\n\nO rebanho apresentou excelente performance durante o período avaliado.\n\n[GRAFICO_BARRAS: Produtividade por Lote: Lote A: 1.2, Lote B: 1.4, Lote C: 1.1]\n\n[IMAGEM:0]",
    "cliente": "Fazenda Santa Clara",
    "propriedade": "Unidade Norte",
    "data_documento": "15/01/2024",
    "recomendacoes": "Recomenda-se ajuste no protocolo nutricional do Lote C.",
    "conclusoes": "A propriedade demonstra potencial para crescimento de 15%.",
    "imagens_anexadas": [
      {
        "id": 0,
        "base64": "iVBORw0KGgoAAAANSUhEUg...",
        "legenda": "Vista geral do rebanho - Lote A"
      }
    ]
  }'
```

### 2. Relatório de Visita (Template Arizona)

```bash
curl -X POST "http://localhost:8000/gerar-relatorio-visita" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SUA_CHAVE_SECRETA_AQUI" \
  -d '{
    "function_args": {
      "nombre_de_la_hacienda": "Fazenda Santa Clara",
      "propietario": "Sr. João Silva",
      "fecha_de_visita": "15/01/2024",
      "tecnicos_responsables": "Dr. Carlos (Arizona)",
      "responsables_presentes": "Sr. Mário (Gerente)",
      "contenido_principal": "## INTRODUCCIÓN GENERAL\n\nVisita de rutina para evaluación del lote de recría...\n\n## LECTURA DE COMEDERO\n\nConsumo adecuado observado...",
      "proprietario_detalhes": {
        "nome": "Dr. Carlos Andrade",
        "formacao": "Médico Veterinário",
        "cargo": "Técnico Arizona"
      },
      "imagens_anexadas": []
    }
  }'
```

## 🤖 Integração com Gemini 2.5 Flash

O sistema utiliza **function calls** do Gemini para gerar conteúdo estruturado automaticamente:

### 🔄 Fluxo de Processamento

1. **Técnico fornece dados** → Gemini 2.5 Flash
2. **IA gera function call** → JSON estruturado  
3. **API processa dados** → Validação Pydantic
4. **Engine converte** → PDF profissional

### 📋 Estruturas de Dados

#### Relatório Dinâmico (`/gerar-pdf-dinamico`)

```json
{
  "tipo_documento": "string",
  "titulo_documento": "string", 
  "tecnico_nome": "string",
  "paleta_cores": "azul_escuro | verde_agronegocio | laranja_comercial | roxo_corporativo | preto_e_branco",
  "conteudo_principal": "string (Markdown)",
  "cliente": "string (opcional)",
  "propriedade": "string (opcional)", 
  "data_documento": "string (opcional)",
  "recomendacoes": "string (opcional)",
  "conclusoes": "string (opcional)",
  "imagens_anexadas": [
    {
      "id": "number (ID numérico para [IMAGEM:id])",
      "base64": "string (codificação base64)",
      "legenda": "string (legenda profissional)"
    }
  ]
}
```

#### Relatório de Visita (`/gerar-relatorio-visita`)

Este endpoint utiliza template fixo da Arizona Nutrição Animal com **suporte completo a gráficos** para visualização de dados de visita técnica.

```json
{
  "function_args": {
    "nombre_de_la_hacienda": "string",
    "propietario": "string",
    "fecha_de_visita": "string",
    "tecnicos_responsables": "string", 
    "responsables_presentes": "string",
    "contenido_principal": "string (Markdown estruturado)",
    "proprietario_detalhes": {
      "nome": "string",
      "formacao": "string",
      "cargo": "string"
    },
    "imagens_anexadas": []
  }
}
```

**Exemplo com Gráficos no Relatório de Visita:**
```json
{
  "function_args": {
    "nombre_de_la_hacienda": "Fazenda San Miguel",
    "propietario": "Sr. Carlos Mendoza",
    "fecha_de_visita": "15/01/2024",
    "tecnicos_responsables": "Dr. Ana Silva (Arizona)",
    "responsables_presentes": "Sr. Carlos (Proprietário) e Luis (Capataz)",
    "contenido_principal": "## LECTURA DE COMEDERO\n\nSe observó consumo adecuado en todos los lotes evaluados.\n\n[GRAFICO_BARRAS: Consumo por Lote: Lote A: 2.1, Lote B: 1.8, Lote C: 2.3]\n\n## EVALUACIÓN ANIMAL\n\nDistribución del rebaño por categorías:\n\n[GRAFICO_PIZZA: Categorías Animales: Vacas: 120, Novilhas: 80, Bezerros: 95]",
    "proprietario_detalhes": {
      "nome": "Dr. Ana Silva",
      "formacao": "Médica Veterinária",
      "cargo": "Técnica Arizona"
    },
    "imagens_anexadas": []
  }
}
```

### Resposta da API

```json
{
  "filename": "relatorio_sitio_sao_joao.pdf",
  "pdf_base64": "JVBERi0xLjQKJcOkw7zDtsO..."
}
```

## 🎨 Paletas de Cores Disponíveis

### 1. Preto e Branco (padrão)
- **Principal**: #000000
- **Secundária**: #333333
- **Destaque**: #666666
- **Fundo**: #F8F8F8

### 2. Azul Escuro
- **Principal**: #1A365D
- **Secundária**: #2D3748
- **Destaque**: #4299E1
- **Fundo**: #F7FAFC

### 3. Verde Agronegócio
- **Principal**: #1B4332
- **Secundária**: #2D5E3E
- **Destaque**: #40916C
- **Fundo**: #F1F8E9

### 4. Laranja Comercial
- **Principal**: #C05621
- **Secundária**: #9C4221
- **Destaque**: #F6AD55
- **Fundo**: #FFFAF0

### 5. Roxo Corporativo
- **Principal**: #44337A
- **Secundária**: #553C9A
- **Destaque**: #9F7AEA
- **Fundo**: #FAF5FF

## 📊 Geração de Gráficos e Imagens

O sistema suporta a criação automática de 3 tipos de gráficos e a inserção de imagens através de tags especiais no conteúdo.

### Inserindo Imagens

O sistema oferece duas formas de inserir imagens:

#### 1. Método com ID (Recomendado)
Use IDs numéricos para ter controle total sobre onde cada imagem aparece, independentemente da ordem na lista.

```json
"conteudo_principal": "Análise inicial [IMAGEM:1]. Conclusão com a primeira foto [IMAGEM:0].",
"imagens_anexadas": [
  { "id": 0, "base64": "...", "legenda": "Primeira foto enviada" },
  { "id": 1, "base64": "...", "legenda": "Segunda foto enviada" }
]
```

Neste exemplo, a segunda imagem (id: 1) aparece primeiro no texto, e a primeira imagem (id: 0) aparece depois.

#### 2. Método Sequencial (Compatibilidade)
Para manter compatibilidade, ainda é possível usar a tag `[IMAGEM]` sem ID. Neste caso, as imagens são inseridas na ordem em que aparecem na lista.

```json
"conteudo_principal": "Primeira foto aqui [IMAGEM]. Segunda foto aqui [IMAGEM].",
"imagens_anexadas": [
  { "base64": "...", "legenda": "Primeira Foto" },
  { "base64": "...", "legenda": "Segunda Foto" }
]
```

### Gráfico de Barras e Pizza

A sintaxe é a mesma para ambos os gráficos, mudando apenas a tag.

- **Tag:** `[GRÁFICO_BARRAS: ...]` ou `[GRÁFICO_PIZZA: ...]`
- **Formato:** `Título do Gráfico: Item1: valor1, Item2: valor2, ...`

```
[GRÁFICO_BARRAS: Produtividade por Cultura: Milho: 85, Soja: 92, Trigo: 78]
[GRÁFICO_PIZZA: Distribuição do Rebanho: Vacas: 80, Novilhas: 40, Bezerros: 65]
```

### Gráfico de Linha

Este gráfico possui uma sintaxe específica para definir a série de dados e os rótulos do eixo X.

- **Tag:** `[GRÁFICO_LINHA: ...]`
- **Formato 1 (Título Externo):** `Título Principal: NomeDaSerie=v1,v2,v3; NomeDoEixoX=label1,label2,label3`
- **Formato 2 (Título Embutido):** `: Título Embutido; NomeDaSerie=v1,v2,v3; NomeDoEixoX=label1,label2,label3`

**Exemplos:**
```
[GRÁFICO_LINHA: Crescimento Mensal: Produção=120,135,142; Meses=Jan,Fev,Mar]
[GRÁFICO_LINHA: : GMD Mensal (kg/dia); GMD=1.1,1.3,1.4; Meses=Jan,Fev,Mar]
```

## 📁 Estrutura do Projeto

```
pdf_service/
├── main.py             # Ponto de entrada da API FastAPI
├── pdf_generator.py    # Lógica de geração de PDF e gráficos
├── models.py           # Modelos de dados (Pydantic)
├── requirements.txt    # Dependências Python
├── Dockerfile          # Configuração Docker
└── README.md          # Documentação
```

## 🎨 Características dos PDFs Gerados

- **Formato**: A4 com margens profissionais
- **Cabeçalho**: Título principal com fundo colorido
- **Seções**: Títulos de seção com bordas coloridas
- **Gráficos**: Gráficos de barras gerados automaticamente
- **Informações**: Box com dados da propriedade, cliente e técnico
- **Cores**: Paletas personalizadas para diferentes tipos de documento
- **Tipografia**: Helvetica para máxima legibilidade

## 🔒 Segurança e Monitoramento

### 🛡️ Autenticação por API Key

Os endpoints protegidos requerem autenticação via API Key:

```bash
-H "Authorization: Bearer SUA_CHAVE_SECRETA_AQUI"
```

**Endpoints protegidos:**
- ✅ `/gerar-pdf-dinamico` 
- ✅ `/gerar-relatorio-visita`

**Endpoint público:**
- ❌ `/` (health check)

### 📊 Sistema de Logs

O sistema possui **logging robusto** com 4 níveis:

| Nível | Uso | Exemplos |
|-------|-----|----------|
| **INFO** | Sucessos | PDF gerado, gráfico criado |
| **WARNING** | Avisos | Fonte não encontrada, imagem faltante |
| **ERROR** | Erros | Parse de dados, processamento |
| **CRITICAL** | Falhas críticas | Erros inesperados do sistema |

### 🔍 Monitoramento Implementado

- ✅ **Geração de PDF**: Início, fim e tempo de processamento
- ✅ **Processamento de Imagens**: Inserção por ID rastreada  
- ✅ **Geração de Gráficos**: Cada gráfico criado é logado
- ✅ **Tratamento de Erros**: 21 tipos específicos capturados

## 🚀 Deploy em Produção

### ☁️ Ambiente Atual: VPS Hostinger

O sistema está **atualmente hospedado em VPS Hostinger** com:

- **Ambiente**: Cloud VPS escalável
- **Containerização**: Docker + Docker Compose
- **Volumes**: Sistema stateless (sem volumes definidos)
- **Escalabilidade**: Horizontal conforme demanda

### 🐳 Configuração Docker Compose

```yaml
version: '3.8'
services:
  voxy-pdf-service:
    build:
      context: .
      dockerfile: pdf_service/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - API_KEY=${API_KEY}
      - HOST=0.0.0.0
      - PORT=8000
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 📈 Planos de Escalabilidade

**🎯 Expansão Planejada:**
- **Múltiplos Nichos**: Expansão além do agronegócio
- **Novos Setores**: Veterinária, consultoria ambiental, engenharia
- **Arquitetura Modular**: Sistema preparado para novos prompts e templates

## 🛠️ Stack Tecnológico

| Componente | Tecnologia | Finalidade |
|------------|------------|------------|
| **IA Engine** | Gemini 2.5 Flash | Function calls para geração de conteúdo |
| **API Framework** | FastAPI | REST API moderna e rápida |
| **PDF Engine** | ReportLab | Geração profissional de PDFs |
| **Gráficos** | Matplotlib | Visualizações e charts |
| **Validação** | Pydantic | Validação robusta de dados |
| **Servidor** | Uvicorn | Servidor ASGI de alta performance |
| **Containerização** | Docker | Deploy e portabilidade |
| **Infraestrutura** | VPS Hostinger | Hospedagem cloud escalável |

## 📊 Métricas do Sistema

### 📈 Complexidade do Código

| Arquivo | Linhas | Funcionalidades Principais |
|---------|--------|----------------------------|
| `pdf_generator.py` | 969 | Engine PDF, gráficos, imagens, Unicode |
| `main.py` | 147 | Endpoints API, autenticação, logs |
| `models.py` | 96 | Validação Pydantic, schemas |

### 🎯 Recursos Implementados

- ✅ **44 pontos de logging** distribuídos no sistema
- ✅ **21 tipos de erro** específicos tratados
- ✅ **5 paletas de cores** profissionais
- ✅ **3 tipos de gráficos** (barras, pizza, linha)
- ✅ **Sistema inteligente** de posicionamento de imagens
- ✅ **Processamento Unicode** avançado com fallbacks

## 🤝 Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🆘 Suporte

Se você encontrar algum problema ou tiver dúvidas, abra uma issue no repositório. 