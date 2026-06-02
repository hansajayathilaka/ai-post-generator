Read CLAUDE.md and scripts/generate_post.py for context.

Check that the following environment variables are set before proceeding:
- At least one of: ANTHROPIC_API_KEY or GEMINI_API_KEY
- TAVILY_API_KEY

If any required key is missing, report which ones are missing and stop.

If keys are present, run the post generation script:
```
python scripts/generate_post.py
```

Monitor the output and report:
- Which AI provider was used (Claude or Gemini)
- The topic that was selected
- Whether a post was successfully generated
- The new post folder path and its contents
- Any errors that occurred

If generation succeeded, show me the generated post.md content.
