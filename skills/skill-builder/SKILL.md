---
name: skill-builder
description: |
  Build, test, and iteratively improve Claude Agent Skills — from first draft through description optimization and benchmarked iteration. Use this skill whenever the user says things like "I want to make a skill for X", "help me build a skill", "my skill isn't triggering / isn't working", "turn this workflow into a skill", "run evals on my skill", "improve my existing skill", or "optimize my skill's description". Also invoke when someone hands you a SKILL.md and asks for feedback, or when you're designing a new skill from scratch and want a rigorous testing loop.
disable-model-invocation: false
---

# Skill Builder

Determine where the user is in the skill development process and help them progress:

| What the user says                                     | Where to start                                                                          |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| "I want to make a skill for X"                         | [Capture Intent](#creating-a-skill) — interview first, write second                     |
| "Here's a workflow I already do, turn it into a skill" | Extract steps from conversation history, confirm with user, then proceed to drafting    |
| "Here's my draft skill, help me improve it"            | [Diagnose before rewriting](#diagnose-before-rewriting) — gather examples, then improve |
| "My skill isn't working / outputs are inconsistent"    | Read transcripts or ask for a bad-output example first, then diagnose and improve       |
| "I don't need evals, just vibe with me"                | Write the skill directly, skip the formal eval loop                                     |

---

## NEVER List

- **NEVER** optimize the description before the skill logic is stable
- **NEVER** skip baseline runs — prevents verifying the skill's added value
- **NEVER** tighten the skill around test cases — avoid rigid rules that narrow scope. Prefer explaining _why_ over adding constraints
- **NEVER** use conversational filler; provide direct, imperative instructions

---

## Communicating with the User

- Use technical terms (evaluation, benchmark, JSON, assertion) only if the user has demonstrated familiarity
- Explain the _why_ behind workflow steps — users new to skill-building won't instinctively understand why baseline runs matter or why assertions should be drafted during test runs
- Err toward explanation when in doubt

---

## Creating a skill

### Interview and Draft

**Extract from conversation:**
- Tools used, sequence of steps, corrections made
- Input/output formats, success criteria, edge cases
- Whether test cases are appropriate (objective outputs: yes; subjective: no)

**Draft immediately.** Write SKILL.md with uncertain sections marked: `[USER TO CONFIRM: X]`. User refines draft rather than starting from scratch.

**Research:** Check available MCPs for useful data. Query in parallel via subagents if needed.

### Write the SKILL.md

Based on the user interview, fill in these components:

- **name**: Skill identifier
- **description**: When to trigger, what it does. This is the primary triggering mechanism - include both what the skill does AND specific contexts for when to use it. All "when to use" info goes here, not in the body. Note: currently Claude has a tendency to "undertrigger" skills -- to not use them when they'd be useful. To combat this, please make the skill descriptions a little bit "pushy". So for instance, instead of "How to build a simple fast dashboard to display internal Anthropic data.", you might write "How to build a simple fast dashboard to display internal Anthropic data. Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard.'"
- **compatibility**: Required tools, dependencies (optional, rarely needed)
- **the rest of the skill :)**

### Skill Writing Guide

#### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic/repetitive tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons, fonts)
```

#### Progressive Disclosure

Skills use a three-level loading system:

1. **Metadata** (name + description) — Always in context (~100 words)
2. **SKILL.md body** — In context when skill triggers (target: <500 lines)
3. **Bundled resources** — As needed (unlimited, scripts can execute without loading)

**Key patterns:**
- Keep SKILL.md under 500 lines. If approaching the limit, add hierarchy + clear pointers for follow-up sections.
- Reference bundled files clearly with guidance on when to read them.
- For large reference files (>300 lines), include a table of contents.

**Domain organization:** When supporting multiple domains, organize by variant:
```
cloud-deploy/
├── SKILL.md (workflow + selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

#### Writing Patterns

Prefer using the imperative form in instructions.

**Output formats:**
```markdown
## Report structure

# [Title]
## Executive summary
## Key findings
## Recommendations
```

**Examples:**
```markdown
## Commit message format

Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

**File editing:** One edit per turn. Multiple simultaneous edits to the same file cause race conditions.

**Code generation:** Output complete, functional blocks. Avoid placeholders like `// ...rest of code`.

### Test Cases

After writing the skill draft, come up with 2-3 realistic test prompts — the kind of thing a real user would actually say. Share them with the user: [you don't have to use this exact language] "Here are a few test cases I'd like to try. Do these look right, or do you want to add more?" Then run them.

Save test cases to `evals/evals.json`. Don't write assertions yet — just the prompts. You'll draft assertions in the next step while the runs are in progress.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

**MANDATORY — READ ENTIRE FILE:** Read `references/schemas.md` for the full schema (including the `assertions` field, which you'll add later).

## Running and Evaluating Test Cases

This section is one continuous sequence — don't stop partway through. Do NOT use `/skill-test` or any other testing skill.

**Workspace location:** `<skill-name>-workspace/` as a sibling to the skill directory. Within it: `iteration-1/`, `iteration-2/`, etc., and per eval: `eval-0/`, `eval-1/`, etc. Create directories as you go.

### Step 1: Spawn all runs (with-skill AND baseline) in the same turn

For each test case, spawn two subagents in the same turn — one with the skill, one without. This is important: don't spawn the with-skill runs first and then come back for baselines later. Launch everything at once so it all finishes around the same time.

Skipping baseline runs makes it impossible to know whether the skill is actually helping — you'd just be measuring what Claude can do, not what the skill adds. Always run both.

**With-skill run:**

```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files if any, or "none">
- Save outputs to: <workspace>/iteration-<N>/eval-<ID>/with_skill/outputs/
- Outputs to save: <what the user cares about — e.g., "the .docx file", "the final CSV">
```

**Baseline run** (same prompt, but the baseline depends on context):

- **Creating a new skill**: no skill at all. Same prompt, no skill path, save to `without_skill/outputs/`.
- **Improving an existing skill**: the old version. Before editing, snapshot the skill (`cp -r <skill-path> <workspace>/skill-snapshot/`), then point the baseline subagent at the snapshot. Save to `old_skill/outputs/`.

Write an `eval_metadata.json` for each test case (assertions can be empty for now). Give each eval a descriptive name based on what it's testing — not just "eval-0". Use this name for the directory too. If this iteration uses new or modified eval prompts, create these files for each new eval directory — don't assume they carry over from previous iterations.

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "assertions": []
}
```

### Step 2: While runs are in progress, draft assertions

Don't just wait for the runs to finish — you can use this time productively. Draft quantitative assertions for each test case and explain them to the user. If assertions already exist in `evals/evals.json`, review them and explain what they check.

Good assertions are objectively verifiable and have descriptive names — they should read clearly in the benchmark viewer so someone glancing at the results immediately understands what each one checks. Subjective skills (writing style, design quality) are better evaluated qualitatively — don't force assertions onto things that need human judgment.

Update the `eval_metadata.json` files and `evals/evals.json` with the assertions once drafted. Also explain to the user what they'll see in the viewer — both the qualitative outputs and the quantitative benchmark.

### Step 3: As runs complete, capture timing data

When each subagent task completes, you receive a notification containing `total_tokens` and `duration_ms`. Save this data immediately to `timing.json` in the run directory:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

This is the only opportunity to capture this data — it comes through the task notification and isn't persisted elsewhere. Process each notification as it arrives rather than trying to batch them.

**If timing data was missed**: Don't skip benchmarking. Instead, compute estimates from similar runs in previous iterations (same task type, same model, same skill complexity). Note in `benchmark.md` that these are estimated rather than measured — the reader needs to know variance may be higher.

### Step 4: Grade, aggregate, and launch the viewer

Once all runs are done:

1. **Grade each run** — **MANDATORY — READ `agents/grader.md` before starting the grading step.** Spawn a grader subagent (or grade inline) that reads this file and evaluates each assertion against the outputs. Save results to `grading.json` in each run directory. The grading.json expectations array must use the fields `text`, `passed`, and `evidence` (not `name`/`met`/`details` or other variants) — the viewer depends on these exact field names. For assertions that can be checked programmatically, write and run a script rather than eyeballing it — scripts are faster, more reliable, and can be reused across iterations.

2. **Aggregate into benchmark** — run the aggregation script from the skill-builder directory:

   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```

   This produces `benchmark.json` and `benchmark.md` with pass_rate, time, and tokens for each configuration, with mean ± stddev and the delta. If generating benchmark.json manually, see `references/schemas.md` for the exact schema the viewer expects.
   Put each with_skill version before its baseline counterpart.

3. **Do an analyst pass** — read the benchmark data and surface patterns the aggregate stats might hide. **MANDATORY — READ `agents/analyzer.md` (the "Analyzing Benchmark Results" section)** to understand what to look for — things like assertions that always pass regardless of skill (non-discriminating), high-variance evals (possibly flaky), and time/token tradeoffs.

4. **Launch the viewer** with both qualitative outputs and quantitative data:

   > **Path substitution:** Replace `<skill-builder-dir>` with the base directory of this skill shown at the top of your context (e.g. `C:\Users\PC\.claude\skills\skill-builder` or `/Users/you/.claude/skills/skill-builder`). Do NOT use `$CLAUDE_SKILL_DIR` — that shell variable is not set in the bash environment and will expand to an empty string, silently breaking the command.

   ```bash
   python -u "<skill-builder-dir>/eval-viewer/generate_review.py" \
     "<workspace>/iteration-N" \
     --skill-name "my-skill" \
     --benchmark "<workspace>/iteration-N/benchmark.json" \
     > /tmp/viewer.log 2>&1 &
   VIEWER_PID=$!
   sleep 2 && grep -m1 "URL:" /tmp/viewer.log
   ```

   The `-u` flag disables Python output buffering so the URL appears in the log immediately.

   For iteration 2+, also pass `--previous-workspace "<workspace>/iteration-<N-1>"`.

   Capture the `URL:` line from the log to get `http://localhost:{port}` — you'll give this to the user in step 5. If the grep returns nothing (server failed to start), check `/tmp/viewer.log` for the error and fix the path before continuing — do not give the user a URL that doesn't work.

   **Cowork / headless environments:** See `references/cowork.md` for adapted instructions (`--static` flag, feedback download, etc.).

Note: please use generate_review.py to create the viewer; there's no need to write custom HTML.

1. **Tell the user** the URL as a clickable markdown link in your response — always. For server mode: `[Open Eval Viewer](http://localhost:{port})`. For static mode: the script prints the `file://` URL — include it in your response as `[Open Eval Viewer](file:///path/to/file.html)`. Do not just describe where the file is; give the user a link they can click. Then say something like: "There are two tabs — 'Outputs' lets you click through each test case and leave feedback, 'Benchmark' shows the quantitative comparison. When you're done, come back here and let me know."

### What the user sees in the viewer

The "Outputs" tab shows one test case at a time:

- **Prompt**: the task that was given
- **Output**: the files the skill produced, rendered inline where possible
- **Previous Output** (iteration 2+): collapsed section showing last iteration's output
- **Formal Grades** (if grading was run): collapsed section showing assertion pass/fail
- **Feedback**: a textbox that auto-saves as they type
- **Previous Feedback** (iteration 2+): their comments from last time, shown below the textbox

The "Benchmark" tab shows the stats summary: pass rates, timing, and token usage for each configuration, with per-eval breakdowns and analyst observations.

Navigation is via prev/next buttons or arrow keys. When done, they click "Submit All Reviews" which saves all feedback to `feedback.json`.

### Step 5: Read the feedback

When the user tells you they're done, read `feedback.json`:

```json
{
  "reviews": [
    {
      "run_id": "eval-0-with_skill",
      "feedback": "the chart is missing axis labels",
      "timestamp": "..."
    },
    { "run_id": "eval-1-with_skill", "feedback": "", "timestamp": "..." },
    { "run_id": "eval-2-with_skill", "feedback": "perfect, love this", "timestamp": "..." }
  ],
  "status": "complete"
}
```

Empty feedback means the user thought it was fine. Focus your improvements on the test cases where the user had specific complaints.

Kill the viewer server when you're done with it:

```bash
kill $VIEWER_PID 2>/dev/null
```

---

## Improving the skill

This is the heart of the loop. You've run the test cases, the user has reviewed the results, and now you need to make the skill better based on their feedback.

### Diagnose Before Rewriting

Don't rewrite without understanding the actual problem. A hypothesis like "output template is missing" is actionable; "the skill is vague" is not.

**If skill is provided inline:** Read it and diagnose directly. Propose improvements. Only ask for examples if something is truly ambiguous.

**If skill is not provided:** Ask for one bad-output example, or propose running a single test case. This takes 30 seconds and prevents a wasted iteration.

### Before You Start Iterating

- **Feedback consistent?** If conflicts exist ("make it more rigid" vs flexible), clarify first. Get a prioritized list.
- **Failures real?** Read transcripts. Some failures are transient (model variance, edge case), not skill defects. Don't optimize away variance.
- **Overfitting?** You're optimizing on 2-3 test cases. Don't narrow scope for marginal gains. Prefer generality.

### How to Think About Improvements

1. **Generalize from feedback.** Don't overfit to 2-3 test cases. If all runs independently wrote the same helper script (e.g., `create_docx.py`), bundle it in `scripts/` — don't repeat for every invocation.

2. **Keep the prompt lean.** Read transcripts to identify wasted steps. Remove parts of the skill that make the model do unproductive work.

3. **Explain the why.** State the reasoning behind each instruction. LLMs with good framing can generalize intent better than rigid rules.

4. **Avoid overfitting.** When stuck, try different metaphors or working patterns rather than adding more constraints.

### The iteration loop

After improving the skill:

1. Apply your improvements to the skill
2. Rerun all test cases into a new `iteration-<N+1>/` directory, including baseline runs. If you're creating a new skill, the baseline is always `without_skill` (no skill) — that stays the same across iterations. If you're improving an existing skill, use your judgment on what makes sense as the baseline: the original version the user came in with, or the previous iteration.
3. Launch the reviewer with `--previous-workspace` pointing at the previous iteration
4. Wait for the user to review and tell you they're done
5. Read the new feedback, improve again, repeat

Keep going until:

- The user says they're happy
- The feedback is all empty (everything looks good)
- You're not making meaningful progress — if pass rate hasn't improved by at least 5-10 percentage points across an iteration, pause rather than keep tweaking. Either the test set is too narrow (the skill is overfitting to it), the root problem hasn't been correctly identified, or you've hit a ceiling. In that case, generalize the approach — try different metaphors, fewer constraints, or a broader reframe — rather than adding more rules.

---

## Advanced: Blind comparison

For situations where you want a more rigorous comparison between two versions of a skill (e.g., the user asks "is the new version actually better?"), there's a blind comparison system. **MANDATORY — READ `agents/comparator.md` AND `agents/analyzer.md`** for the details. The basic idea is: give two outputs to an independent agent without telling it which is which, and let it judge quality. Then analyze why the winner won.

This is optional, requires subagents, and most users won't need it. The human review loop is usually sufficient.

---

## Description Optimization

The description field in SKILL.md frontmatter is the primary mechanism that determines whether Claude invokes a skill. Wait until the skill's logic is stable before optimizing the description — if the skill's behavior is still changing, triggering criteria will change too and you'll be optimizing for the wrong thing.

After the skill logic is finalized, offer to optimize the description for better triggering accuracy.

### Step 1: Generate trigger eval queries

Create 20 eval queries (8-10 should-trigger, 8-10 should-not-trigger). Save as JSON:

```json
[
  { "query": "the user prompt", "should_trigger": true },
  { "query": "another prompt", "should_trigger": false }
]
```

**should-trigger queries:** Vary phrasing (formal/casual), include cases without explicit skill names but where it's needed. Real context: file paths, job context, data details.

**Bad examples:** `"Format this data"`, `"Extract text from PDF"`  
**Good example:** `"ok so my boss just sent me this xlsx file (Q4 sales final FINAL v2.xlsx) and she wants me to add a profit margin % column. Revenue is column C, costs are column D"`

**should-not-trigger queries:** Focus on near-misses — queries sharing keywords but needing a different tool. Adjacent domains, ambiguous phrasing, contexts where another tool fits better. Avoid obvious irrelevance (the negatives should be genuinely tricky).

### Step 2: Review with user

Present the eval set inline in the conversation. Format it as a readable table showing each query and whether it should trigger:

| #   | Query | Should trigger? |
| --- | ----- | --------------- |
| 1   | "..." | Yes             |
| 2   | "..." | No              |

Ask the user: "Do these look right? Feel free to suggest changes, remove any that feel off, or add ones you think I'm missing." Wait for their sign-off before saving and proceeding.

Once confirmed, save the (possibly revised) queries to `<workspace>/trigger-eval.json`.

This step matters — bad eval queries lead to bad descriptions.

### Step 3: Run the optimization loop

Tell the user: "This will take some time — I'll run the optimization loop in the background and check on it periodically."

Save the eval set to the workspace, then run in the background:

```bash
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id-powering-this-session> \
  --max-iterations 5 \
  --verbose
```

Use the model ID from your system prompt (the one powering the current session) so the triggering test matches what the user actually experiences.

While it runs, periodically tail the output to give the user updates on which iteration it's on and what the scores look like.

This handles the full optimization loop automatically. It splits the eval set into 60% train and 40% held-out test, evaluates the current description (running each query 3 times to get a reliable trigger rate), then calls Claude to propose improvements based on what failed. It re-evaluates each new description on both train and test, iterating up to 5 times. When it's done, it opens an HTML report in the browser showing the results per iteration and returns JSON with `best_description` — selected by test score rather than train score to avoid overfitting.

### How Skill Triggering Works

Claude consults skills only for tasks it can't easily handle alone. Simple queries ("read this PDF") won't trigger skills even if the description matches — Claude handles them directly. Complex, multi-step, or specialized queries trigger when description matches.

**Implication:** Eval queries must be substantive enough to benefit from skill consultation. Simple queries like "read file X" are poor test cases.

### Step 4: Apply the result

Take `best_description` from the JSON output and update the skill's SKILL.md frontmatter. Show the user before/after and report the scores.

---

### Package and Present (only if `present_files` tool is available)

Check whether you have access to the `present_files` tool. If you don't, skip this step. If you do, package the skill and present the .skill file to the user:

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

After packaging, direct the user to the resulting `.skill` file path so they can install it.

---

## Claude.ai-specific Instructions

Core workflow is the same (draft → test → review → improve → repeat), but without subagents:

| Task | Claude Code | Claude.ai |
|------|-----------|-----------|
| Test cases | Parallel subagents + baseline | Serial, no baseline — you run the skill |
| Review results | Browser viewer (outputs + benchmark) | Present in conversation; user gives feedback inline |
| Benchmarking | Quantitative (with baseline comparison) | Skip — qualitative feedback only |
| Description optimization | `claude -p` loop | Skip — requires Claude Code CLI |
| Blind comparison | Subagent-driven | Skip — requires subagents |
| Packaging | `package_skill.py` | Same — works on any filesystem |

**Updating an existing skill:**
- Preserve original `name` field (e.g., `research-helper`, not `research-helper-v2`)
- Copy to `/tmp/skill-name/` before editing (installed path may be read-only)
- Output to `/tmp/` first, then move to destination

---

**Running in Cowork?** See `references/cowork.md` for the adapted workflow (no browser, static viewer, feedback download, etc.).

---

## Reference files

The agents/ directory contains instructions for specialized subagents. Each has an explicit MANDATORY trigger embedded in the workflow above — don't load them proactively.

- `agents/grader.md` — Grading assertions against run outputs (MANDATORY trigger at Step 4)
- `agents/comparator.md` — Blind A/B comparison between two skill versions (triggered in Advanced section)
- `agents/analyzer.md` — Analyst pass on benchmark data (MANDATORY trigger at Step 4)

The references/ directory:

- `references/schemas.md` — Full JSON schemas for evals.json, grading.json, benchmark.json, eval_metadata.json. MANDATORY trigger is embedded in the Test Cases section above. Do NOT load for other tasks.
- `references/cowork.md` — Adapted workflow for headless/Cowork environments. Load only when the user is in Cowork or you can't open a browser.

---

Repeating one more time the core loop here for emphasis:

- Figure out what the skill is about
- Draft or edit the skill
- Run claude-with-access-to-the-skill on test prompts
- With the user, evaluate the outputs:
  - Create benchmark.json and run `eval-viewer/generate_review.py` to help the user review them
  - Run quantitative evals
- Repeat until you and the user are satisfied
- Package the final skill and return it to the user.

Please add steps to your TodoList, if you have such a thing, to make sure you don't forget. If you're in Cowork, please specifically put "Generate eval viewer and give user the link before revising skill" in your TodoList to make sure it happens.

Good luck!
