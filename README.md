# my-claude-skills

> 92+ curated skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) / [Ducc](https://comate.baidu.com) — supercharge your AI coding agent.

A comprehensive collection of Claude Code skills covering code review, document processing, research, frontend design, DevOps, data analysis, and more. Install any skill to extend your Claude Code / Ducc agent with powerful new capabilities.

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/pandengyao/my-claude-skills.git

# Copy skills you need to your Claude Code skills directory
cp -r my-claude-skills/paper-reader ~/.claude/skills/
```

Or copy the entire collection:

```bash
cp -r my-claude-skills/* ~/.claude/skills/
```

---

## Skill Categories

### Code Review & Quality (10)

| Skill | Description |
|-------|-------------|
| `go-code-analyzer` | Deep Go analysis with 41 checks: security, memory, concurrency, I/O, compiler optimization |
| `go-codereviewer` | Automated Go code review against Baidu Go coding standards |
| `go-robustness-review-v2` | Go robustness & security review: 42 checks across 7 categories |
| `code-review-skill` | Multi-language code review for commits, branch diffs, and review standards |
| `code-refactoring-and-optimization` | Diagnose code smells and performance bottlenecks, refactor safely |
| `pr-reviewer` | Expert Flutter PR reviewer for quality, architecture, and performance |
| `android-peer-pushedcode-reviewer` | Android code review via Gerrit with call-chain and data-flow analysis |
| `experiment-code-cleanup` | Remove experiment / feature-flag code across multiple languages |
| `sql-optimization-patterns` | SQL query optimization, indexing strategies, and EXPLAIN analysis |
| `doc-check-solution` | Check documents for typos, punctuation errors, and style issues |

### Code Generation & Development (8)

| Skill | Description |
|-------|-------------|
| `code-generation` | Structured workflow: requirements → design → iteration → testing → delivery |
| `typescript-write` | Write TypeScript / JavaScript following Metabase coding standards |
| `gdp2-sql-api` | Generate CRUD APIs from DB table structures using GDP2 MVC framework |
| `linear-implement` | Full TDD workflow from Linear issue to PR with parallel code reviews |
| `create-pr` | Create GitHub PRs with properly formatted titles that pass CI |
| `git-commit-helper` | Generate descriptive commit messages by analyzing git diffs |
| `dam-function-documentation-generator` | Auto-generate structured function docs for Java projects |
| `dam-mapper-to-repository-sync` | Sync SQL/PO/Mapper/Repository/Gateway after DB table changes |

### Search & Research (7)

| Skill | Description |
|-------|-------------|
| `paper-reader` | Deep-read academic papers and generate structured reading notes |
| `arxiv-search` | Search arXiv for papers in physics, math, CS, and more |
| `baidu-search` | Web search via Baidu AI Search Engine |
| `baidu-scholar-search` | Search Chinese & English academic literature |
| `baidu-baike` | Query authoritative encyclopedia entries from Baidu Baike |
| `web-research` | Structured comprehensive web research using spawned subagents |
| `research-synthesis` | Synthesize research findings for OAK planning |

### Frontend & Design (9)

| Skill | Description |
|-------|-------------|
| `frontend-design` | Create distinctive, production-grade frontend interfaces |
| `app-builder` | Build React apps, admin panels, data dashboards |
| `web-artifacts-builder` | Build multi-component HTML artifacts with React + Tailwind + shadcn/ui |
| `canvas-design` | Create visual art (posters, designs) as PNG / PDF |
| `algorithmic-art` | Generative art using p5.js with seeded randomness |
| `theme-factory` | Apply professional themes to slides, docs, reports, landing pages |
| `brand-guidelines` | Apply Anthropic's official brand colors and typography |
| `acud-icon-components` | 722 React icon components for Baidu Cloud Console (ACUD) |
| `seui-figma-to-xml` | Generate SEUI XML layout code from Figma design specs |

### File Processing (7)

| Skill | Description |
|-------|-------------|
| `pdf` | Full PDF toolkit: read, merge, split, rotate, watermark, OCR, encrypt |
| `docx` | Create, read, edit, and manipulate Word documents |
| `pptx` | Create, edit, and analyze PowerPoint presentations |
| `xlsx` | Work with Excel spreadsheets (.xlsx, .csv, .tsv) |
| `file-covert-to-markdown` | Convert various file formats to Markdown (markitdown) |
| `wechat-article-to-markdown` | Scrape WeChat articles → Markdown with images |
| `processing-batch-crypto` | Batch encrypt / decrypt using AES, RSA, SHA256, MD5, Base64, etc. |

### Documentation & Writing (6)

| Skill | Description |
|-------|-------------|
| `doc-coauthoring` | Structured collaborative workflow for docs, proposals, and specs |
| `prd-to-tech-design` | Convert PRD to comprehensive technical design documents |
| `module-detailed-design` | Produce detailed module design documents from PRD |
| `changelog-generator` | Transform git commits into polished user-facing changelogs |
| `weekly-git-report` | Generate weekly work reports by analyzing Git commits and diffs |
| `internal-comms` | Write status reports, newsletters, incident reports |

### Data & Analysis (5)

| Skill | Description |
|-------|-------------|
| `excel-analysis` | Pivot tables, charts, and data analysis for Excel |
| `dashboard-creator` | HTML dashboards with KPI cards, bar / pie / line charts |
| `creating-financial-models` | DCF analysis, sensitivity testing, Monte Carlo simulations |
| `annotation-converter` | Convert multi-modal annotation Excel data to structured JSON |
| `lx-analyzer` | Diagnose distributed training / inference failures: hang, OOM, NCCL |

### AI & Model Tools (7)

| Skill | Description |
|-------|-------------|
| `claude-api` | Build, debug, and optimize Claude API / Anthropic SDK apps |
| `gemini` | Execute Gemini CLI for AI-powered code analysis |
| `hf-model-explorer` | Explore HuggingFace model structures, parameters, architecture |
| `prompt-engineering-patterns` | Advanced prompt engineering for production LLM performance |
| `mcp-builder` | Build MCP (Model Context Protocol) servers in Python / TypeScript |
| `notebooklm-skill` | NotebookLM CLI: create notebooks, add sources, generate podcasts |
| `shenghua-skill` | Baidu AI+ short drama creation: full workflow from script to video |

### DevOps & Infrastructure (7)

| Skill | Description |
|-------|-------------|
| `playwright-mcp` | Browser testing, web scraping, and UI validation |
| `webapp-testing` | Test local web apps with Playwright: screenshots, browser logs |
| `chrome-devtools` | Browser automation and performance analysis with Puppeteer |
| `database-helper` | Database operations assistant for querying and analysis |
| `integrating-probehub` | ProbeHub distributed task scheduling: agents, cron jobs, alerts |
| `aihc-kubeconfig` | Retrieve kubeconfig for Baidu AIHC managed resource pools |
| `relay-oncall` | Troubleshoot Baidu Relay bastion host issues |

### Productivity & Workflow (7)

| Skill | Description |
|-------|-------------|
| `create-plan` | Generate detailed implementation plans with objectives and risks |
| `planning-with-files` | Manus-style file-based planning: task_plan.md, findings.md, progress.md |
| `sequential-thinking` | Step-by-step reasoning with revision and branching |
| `agent-teams-playbook` | Multi-agent orchestration and task distribution |
| `skill-creator` | Create, modify, evaluate, and optimize Claude Code skills |
| `skill-recommender` | Discover and install new skills from remote platform |
| `claude-backup-migrate` | Backup, migrate, and restore Claude Code conversations and config |

### Communication & Social (5)

| Skill | Description |
|-------|-------------|
| `so-send-message` | Send text / Markdown / image messages to Baidu Hi (Ruliu) |
| `xiaohongshu` | Automated Xiaohongshu posting, commenting, and interaction |
| `slack-gif-creator` | Create animated GIFs optimized for Slack |
| `presentation-builder` | Structure compelling presentations with visual suggestions |
| `programmer-cheerleader` | Humorous encouragement and morale-boosting for developers |

### Baidu Internal Tools (11)

| Skill | Description |
|-------|-------------|
| `baidu-exchange-skill` | Manage Baidu enterprise email via natural language |
| `bdpan-storage` | Upload to Baidu Netdisk and generate share links |
| `icafe-skill` | iCafe project management: cards, status transitions, batch ops |
| `iapi-manager` | Search APIs, get Swagger / Markdown specs from iAPI platform |
| `itest-assistant` | Manage test submissions and readiness checks on iTest |
| `ku-doc-manage` | Manage Baidu Knowledge Base documents |
| `weiyun-log-query` | Query logs from Baidu Weiyun LogHub API |
| `scan-log-analyzer` | Analyze Comate scan feature logs |
| `clawdbot-logs` | Analyze Clawdbot bot performance, errors, and costs |
| `zhiyanshi-assistant` | Zhiyanshi requirement management: cards, state transitions, batch ops |
| `figma-image-processor` | Download Figma images, compress, and upload to CDN |

### Utilities (3)

| Skill | Description |
|-------|-------------|
| `daily-hot-news` | Trending topics from 54 platforms (Weibo, Zhihu, Bilibili, Douyin...) |
| `get-weather` | Fetch current weather for any location |
| `api-design-principles` | REST and GraphQL API design best practices |

---

## How Skills Work

Each skill is a directory containing a `SKILL.md` file that defines:
- **When to trigger** — keywords or scenarios that activate the skill
- **Instructions** — step-by-step guidance for Claude Code to follow
- **References** — additional docs, scripts, or templates

Claude Code automatically loads relevant skills based on your prompt context.

---

## Contributing

Found a bug or want to add a new skill? PRs welcome!

1. Fork this repo
2. Create a new skill directory with a `SKILL.md`
3. Submit a PR with a description of what the skill does

---

## License

See [LICENSE](LICENSE) for details.
