# 🔷 Beacon

**Navegador Controlado por Voz para Pessoas Cegas**

## Hackathon Devs de Impacto!

---

## 💡 O Problema

Navegar na web é uma tarefa visual por design. Para pessoas cegas, a experiência atual significa:
- Ouvir cada elemento da página em ordem sequencial
- Navegar por anúncios, popups e botões sem rótulos
- Não ter contexto sobre o que a página realmente oferece
- Dificuldade em identificar ações importantes rapidamente

## 🎯 Nossa Solução: Beacon

Beacon não apenas **lê** páginas web — ele as **compreende**. Transformamos páginas visuais complexas em menus falados simples que tornam a navegação intuitiva e eficiente.

### Como Funciona

1. **Analisa** a página — identifica se é uma loja, artigo, formulário, checkout, etc.
2. **Resume** informações-chave — apresenta o conteúdo mais importante primeiro
3. **Simplifica** ações — converte interações complexas em um menu numerado:
   - "1. Adicionar ao carrinho"
   - "2. Ler avaliações"
   - "3. Ver especificações técnicas"
4. **Age em seu nome** — clica botões, preenche formulários, rola e navega baseado na sua intenção
5. **Mantém você seguro** — sempre confirma antes de ações de alto risco como pagamentos ou publicações

## 🚀 Instalação Rápida

```bash
# Instalar dependências
uv sync

# Configurar chaves de API no .env

# Executar Beacon
uv run main.py
```

### Flags Úteis

- `--agent-steps` — número máximo de passos do agente por ação (padrão: 8)
- `--load-wait` — segundos de espera após navegação (padrão: 4.0)

## 🎮 Como Usar

### Comandos por Voz ou Teclado

Beacon entende linguagem natural:

- **Navegação**: "Abrir amazon.com" / "Ir para YouTube"
- **Compreensão**: "O que é esta página?" / "Resumir"
- **Ações**: "Adicionar ao carrinho" / "Fazer número 2" / "Ler artigo"
- **Interação**: "Pesquisar fones sem fio" / "Voltar"
- **Nova página**: "Nova página" → Beacon pedirá a URL

### Segurança em Primeiro Lugar

Beacon **sempre pedirá confirmação** antes de:
- ✅ Enviar informações de pagamento
- ✅ Publicar conteúdo
- ✅ Fazer compras
- ✅ Deletar qualquer coisa
- ✅ Enviar mensagens ou emails

## 🏗️ Arquitetura Técnica

```
browser-use/
├── main.py     # Ponto de entrada CLI
├── beacon.py   # Orquestração do aplicativo
└── tools.py    # Motor de análise de páginas e interface de voz
```

### Componentes Principais

1. **PageUnderstandingEngine** — Usa GPT-4o-mini para analisar DOM e extrair ações relevantes
2. **VoiceInterface** — TTS (text-to-speech) e STT (speech-to-text) via OpenAI
3. **BeaconApp** — Coordena navegação, resumos e delegação de tarefas ao agente
4. **browser-use Agent** — Executa ações autônomas na página atual

### Dependências

- `browser-use>=0.9.1` — Automação de navegador com agente
- `openai>=1.52.0` — API para análise, TTS e STT
- `sounddevice` + `numpy` — (Opcional) Captura de áudio por microfone

### Requisitos

- Python 3.13+
- Google Chrome instalado localmente
- Chave da API OpenAI
- macOS/Linux com `afplay`/`ffplay` para reprodução de áudio (ou prints apenas)

## 🎨 Princípios de Design

1. **Intenção sobre interação** — Usuários dizem o que querem, não como fazer
2. **Consciência de contexto** — Cada página é analisada por tipo e propósito
3. **Hierarquia de informação** — Conteúdo mais importante primeiro
4. **Segurança por padrão** — Confirmação para qualquer ação arriscada
5. **Comunicação natural** — Fale naturalmente, Beacon entende

## � Impacto Esperado

- **Redução de tempo** para completar tarefas comuns na web
- **Aumento de autonomia** para usuários cegos em compras, leitura e formulários online
- **Experiência mais digna** — sem precisar ouvir todo o "ruído" visual de uma página

## 🛠️ Melhorias Futuras

- Detecção por palavra de ativação (wake-word)
- STT em streaming para respostas mais rápidas
- Suporte multi-abas
- Verificações de segurança baseadas em regras (detecção de formulários de pagamento)
- Integração com dados ARIA e landmarks para priorização ainda melhor

## 👥 Equipe

Desenvolvido para o **Hackathon Devs de Impacto** por [seu nome/equipe].

## 📄 Licença

[Adicione sua licença aqui]

---

**Beacon** — Porque a web deve ser acessível para todos. 🌟
