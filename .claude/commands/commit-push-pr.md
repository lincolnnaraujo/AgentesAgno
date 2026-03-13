---
description: Analisa mudancas, cria commit documentado com Conventional Commits, faz push e abre PR com descricao detalhada
allowed-tools: Bash(git *), Bash(gh *), Bash(mvn test *), Bash(pytest *)
---

Voce e um assistente especializado em documentar e publicar mudancas de codigo.
O usuario forneceu esta descricao: $ARGUMENTS

## Passo 1 — Analisar estado atual

Execute em paralelo:

```bash
git status
```

```bash
git diff --stat
git diff
```

```bash
git log --oneline -5
```

```bash
git branch --show-current
```

Analise os resultados e identifique:
- Quais arquivos foram modificados, adicionados ou removidos
- Qual a natureza da mudanca (feat, fix, refactor, docs, test, chore)
- Se ha arquivos sensiveis (.env, credentials, secrets, chaves privadas, tokens)

**BLOQUEIO**: Se detectar arquivos sensiveis no diff, liste-os e pergunte ao usuario se deseja exclui-los antes de continuar. Nunca faca stage de arquivos sensiveis automaticamente.

## Passo 2 — Verificar branch

Se a branch atual for `main` ou `master`:
- PARE e pergunte ao usuario se deseja criar uma nova branch
- Sugira um nome baseado na mudanca: `feat/descricao-curta`, `fix/descricao-curta`, etc.
- So continue apos confirmacao

## Passo 3 — Stage dos arquivos

Adicione arquivos **por nome**, nunca use `git add .` ou `git add -A`.
Selecione apenas os arquivos relevantes para a mudanca descrita pelo usuario.

```bash
git add <arquivo1> <arquivo2> ...
```

## Passo 4 — Criar commit

Analise todas as mudancas staged e crie uma mensagem de commit seguindo Conventional Commits.

**Regras da mensagem**:
- Primeira linha: `<tipo>(<escopo opcional>): <descricao imperativa em portugues>` (max 72 caracteres)
- Linha em branco
- Corpo: explique **o que** mudou e **por que** (nao o como — o diff mostra o como)
- Se a mudanca for em Java, mencione patterns relevantes (records, sealed classes, virtual threads, etc.)
- Se a mudanca for em Python, mencione patterns relevantes (type hints, match/case, pydantic, etc.)
- Termine com Co-Authored-By

**Tipos permitidos**: feat, fix, refactor, docs, test, chore, perf, ci, build
**Escopos sugeridos**: backend, scripts, api, config, deps

Use HEREDOC para garantir formatacao correta:

```bash
git commit -m "$(cat <<'EOF'
<tipo>(<escopo>): <descricao>

<corpo com contexto — o que e por que>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

Apos o commit, mostre o resultado:
```bash
git log --oneline -1
```

## Passo 5 — Push

Antes de fazer push, **pergunte ao usuario se deseja revisar o commit** ou prosseguir.

Apos confirmacao:

```bash
git push -u origin HEAD
```

Se o push falhar por falta de upstream ou branch remota, crie automaticamente:
```bash
git push -u origin HEAD
```

## Passo 6 — Criar Pull Request

Use `gh pr create` com um template bem documentado.

**Regras do PR**:
- Titulo: mesmo formato do commit, max 70 caracteres
- Body: estruturado com Summary, detalhes tecnicos e test plan
- Se houver mudancas em Java E Python, mencione ambos os ecossistemas
- Inclua checklist de testes relevante para a stack modificada

```bash
gh pr create --title "<tipo>(<escopo>): <descricao curta>" --body "$(cat <<'EOF'
## Summary

- <bullet 1: mudanca principal>
- <bullet 2: detalhes relevantes>
- <bullet 3: decisoes tecnicas se houver>

## Detalhes Tecnicos

<Descreva brevemente a abordagem tecnica, patterns utilizados, e decisoes de design.
Para Java: mencione se usou records, sealed classes, virtual threads, pattern matching, etc.
Para Python: mencione se usou type hints, match/case, pydantic v2, async, etc.>

## Test Plan

<Inclua apenas os items aplicaveis:>

- [ ] Testes unitarios passam (`mvn test` / `pytest`)
- [ ] Testes de integracao passam
- [ ] Linting sem erros (`mvn checkstyle:check` / `ruff check`)
- [ ] Testado manualmente
- [ ] Sem regressoes identificadas

## Tipo de Mudanca

- [ ] feat: Nova funcionalidade
- [ ] fix: Correcao de bug
- [ ] refactor: Refatoracao sem mudanca de comportamento
- [ ] docs: Documentacao
- [ ] test: Testes
- [ ] chore: Tarefas auxiliares

---
Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

## Passo 7 — Resumo final

Apresente um resumo conciso com:

```
Commit:  <hash curto> — <mensagem do commit>
Branch:  <nome da branch>
Push:    origin/<branch>
PR:      <URL do PR criado>
```

## Regras gerais

- **Idioma**: mensagens de commit e PR em portugues (exceto termos tecnicos)
- **Conventional Commits**: seguir rigorosamente o padrao definido no CLAUDE.md
- **Seguranca**: nunca fazer commit de secrets, .env, credenciais ou chaves
- **Confirmacao**: sempre pedir confirmacao antes de push e criacao de PR (acoes irreversiveis)
- **Falha em testes**: se testes falharem durante a analise, informe o usuario e sugira criar o PR como draft (`--draft`)
- **Conflitos**: se houver conflitos com a branch base, informe o usuario antes de criar o PR
