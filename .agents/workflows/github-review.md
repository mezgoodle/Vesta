---
description: Review github pull request
---

# Agent Workflow: PR Review & Auto-Correction

## Agent Workflow Logic
### Step 1: Context Retrieval
- Use `github-mcp` to fetch:
  - The current diff of the Pull Request.
  - All existing comments and review suggestions left by reviewers.

### Step 2: Semantic Analysis (Root Agent)
- Analyze the diff and match every comment/suggestion to the specific line of code.
- Categorize comments into:
  - "Actionable" (suggestions with code blocks or clear instructions).
  - "Discussion" (questions or general feedback).

### Step 3: Execution (Tool Calling)
- For every "Actionable" comment:
  - Apply the suggested changes (create a new commit or file update) if you think it's useful.


### Step 4: Resolving Review Threads & Verification
- Run lint and test scripts to ensure the changes didn't break anything.
- If checks pass:
  - Resolve the corresponding review threads on GitHub via `gh api graphql`:
    ```bash
    gh api graphql -F threadId="<THREAD_NODE_ID>" -f query='mutation($threadId: ID!) { resolveReviewThread(input: {threadId: $threadId}) { thread { id isResolved } } }'
    ```
  - Provide a concise summary to the user of resolved review threads and committed changes.
- If checks fail:
  - Roll back (if possible) or alert the user with the error log.