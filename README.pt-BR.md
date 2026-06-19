<sub>[English](README.md) · **Português 🇧🇷**</sub>

# 🎬 TikTok Transcriber

> Transforme um link do TikTok **ou um perfil inteiro** em transcrições limpas em Markdown, cada uma
> carimbada com as métricas do post: visualizações, curtidas, comentários, reposts, **salvamentos** e data.

Feito para cair direto no [Obsidian](https://obsidian.md), mas a saída é só Markdown
puro, então funciona em qualquer lugar. Sem login, sem cookies, sem automação de navegador.

![python](https://img.shields.io/badge/python-3.9%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![whisper](https://img.shields.io/badge/transcription-Groq%20Whisper-orange)

---

## ✨ O que você recebe

Rode em um vídeo ou no perfil inteiro de um criador e você recebe uma nota por vídeo:

```markdown
# 10 broken ChatGPT codes to change how it answers you

- **Profile:** sabrina_ramonov
- **Date:** 2026-06-05 15:43 (BRT)
- **Views:** 11K (10,800)
- **Likes:** 457
- **Comments:** 74
- **Saves:** 590
- **Shares/Reposts:** 156
- **Language:** English
- **Link:** https://www.tiktok.com/@sabrina_ramonov/video/7647983635416616206

## Caption
...

## Transcript
...
```

---

## 🚀 Recursos

- **Um vídeo ou um perfil inteiro**: cole um link, um `@handle` ou apenas um nome de usuário.
- **Toda métrica pública**: visualizações, curtidas, comentários, reposts, **salvamentos** e a data do post.
  (O TikTok expõe os salvamentos publicamente; a maioria das ferramentas não os mostra.)
- **Sem login / sem cookies**: o `yt-dlp` lista o perfil e puxa as métricas para você.
- **Transcrições precisas**: o áudio passa pelo
  `whisper-large-v3` da [Groq](https://groq.com), que detecta o idioma automaticamente.
- **Retomável**: rodar de novo pula os vídeos que já estão prontos e tenta novamente os que
  falharam. Ótimo para grandes acervos.
- **Downloads que se auto-corrigem**: o extrator de TikTok do yt-dlp engasga às vezes; uma
  repetição embutida o recupera.

---

## 📦 Requisitos

| Ferramenta | Por quê | Instalação |
|------|-----|---------|
| [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) | lista perfis + baixa áudio | `pip install -U yt-dlp` |
| [`ffmpeg`](https://ffmpeg.org) | extrai a faixa de áudio | [ffmpeg.org/download](https://ffmpeg.org/download.html) |
| `curl` | chama a API da Groq | já vem instalado no macOS/Linux/Win10+ |
| **Chave de API da Groq** | transcrição (plano gratuito) | [console.groq.com/keys](https://console.groq.com/keys) |

Nenhum pacote Python necessário além da biblioteca padrão.

---

## 🛠️ Configuração

```bash
git clone https://github.com/pedroccm/tiktok-transcriber.git
cd tiktok-transcriber

# 1) free Groq key -> https://console.groq.com/keys
export GROQ_API_KEY="gsk_..."           # Windows (PowerShell): $env:GROQ_API_KEY="gsk_..."

# 2) (optional) where notes are saved. Defaults to ~/Documents/Obsidian Vault/TikTok
export OBSIDIAN_VAULT="/path/to/your/Obsidian Vault"
```

---

## ▶️ Uso

```bash
# one video
python tiktok.py "https://www.tiktok.com/@user/video/7647983635416616206"

# a whole profile (newest -> oldest)
python tiktok.py "https://www.tiktok.com/@sabrina_ramonov"

# just the 50 most recent
python tiktok.py @sabrina_ramonov --limit 50

# several at once
python tiktok.py @user1 @user2 "https://www.tiktok.com/@user3/video/123"
```

Flags:
- `--limit N`, apenas os **N vídeos mais recentes** do perfil.
- `--force`, ignora o cache de retomada e retranscreve tudo.

Usuários de Windows também podem rodar de forma amigável a duplo-clique com `tiktok.cmd @user`.

> **Perfis grandes:** alguns criadores têm milhares de vídeos. Verifique primeiro com
> `yt-dlp --flat-playlist --print id "https://www.tiktok.com/@user" | wc -l`, depois use
> `--limit`. O plano gratuito da Groq limita os minutos de áudio por hora/dia; o script espera
> o limite passar e continua, e é retomável, então você pode avançar aos poucos entre execuções.

---

## 📁 Saída

```
$OBSIDIAN_VAULT/TikTok/
└── <profile>/
    └── <video title>/
        └── Transcript.md
```

O título vem da primeira linha da legenda (já limpa). Vídeos já transcritos
são detectados pelo link, então nada é feito duas vezes.

---

## ⚙️ Como funciona

1. **Listar**: para um perfil, o `yt-dlp --flat-playlist` enumera todas as URLs de vídeo.
2. **Baixar**: o `yt-dlp -x` pega só o áudio como um mp3 mono minúsculo de 16 kHz (com repetição).
3. **Transcrever**: o mp3 é enviado para o Groq Whisper (`whisper-large-v3`).
4. **Escrever**: legenda + métricas + transcrição são salvas como uma nota Markdown.

As métricas vêm direto dos metadados do yt-dlp (`view_count`, `like_count`, `comment_count`,
`repost_count`, `save_count`, `timestamp`), sem scraping, sem segunda requisição.

---

## 🤖 Use como uma skill do Claude Code

Este repositório também é uma skill do [Claude Code](https://claude.com/claude-code). Coloque-o na sua
pasta de skills e invoque-o no chat:

```bash
git clone https://github.com/pedroccm/tiktok-transcriber.git \
  ~/.claude/skills/tiktok-transcriber
```

Depois é só dizer *"transcreva este perfil do TikTok: @user"* e o Claude roda para você.

---

## 📝 Notas & limites

- **Salvamentos** aqui são exclusivos do TikTok; a ferramenta irmã do Instagram não consegue obtê-los (o Instagram
  mantém os salvamentos privados, visíveis só para o dono do post).
- Contagens ocultas voltam como `-1` do yt-dlp e são simplesmente omitidas da nota.
- Posts de foto (carrossel) são pulados, não há fala para transcrever.

---

## 📄 Licença

MIT, veja [LICENSE](LICENSE).
