# Instruções para Configurar N8N - Voxy Agro v2.0

## 1. Atualizar Prompt do Agente

1. Abra o workflow no N8N
2. Encontre o node "credenciais"
3. Localize o campo `prompt_do_agente`
4. Substitua pelo conteúdo de `prompt_v2_n8n.md`

## 2. Adicionar Análise de Imagem com Visão

Quando receber tipo "image", antes de salvar no REDIS, envie para Gemini com este prompt:

```
Analise esta imagem de contexto agropecuário brasileiro.
Descreva em 1 frase técnica o que você vê.
Exemplo: "Lote de bovinos Nelore em pastagem de Brachiaria brizantha cv. Marandu"
```

Armazene a descrição junto com base64 no REDIS.

## 3. Adicionar Mensagens de Status

Adicionar nodes para enviar mensagens de feedback:

- Ao receber áudio: "🎤 Recebi! Processando..."
- Após transcrição: "📝 Entendi! Organizando seu relatório..."
- Antes de enviar PDF: "📄 Gerando documento..."

## 4. Tratamento de Erros

Adicionar IF node após HTTP Request de PDF:
- Se sucesso: continua fluxo normal
- Se erro: envia "Ops! Tive um probleminha. Pode tentar de novo? 🔄"

## 5. URL da API

Atualizar URL do endpoint para a nova versão quando deployar:
- Endpoint: `/gerar-pdf-dinamico`
- Manter mesma estrutura de autenticação
