# Person Memory GitHub Facade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the repository homepage into a polished bilingual presentation of Person Memory as a unified, local-first Agent Skill, while retaining Hermes as the current independent-agent integration.

**Architecture:** Keep all runtime code unchanged. Put the English and Simplified Chinese narratives in parallel root README files, use one repository-owned SVG as the shared hero artwork and render it to a 1280 by 640 PNG, then update GitHub repository metadata through the authenticated GitHub CLI.

**Tech Stack:** GitHub-flavored Markdown, Mermaid, SVG, Sharp, PowerShell, Python unittest, GitHub CLI

---

## File Structure

- Create `assets/person-memory-hero.svg`: source artwork used at the top of both README editions.
- Create `assets/person-memory-social-preview.png`: 1280 by 640 raster export suitable for GitHub's Social Preview setting.
- Modify `README.md`: canonical English repository homepage.
- Create `README.zh-CN.md`: first-class Simplified Chinese repository homepage.
- Preserve `TRIGGERS.md`: detailed trigger reference linked from both README editions.
- Preserve all files under `person-memory/`, `hermes/`, and `tests/`: runtime behavior is outside this change.

### Task 1: Create the Shared Brand Asset

**Files:**
- Create: `assets/person-memory-hero.svg`
- Create: `assets/person-memory-social-preview.png`

- [ ] **Step 1: Create the SVG source**

Create a 1280 by 640 accessible SVG with `role="img"`, an English `<title>`, a dark indigo-to-violet background, a person node connected to evidence and memory nodes, the title `Person Memory`, and the line `Local-first memory for AI agents — grounded in evidence.` Use only system fonts and SVG primitives so the asset is deterministic and repository-native.

- [ ] **Step 2: Validate the SVG syntax**

Run:

```powershell
[xml](Get-Content -LiteralPath '.\assets\person-memory-hero.svg' -Raw) | Out-Null
```

Expected: exit code 0 with no parser error.

- [ ] **Step 3: Render the social-preview PNG**

Run:

```powershell
$env:NODE_PATH='C:\Users\Hubujiu\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'
node -e "require('sharp')('assets/person-memory-hero.svg').resize(1280,640).png().toFile('assets/person-memory-social-preview.png')"
```

Expected: Sharp reports a 1280 by 640 PNG.

- [ ] **Step 4: Inspect the rendered asset**

Open `assets/person-memory-social-preview.png` with the local image viewer. Confirm readable title and tagline, no clipped nodes, and strong contrast.

- [ ] **Step 5: Commit the assets**

```powershell
git add -- assets/person-memory-hero.svg assets/person-memory-social-preview.png
git commit -m "docs: add Person Memory brand artwork"
```

### Task 2: Rewrite the English Homepage

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the current README with the approved hierarchy**

Use this exact section order:

```text
hero image and language switch
value proposition and badges
Why Person Memory
How it works
What it remembers
Designed for any agent, ready for Hermes
Quick start
Memory with restraint
Triggers and routing
Privacy by default
Repository layout
Testing
FAQ
License
```

The first paragraph must identify the project as a unified Agent Skill. State that Hermes is the current complete independent-agent integration. Preserve all material feature claims from the existing README, link trigger details to `TRIGGERS.md`, and use the real clone URL `https://github.com/Hubujiu/person-memory.git`.

- [ ] **Step 2: Add a compact Mermaid flow**

Use a left-to-right flow from forwarded message to raw evidence and conservative extraction, then to SQLite and targeted recall. Label nodes in English and avoid HTML-only styling that breaks GitHub rendering.

- [ ] **Step 3: Check English README facts and links**

Run:

```powershell
rg -n 'README.zh-CN.md|TRIGGERS.md|Hubujiu/person-memory|Hermes|Agent Skill|privacy|unittest' README.md
rg -n '<repo-url>|T[B]D|T[O]DO' README.md
```

Expected: the first command finds every required concept; the second returns no matches.

- [ ] **Step 4: Commit the English README**

```powershell
git add -- README.md
git commit -m "docs: reshape the English project homepage"
```

### Task 3: Add the Simplified Chinese Homepage

**Files:**
- Create: `README.zh-CN.md`

- [ ] **Step 1: Write the Chinese edition**

Mirror every English section, command, path, compatibility statement, privacy boundary, and FAQ answer. Write natural Simplified Chinese rather than sentence-by-sentence machine translation. Link back to `README.md` in the first screen.

- [ ] **Step 2: Verify structural parity**

Run:

```powershell
$en = (Select-String -Path '.\README.md' -Pattern '^## ').Count
$zh = (Select-String -Path '.\README.zh-CN.md' -Pattern '^## ').Count
if ($en -ne $zh) { throw "README section mismatch: en=$en zh=$zh" }
```

Expected: exit code 0 and equal second-level heading counts.

- [ ] **Step 3: Verify shared commands and links**

Run:

```powershell
rg -n 'README.md|TRIGGERS.md|git clone https://github.com/Hubujiu/person-memory.git|person_memory.py|python3 -m unittest' README.zh-CN.md
rg -n '<repo-url>|T[B]D|T[O]DO' README.zh-CN.md
```

Expected: the first command finds all shared operational references; the second returns no matches.

- [ ] **Step 4: Commit the Chinese README**

```powershell
git add -- README.zh-CN.md
git commit -m "docs: add the Simplified Chinese homepage"
```

### Task 4: Verify the Complete Repository Facade

**Files:**
- Verify: `README.md`
- Verify: `README.zh-CN.md`
- Verify: `assets/person-memory-hero.svg`
- Verify: `assets/person-memory-social-preview.png`
- Test: `tests/test_person_memory.py`
- Test: `tests/test_trigger.py`

- [ ] **Step 1: Run whitespace and repository checks**

```powershell
git diff --check origin/main...HEAD
git status --short
```

Expected: no whitespace errors; only intentional plan/spec changes remain if they have not yet been committed.

- [ ] **Step 2: Run the existing test suite**

```powershell
python3 -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 3: Confirm PNG dimensions and file size**

```powershell
$env:NODE_PATH='C:\Users\Hubujiu\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'
node -e "const sharp=require('sharp'); sharp('assets/person-memory-social-preview.png').metadata().then(m=>{if(m.width!==1280||m.height!==640)process.exit(1); console.log(m.width+'x'+m.height)})"
Get-Item '.\assets\person-memory-social-preview.png' | Select-Object Length
```

Expected: `1280x640` and a file smaller than 1 MB.

- [ ] **Step 4: Inspect both README editions on GitHub-compatible rendering**

Confirm that the SVG appears above the fold, language links work, Mermaid renders, tables remain readable, and commands do not overflow at a narrow viewport.

### Task 5: Publish and Update GitHub Metadata

**Files:**
- Modify: GitHub repository metadata for `Hubujiu/person-memory`

- [ ] **Step 1: Commit the implementation plan and any final documentation corrections**

```powershell
git add -- docs/superpowers/plans/2026-08-18-github-facade.md README.md README.zh-CN.md assets
git commit -m "docs: finalize GitHub facade refresh"
```

Expected: a commit is created, or Git reports that all intended files are already committed.

- [ ] **Step 2: Update the repository description and Topics**

```powershell
gh repo edit Hubujiu/person-memory --description "A local-first, evidence-backed memory skill that helps AI agents remember people with context, privacy, and restraint." --add-topic agent-skill --add-topic ai-agent --add-topic personal-memory --add-topic long-term-memory --add-topic local-first --add-topic privacy-first --add-topic evidence-based --add-topic sqlite --add-topic hermes-agent --add-topic python
```

Expected: exit code 0.

- [ ] **Step 3: Verify GitHub metadata**

```powershell
gh repo view Hubujiu/person-memory --json description,repositoryTopics
```

Expected: the approved description and all ten Topics are present.

- [ ] **Step 4: Push the completed commits**

```powershell
git push origin main
```

Expected: `main` advances on `origin` without a force push.

- [ ] **Step 5: Verify the live repository**

Open `https://github.com/Hubujiu/person-memory` and confirm the updated homepage, description, Topics, language switch, hero artwork, and Mermaid diagram are visible.
