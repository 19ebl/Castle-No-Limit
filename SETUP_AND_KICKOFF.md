# Setup and kickoff prompts (for Emilio, keep this file out of the repo)

The repo holds the brief: `AGENTS.md` (rules, protocol, lanes), `PLAN.md` (method and templates), and `CLAUDE.md` (imports AGENTS.md for Claude Code). Codex reads AGENTS.md on its own, and Claude Code reads CLAUDE.md. Each agent then only needs the short kickoff prompt below.

## Setup (about 10 minutes)

1. On GitHub, create an empty private repo, for example `castle-allocation`.
2. Upload `AGENTS.md`, `CLAUDE.md` and `PLAN.md` to the repo root (Add file, then Upload files) and commit to main. Change the time budget at the top of AGENTS.md first if you want more or less than 3 hours.
3. Install the GitHub CLI and sign in with `gh auth login`. Both agents use it for issues and pull requests.
4. Clone the repo twice, one folder per agent:

   ```bash
   gh repo clone YOUR-USERNAME/castle-allocation castle-claude
   gh repo clone YOUR-USERNAME/castle-allocation castle-codex
   ```

5. Terminal 1, Claude Code:

   ```bash
   cd castle-claude
   claude --permission-mode auto
   ```

   Paste the Claude Code kickoff. Auto mode lets it run git, gh and python without asking you each time, with a safety check on every action.

6. Terminal 2, about a minute later (so they don't both create the Coordination issue at once), Codex:

   ```bash
   cd castle-codex
   codex
   ```

   Paste the Codex kickoff. Codex's default sandbox has no network access and keeps `.git` read-only, so package installs, commits, pushes and gh calls will each ask for your approval. Either stay nearby and approve them, or start it with `codex --sandbox danger-full-access` for hands-off running. That turns off Codex's sandbox for your whole computer and OpenAI marks it not recommended, so only use it if you're comfortable with that.

7. Watch the `Coordination` issue on GitHub. That's where they talk, claim work, and post findings.

## Kickoff: Claude Code

```text
You are Claude Code, agent id `claude-code`. OpenAI Codex (agent id `codex`) is working in this same GitHub repository right now from a separate clone. AGENTS.md (loaded through CLAUDE.md) is the shared brief and protocol, and PLAN.md is the method. Read both in full before doing anything else.

Then:
1. Run the Phase 0 preflight in PLAN.md and post HELLO on the Coordination issue (create it if it doesn't exist yet): what works, what doesn't, CPU cores, RAM.
2. CLAIM and build your Phase 0 work: reference.py, tests for every test vector, and the differential-test harness.
3. CLAIM Phase 1 and build the applicant pool model. After that, lead Phase 4, reproduce Codex's final numbers with different seeds, and draft RESULTS.md and STRATEGY_ANSWER.md.

Sync at the points AGENTS.md lists, and answer Codex's requests before starting new work. Keep going until AGENTS.md section 7 is satisfied or the time budget runs out. Run everything you write, and never report a number you didn't compute.
```

## Kickoff: Codex

```text
You are OpenAI Codex, agent id `codex`. Anthropic Claude Code (agent id `claude-code`) is working in this same GitHub repository right now from a separate clone. AGENTS.md is the shared brief and protocol, and PLAN.md is the method. Read both in full before doing anything else.

Then:
1. Run the Phase 0 preflight in PLAN.md and post HELLO on the Coordination issue (create it if it doesn't exist yet): what works, what doesn't, CPU cores, RAM.
2. CLAIM and build your Phase 0 work: the package skeleton, CI, and engine.py passing every test vector. Get it merged fast, because Claude Code builds on it.
3. CLAIM Phases 2 and 3 (Game 1 exact search, Game 2 search) and run them against Claude Code's scenarios as they land. Then run the Phase 5 final validation.

Sync at the points AGENTS.md lists, and answer Claude Code's requests before starting new work. Keep going until AGENTS.md section 7 is satisfied or the time budget runs out. Run everything you write, and never report a number you didn't compute.
```

## Kickoff: one agent only (if you skip the two-agent setup)

```text
You are the only agent on this project. AGENTS.md is the brief and PLAN.md is the method; read both in full. Ignore the parts about the other agent and GitHub messaging, but keep everything else: the independent reference scorer and differential test, seeded experiments saved as JSON, the log files, the 1,000,000-sample final validation, RESULTS.md and STRATEGY_ANSWER.md. Work through PLAN.md phases 0 to 5 in order. Keep going until AGENTS.md section 7 is satisfied (minus the DECISION comments) or the time budget runs out. Run everything you write, and never report a number you didn't compute.
```

## If an agent goes quiet

```text
Sync now: git fetch, read new comments on the Coordination issue, check open PRs, answer anything addressed to you, then continue with the plan.
```

## When they finish

- `RESULTS.md`: the two allocations, exactly as you'd type them in, plus the evidence and the assumption most likely to change the answer.
- `STRATEGY_ANSWER.md`: two drafts for the strategy box. Rewrite in your own words, and keep only what you can explain if an interviewer asks.
