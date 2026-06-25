---
name: receive-code-review
description: "Processes, verifies, and implements code review feedback received from human reviewers, pull request bots, or subagents. Accepts markdown or text review comments as input, checks them against the codebase to prevent regression or conflict, and outputs verified, atomic file edits. Also triggers when addressing automated git comments, fixing lints, or updating changes from a previous review. Always prefer this skill over request-code-review when modifying code based on existing feedback rather than requesting a new review. Trigger on: 'review feedback', 'reviewer said', 'PR comments', 'fix review comments', 'receive-code-review', 'implement feedback', 'address feedback', 'PR feedback', 'address review comments'."
disable-model-invocation: false
---

# receive-code-review

Code review feedback requires technical evaluation, not emotional performance or blind compliance. Verify before implementing. Ask before assuming.

## Process Flow

```
Start: Feedback Received
  -> 1. Identify Source (subagent, human, bot)
  -> 2. Read & Clarify (stop if ambiguous)
  -> 3. Verify Finding (mandatory) -- match codebase? no regressions? no conflicts?
  -> 4. Respond (verified or pushback)
  -> 5. Implement (severity order)
       -- Tier 1/2 blocking --> diagnose (handoff)
  -> 6. Test individual fix
  -> next item --> back to 3. Verify Finding
  -- all items fixed --> verification-before-completion (handoff)
```

## Never Do This

- **No Chatting:** Never say thanks or "you're right." Just fix it.
- **No Blind Fixes:** Never change code without checking it first.
- **No Grouping:** Fix one thing, test it, repeat. Do not do them all at once.
- **No Ignoring Rules:** Follow `AGENTS.md` and the user. If they fight, tell the user.
- **No Huge Changes:** Ask first before changing 10+ files or core designs.
- **No Loops:** Stop after 2 reviews of the same code. Ask the user.

## Who to Trust

- **Human:** Trust. Fix it. Ask if confused.
- **Subagent (`request-code-review`):** Do not trust. Verify everything.
- **GitHub PR/Bot:** Do not trust. Read: `gh pr view <number> --comments`. Reply: `gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies -f body="..."`.

## Ask First

- **Read All:** Read all feedback before you start.
- **Ask Questions:** Use `AskUserQuestion` to ask about confusing things (max 4 questions at once).
- **Stop and Wait:** Do not fix code if you are confused about it.

## Always Do This

- **Read Docs:** Read `AGENTS.md` before coding.
- **Check the Code:** Use `git grep` and tests to see if a fix is actually needed.
- **Run Tests:** Test before and after you change code.
- **Look for Reasons:** Check if the code was written that way on purpose.
- **Delete Unused Code:** If code is never used, ask to delete it instead of fixing it.

## How to Talk

- **Good Fix:** Say "Fixed. [what changed]".
- **Bad Idea:** Say no and prove why using the code.
- **Need Help:** Say "Can't verify this without [X]. Should I proceed?".
- **Mistakes:** Say "Checked [X]. Fixing." (Never apologize).

## How to Work

- **Order to Fix:** 1. Big bugs. 2. Typos. 3. Hard changes.
- **Test Always:** Test every single fix right after you make it.

## What Tools to Use

- **Bugs & Security:** Use `diagnose` to find the real problem.
- **Cleanups:** Fix the code directly.
- **Finished:** Run `verification-before-completion`, then ask for a new review.
- **Stuck:** If you fail twice, STOP. Mark as **BLOCKED**. Wait for the user. Do not try again.
