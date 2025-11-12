# Local-AI
- The file `models.yaml` describe the models that are going to be served for inference.
- Because the model files are heavy and the public repositories have restrictions for downloading them programatically, we leave it as a manual step.

## Windows (PowerShell)

- Mistral:
```
Invoke-WebRequest -Uri "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q3_K_M.gguf" -OutFile ".\llm\models\mistral-7b-instruct-v0.2.Q3_K_M.gguf"
```

- TinyLlama:
```
Invoke-WebRequest -Uri "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" -OutFile ".\llm\models\tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
```

- Phi-2:
```
Invoke-WebRequest -Uri "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf" -OutFile ".\llm\models\phi-2.Q4_K_M.gguf"
```

## Linux / Mac

- Mistral:
```
wget "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q3_K_M.gguf" -O ./llm/models/mistral-7b-instruct-v0.2.Q3_K_M.gguf
```

- TinyLlama:
```
wget "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" -O ./llm/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

- Phi-2:
```
wget "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf" -O ./llm/models/phi-2.Q4_K_M.gguf
```

## Model Comparison

| Model | Parameters | File Size | RAM Usage | Best For |
|-------|-----------|-----------|-----------|----------|
| **TinyLlama** | 1.1B | ~700MB | 2-3GB | CPU-only laptops, demos |
| **Phi-2** | 2.7B | ~1.6GB | 3-5GB | Balanced quality/performance |
| **Mistral** | 7B | ~4GB | 8-10GB | High quality, GPU recommended |

> **Recommendation:** Start with TinyLlama if you don't have a GPU. Phi-2 offers better quality if you have 8GB+ RAM.

