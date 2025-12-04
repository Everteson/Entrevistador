# Entrevistador IA

Sistema de entrevistas técnicas com IA usando reconhecimento de voz, LLM e síntese de voz.

## 🚀 Características

- **8 Perfis de Entrevistador**: Junior, Pleno, Senior, DevOps, Frontend, Backend, Fullstack, Data Engineer
- **Reconhecimento de Voz**: Fast Whisper com suporte CUDA
- **IA Conversacional**: OpenRouter GPT-4o com sistema de tags customizado
- **Síntese de Voz**: ElevenLabs v3 com vozes naturais
- **Interface Moderna**: Design premium com animações suaves
- **Avaliação Final**: Análise completa com pontos fortes, fracos e nota

## 📋 Pré-requisitos

- Python 3.10+
- CUDA (para Fast Whisper)
- API Keys:
  - OpenRouter (para GPT-4o)
  - ElevenLabs (para TTS)

## 🔧 Instalação

### 1. Clone o repositório

```bash
cd Entrevistador
```

### 2. Instale as dependências

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure as API Keys

Edite `backend/config.json` e adicione suas chaves:

```json
{
  "api_keys": {
    "openrouter": "SUA_CHAVE_OPENROUTER",
    "elevenlabs": "SUA_CHAVE_ELEVENLABS"
  },
  "tts": {
    "voice_id": "SEU_VOICE_ID_ELEVENLABS"
  }
}
```

## 🎯 Como Usar

### 1. Inicie o backend

```bash
cd backend
python main.py
```

O servidor estará rodando em `http://localhost:8000`

### 2. Abra o frontend

Abra `frontend/index.html` no seu navegador ou use um servidor local:

```bash
cd frontend
python -m http.server 3000
```

Acesse `http://localhost:3000`

### 3. Configure a entrevista

1. Selecione o **perfil do entrevistador** (Junior, Pleno, Senior, etc.)
2. Escolha a **stack** (Backend, Frontend, Fullstack, etc.)
3. Clique em **Iniciar Entrevista**

### 4. Durante a entrevista

- **Falar**: Clique no botão de microfone e fale sua resposta
- **Código**: Use o campo de texto para digitar código (evita erros de transcrição)
- **Ouvir**: A IA responderá com voz e exibirá perguntas na tela

### 5. Finalizar

Clique em **Finalizar Entrevista** para receber uma avaliação completa com:
- ✅ Pontos fortes
- ⚠️ Pontos fracos
- 💡 Sugestões de melhoria
- 📊 Nota final (0-10)

## 🏗️ Arquitetura

### Backend (FastAPI)

```
backend/
├── main.py                 # Aplicação FastAPI principal
├── config.json             # Configurações e API keys
├── requirements.txt        # Dependências Python
└── modules/
    ├── stt.py             # Fast Whisper (Speech-to-Text)
    ├── tts.py             # ElevenLabs (Text-to-Speech)
    ├── llm.py             # OpenRouter GPT-4o
    ├── profiles.py        # Perfis de entrevistador
    └── context_manager.py # Gerenciamento de contexto
```

### Frontend (HTML/CSS/JS)

```
frontend/
├── index.html             # Interface principal
├── css/
│   └── styles.css        # Design system premium
└── js/
    ├── app.js            # Lógica da aplicação
    └── markdown.js       # Renderização de markdown
```

## 🎨 Perfis de Entrevistador

| Perfil | Foco | Nível |
|--------|------|-------|
| **Junior** | Fundamentos, sintaxe básica | Iniciante |
| **Pleno** | Arquitetura, padrões, frameworks | Intermediário |
| **Senior** | Sistemas distribuídos, trade-offs | Avançado |
| **DevOps** | Infraestrutura, CI/CD, cloud | Especializado |
| **Frontend** | UI/UX, frameworks, performance | Especializado |
| **Backend** | APIs, bancos de dados, serviços | Especializado |
| **Fullstack** | Frontend + Backend integrado | Generalista |
| **Data Engineer** | Pipelines, ETL, big data | Especializado |

## 🔄 Fluxo de Funcionamento

1. **Usuário fala** → Áudio capturado
2. **Fast Whisper** → Transcreve para texto
3. **Backend** → Envia para OpenRouter GPT-4o
4. **LLM responde** com tags:
   - `<falar>` → Texto para ElevenLabs (voz)
   - `<codigo>` → Conteúdo visual (tela)
5. **Frontend** → Exibe código e reproduz áudio
6. **Ciclo continua** até finalização

## 🛠️ API Endpoints

- `GET /` - Health check
- `GET /api/profiles` - Lista perfis disponíveis
- `POST /api/interview/start` - Inicia nova entrevista
- `POST /api/transcribe` - Transcreve áudio
- `POST /api/interview/message` - Envia mensagem ao LLM
- `POST /api/synthesize` - Gera áudio (TTS)
- `POST /api/interview/evaluate` - Gera avaliação final
- `GET /api/session/{id}` - Info da sessão
- `DELETE /api/session/{id}` - Deleta sessão

## ⚙️ Configurações

### Fast Whisper

```json
"stt": {
  "model_size": "base",      // tiny, base, small, medium, large-v3
  "device": "cuda",          // cuda ou cpu
  "compute_type": "float16", // float16, int8
  "language": "pt"           // Português
}
```

### LLM (OpenRouter)

```json
"llm": {
  "model": "openai/gpt-4o",
  "temperature": 0.7,
  "max_tokens": 1000,
  "context_window": 6        // Últimas 6 trocas
}
```

### ElevenLabs TTS

```json
"tts": {
  "voice_id": "SEU_VOICE_ID",
  "model_id": "eleven_multilingual_v2",
  "stability": 0.5,
  "similarity_boost": 0.75
}
```

## 📝 Licença

MIT

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

---

**Desenvolvido com ❤️ usando FastAPI, Fast Whisper, OpenRouter e ElevenLabs**
