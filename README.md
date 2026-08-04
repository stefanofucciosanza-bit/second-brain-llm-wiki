# 🧠 Second Brain — LLM Wiki + PARA

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Obsidian](https://img.shields.io/badge/Obsidian-vault-7C3AED.svg)
![Built with Claude Code](https://img.shields.io/badge/Built%20with-Claude%20Code-D97757.svg)

A personal knowledge system where an **LLM agent (Claude Code) incrementally builds and maintains a
persistent wiki** inside an Obsidian vault. Instead of re-deriving knowledge on every question (RAG),
the agent compiles it once into interlinked markdown and keeps it current.

**Obsidian is the IDE · the LLM is the programmer · the wiki is the codebase.**

> ⚠️ This repo is a **system showcase / template**. It contains the *method and tools* only — no
> personal notes. Keep your actual content (and anything confidential) out of any public repo.

---

## How it works — three layers
1. **`raw/`** — immutable source documents (articles, PDFs, transcripts). The agent reads, never edits.
2. **The wiki** — LLM-generated markdown (summaries, entity/concept pages, MOCs) in PARA folders.
3. **The schema** — [`CLAUDE.md`](./CLAUDE.md): the conventions and workflows that make the agent a
   disciplined librarian.

## Three operations
- **Ingest** — drop a source in `raw/`, the agent summarizes + propagates across the wiki + logs it.
- **Query** — ask a question; the agent answers with citations and files valuable answers back.
- **Lint** — periodic health-check (contradictions, orphans, stale claims, missing links).

Two index files keep it navigable: `index.md` (content catalog) and `log.md` (append-only chronology).

---

## Tools (`/tools`)
| Tool | What it does |
|---|---|
| `pdf_ingest.py` | Extract text (`pypdf`) + render pages to PNG (`pypdfium2`+`pillow`) so the agent can read text and view diagram pages. |
| `jarvis.py` | Local voice layer: mic -> `faster-whisper` (STT) -> `claude -p` in the vault -> `Piper` (TTS). Talk to your second brain. |
| `claude_bridge.py` | OpenAI-compatible server that routes `/v1/chat/completions` to `claude -p` in the vault. Lets any OpenAI-compatible voice/chat client use your Claude Code brain as the LLM (e.g. [huggingface/speech-to-speech](https://github.com/huggingface/speech-to-speech)). |

## Quickstart
1. Install [Obsidian](https://obsidian.md) and [Claude Code](https://claude.com/claude-code).
2. Copy `CLAUDE.md` to your vault root and adapt the domain sections.
3. Open Claude Code in the vault folder. Drop sources in `raw/` and say *"process this"*.

## Credit
Inspired by the "LLM Wiki" pattern for building personal knowledge bases with LLMs.

## License
MIT — do what you like with the **system**. Your **content** is yours; keep it private.
