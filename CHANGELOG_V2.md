# CHANGELOG - Voxy Agro v2.0

**Data:** 12/12/2024

## Visão Geral

A versão 2.0 do Voxy Agro representa uma evolução significativa do produto, focando em:
- Simplificação extrema da experiência do usuário
- Melhoria visual dos PDFs gerados
- Otimização do código e remoção de duplicações

---

## Mudanças no Backend (FastAPI/PDF)

### Refatoração do pdf_generator.py

1. **Remoção de código duplicado**
   - Funções `limpar_html_malformado()` e `limpeza_agressiva_html()` removidas (eram duplicadas)
   - Agora usa apenas imports de `text/html_cleaner.py`

2. **Legendas de imagens funcionando**
   - Corrigido bug: legendas agora aparecem abaixo de cada imagem
   - Estilo: itálico, 9pt, cinza, centralizado

3. **Tamanho adaptativo de imagens**
   - Detecção automática de orientação (paisagem vs retrato)
   - Paisagem: 5.5" x 3.5"
   - Retrato: 3.5" x 5.0"

4. **Novo rodapé Voxy**
   - Texto centralizado: "Documento feito com ajuda do Voxy Agro"
   - Logo do usuário movido para esquerda
   - Estilo: 7pt, cor #999999

5. **Zebra striping em tabelas**
   - Linhas alternadas com fundo #F8F8F8
   - Melhora legibilidade

### Melhorias nos Gráficos

1. **Correção de cores preto-branco**
   - `bar_chart.py`: Agora usa escala de cinzas real
   - `pie_chart.py`: Mesma correção aplicada
   - Escala: ['#2D2D2D', '#4A4A4A', '#6B6B6B', '#8C8C8C', '#ADADAD', '#C4C4C4', '#DBDBDB']

2. **Gráfico de linha com área preenchida**
   - `line_chart.py`: Área semi-transparente (alpha=0.15) sob a linha
   - Visual mais moderno e atraente

### Novo Design System

**Arquivo:** `core/design_system.py`

- Escala tipográfica harmônica (9pt a 22pt)
- Escala de espaçamento (6pt a 36pt)
- Constantes de cores para gráficos
- Configurações de tamanho de imagem

### Atualização do config.py

- Paletas de cores agora incluem campo `escala` com 7 cores graduadas
- Paleta preto_e_branco melhorada (principal #1A1A1A em vez de #000000)

---

## Mudanças no Frontend (Prompt/N8N)

### Novo Prompt v2.0

**Arquivo:** `prompt_v2_n8n.md`

**Fluxo simplificado:**
```
Áudio → Organização automática → 1 confirmação → PDF
```

**Principais mudanças:**
- Removidas múltiplas etapas de confirmação
- Visão do Gemini para análise automática de fotos
- Gráficos só se usuário pedir
- Paleta padrão: azul_escuro
- Mensagem de onboarding amigável

### Instruções para N8N

**Arquivo:** `INSTRUCOES_N8N_V2.md`

- Como atualizar o prompt
- Como adicionar análise de imagem com visão
- Mensagens de status para feedback
- Tratamento de erros

---

## Arquivos Criados

- `pdf_service/core/design_system.py`
- `prompt_v2_n8n.md`
- `INSTRUCOES_N8N_V2.md`
- `CHANGELOG_V2.md`

## Arquivos Modificados

- `pdf_service/pdf_generator.py`
- `pdf_service/core/config.py`
- `pdf_service/graphics/charts/bar_chart.py`
- `pdf_service/graphics/charts/pie_chart.py`
- `pdf_service/graphics/charts/line_chart.py`

---

## Próximos Passos

1. [ ] Deploy no GitHub (novo repositório ou branch v2)
2. [ ] Deploy no Hostinger/EasyPanel
3. [ ] Atualizar prompt no N8N
4. [ ] Configurar visão do Gemini para fotos
5. [ ] Testar fluxo completo no WhatsApp

---

## Métricas Esperadas

- Redução de 50% no número de mensagens até gerar PDF
- Taxa de erro de imagens reduzida (legendas funcionando)
- Visual mais profissional (zebra striping, cores corretas)
- Branding Voxy em todos os documentos
