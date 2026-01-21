# Deploy Voxy Agro v2.0 no EasyPanel (Hostinger VPS)

## Pré-requisitos

- VPS Hostinger com EasyPanel instalado
- Acesso ao painel do EasyPanel
- Conta GitHub conectada ao EasyPanel

---

## Passo a Passo

### 1. Acessar EasyPanel

1. Acesse seu VPS via browser: `http://SEU_IP:3000` ou o domínio configurado
2. Faça login no EasyPanel

### 2. Criar Novo Serviço

1. Clique em **"Create Service"** ou **"+ Service"**
2. Selecione **"App"** (não template)
3. Preencha:
   - **Name:** `voxy-agro-v2`
   - **Source:** GitHub
   - **Repository:** `diogo-salves/Voxy-Agro-v2`
   - **Branch:** `main`

### 3. Configurar Build

Na aba **Build**:

```
Build Command: (deixar vazio - usa Dockerfile)
Dockerfile Path: pdf_service/Dockerfile
```

### 4. Configurar Variáveis de Ambiente

Na aba **Environment**:

```
API_KEY=SUA_CHAVE_SECRETA_AQUI
REQUEST_TIMEOUT=30
PDF_GENERATION_TIMEOUT=60
```

> **IMPORTANTE:** Use uma API_KEY forte e aleatória (mínimo 32 caracteres)

### 5. Configurar Porta

Na aba **Domains/Ports**:

- **Container Port:** `8000`
- **Protocol:** HTTP
- (Opcional) Adicionar domínio personalizado

### 6. Deploy

1. Clique em **"Deploy"** ou **"Save & Deploy"**
2. Aguarde o build (~2-5 minutos na primeira vez)
3. Verifique os logs para erros

### 7. Verificar Deploy

Após deploy concluído:

```bash
# Health check básico
curl https://SEU_DOMINIO/

# Deve retornar:
# {"status":"healthy","message":"Voxy PDF Service v2.0"}

# Health check completo
curl https://SEU_DOMINIO/health/resources
```

---

## Configurar N8N para Usar a Nova API

### 1. Atualizar URL da API

No N8N, encontre o node HTTP Request que chama a API e atualize:

```
URL: https://SEU_DOMINIO/gerar-pdf-dinamico
```

### 2. Atualizar Headers

```
X-API-Key: SUA_NOVA_API_KEY
Content-Type: application/json
```

### 3. Atualizar Prompt do Agente

1. Vá no node "credenciais" do workflow
2. Substitua o `prompt_do_agente` pelo conteúdo de `prompt_v2_n8n.md`

### 4. Configurar Visão do Gemini (Análise de Fotos)

Adicionar um node para enviar imagens ao Gemini com visão antes de catalogar:

```javascript
// Prompt para análise de imagem
const visionPrompt = `Analise esta imagem de contexto agropecuário brasileiro.
Descreva em 1 frase técnica o que você vê.
Exemplo: "Lote de bovinos Nelore em pastagem de Brachiaria brizantha cv. Marandu"`;
```

### 5. Adicionar Mensagens de Status

Adicionar nodes para feedback ao usuário:

| Evento | Mensagem |
|--------|----------|
| Recebeu áudio | 🎤 Recebi! Processando... |
| Após transcrição | 📝 Entendi! Organizando seu relatório... |
| Gerando PDF | 📄 Gerando documento... |
| Erro | Ops! Tive um probleminha. Pode tentar de novo? 🔄 |

---

## Testar Fluxo Completo

### Teste 1: Via Curl (API Direta)

```bash
curl -X POST https://SEU_DOMINIO/gerar-pdf-dinamico \
  -H "Content-Type: application/json" \
  -H "X-API-Key: SUA_API_KEY" \
  -d '{
    "titulo_documento": "Relatório de Teste",
    "tipo_documento": "Visita Técnica",
    "cliente": "Cliente Teste",
    "propriedade": "Fazenda Teste",
    "data_documento": "12/12/2024",
    "conteudo_principal": "Teste de integração v2.0.\n\nPastagem em boas condições.",
    "recomendacoes": "Continuar monitoramento.",
    "paleta_cores": "verde_agronegocio"
  }'
```

### Teste 2: Via WhatsApp

1. Envie uma mensagem de áudio descrevendo uma visita técnica
2. Verifique se recebe as mensagens de status
3. Confirme geração do PDF
4. Verifique visual do PDF (cabeçalho, zebra, assinatura)

---

## Troubleshooting

### Erro 401 Unauthorized
- Verificar se `API_KEY` está configurada corretamente
- Verificar header `X-API-Key` no N8N

### Erro 500 Internal Server Error
- Ver logs no EasyPanel: `Logs` → `voxy-agro-v2`
- Geralmente é problema de JSON mal formatado

### PDF não gera
- Verificar se JSON do Gemini está correto
- Testar endpoint direto com curl
- Verificar timeout (aumentar se necessário)

### Imagens não aparecem
- Verificar se base64 está correto
- Verificar tamanho (máx 5MB por imagem)
- Verificar formato (PNG, JPG, JPEG)

---

## URLs de Referência

| Ambiente | URL |
|----------|-----|
| GitHub | https://github.com/diogo-salves/Voxy-Agro-v2 |
| API Docs | https://SEU_DOMINIO/docs |
| Health | https://SEU_DOMINIO/health/resources |

---

*Última atualização: 12/12/2024*
