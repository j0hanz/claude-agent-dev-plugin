# Cowork-Specific Workflow

Headless/Cowork environment adjustments for the core lifecycle.

## Workflow Adjustments

- **Viewer**: Use `--static <path>` with `generate_review.py`. Provide the `file://` URL as a clickable link.
- **Feedback**: "Submit All Reviews" downloads `feedback.json`. Request access to read it.
- **Timing**: Run test prompts serially if parallel execution causes timeouts.

## Mandatory Procedure

1. **Viewer First**: Always run `generate_review.py` and provide the link before modifying the skill.
2. **installed Skills**:
   - Preserve original `name`.
   - Copy to `/tmp/` before editing to avoid permission issues.
   - Stage in `/tmp/` for packaging.

```bash
python <skill-path>/eval-viewer/generate_review.py \
  <workspace>/iteration-N \
  --skill-name "my-skill" \
  --benchmark <workspace>/iteration-N/benchmark.json \
  --static <workspace>/iteration-N/review.html
```
