# Git Workflow & Team Collaboration

## Version Control & Git Integration

Track plan evolution using Git:

### Branching Strategy

```bash
git checkout -b plans/auth-middleware
git add plan-feature-auth-middleware-1.md
git commit -m "Add JWT auth implementation plan"
git push origin plans/auth-middleware
```

### Committing Plans

Include the plan in your PR or branch:

```bash
git commit -m "Add auth implementation plan

Implements task: Add JWT auth to Express API
File: plan-feature-auth-middleware-1.md
Effort: 3-4 hours
Status: Ready for review"
```

### Plan Versioning

When updating a plan:

- Increment version: `plan-feature-auth-middleware-1.md` → `plan-feature-auth-middleware-2.md`
- Keep old versions for history (don't delete)
- Reference in commits: "Updates plan-feature-auth-middleware-1.md"

### Linking Plans in PRs

```
Implements plan: plan-feature-auth-middleware-1.md
See: /plan/feature-auth-middleware-1.md
```

---

## Team Collaboration & Reviews

### Plan Review Workflow

1. **Generate plan** and commit to feature branch: `plans/[purpose]-[component]`
2. **Create PR** with plan for stakeholder review
3. **Reviewers check**:
   - Are all dependencies tracked correctly?
   - Is the effort estimate realistic for our team?
   - Are there missing edge cases?
   - Does it match our team's standards?
4. **Approve and merge** after feedback
5. **Assign to executor** with link to the plan: `[Full Plan](./plan/plan-name.md)`

### Feedback & Iteration

If reviewers request changes:

1. Update the plan in place (don't create v2 yet)
2. Push updates to the same branch
3. Request re-review
4. Merge when approved

If plan scope changes mid-execution:

1. Create new version: `v2`, `v3`, etc.
2. Document what changed and why
3. Notify executor of the new plan version

### Team Standards Checklist

Before approving a plan, verify:

- ✅ Plan file follows naming: `[purpose]-[component]-[version].md`
- ✅ Passes automated validation: `python ${CLAUDE_SKILL_DIR}/scripts/validate_plan.py [plan].md`
- ✅ Effort estimate is realistic for your team and codebase
- ✅ All external dependencies documented
- ✅ Security considerations addressed
- ✅ Testing strategy is comprehensive
- ✅ Rollback plan included (if applicable)
