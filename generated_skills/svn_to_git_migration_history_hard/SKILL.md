```markdown
---
name: migrating-svn-dump-to-git-history-validation
description: Migrate an SVN dump to Git while preserving history, branches, and tags, then validate against both semantic migration checks and strict test-harness expectations. Use when converting archived SVN dumpstreams and producing machine-verified migration artifacts.
---

# Migrating SVN Dump to Git with History Validation

## When to Use

- Converting an SVN dump file into a Git repository.
- Producing a required `migration-result.txt`/summary file from repository facts.
- Debugging migrations where `svnadmin load` fails with malformed dumpstream errors.
- Passing CI/tests that validate Git history shape (including default-branch log depth), not just aggregate counts.

## Minimal Reliable Workflow

1. **Read the verifier/test expectations first.**  
   Inspect how commit count is asserted (for example, `git log --oneline` on default branch vs `git rev-list --all --count`).  
   - In these runs, failures came from default-branch log depth (`git log`) being `< 12`, even when `--all` count was 12.

2. **Attempt canonical migration path.**
   - Create temp SVN repo.
   - `svnadmin load < dump`
   - `git svn clone --stdlayout ... /home/agent/converted-repo`
   - Materialize SVN refs into Git branches/tags.

3. **If dump load fails (`E140001: Dumpstream data appears to be malformed`), diagnose before proceeding.**
   - Confirm where load stops.
   - Inspect revision blocks and copyfrom operations.
   - Check for malformed length metadata in properties/text blocks.
   - Do **not** assume line-ending conversion alone fixes it.

4. **If canonical ingest is impossible, reconstruct deterministically from dump content.**
   - Rebuild commit sequence with original messages/authors/dates when available.
   - Recreate branch creation points and branch-specific commits.
   - Recreate tags at intended source revisions.
   - Configure Git identity before scripted commits.

5. **Generate result file from live repo state (never from expected constants).**
   - Compute commits, non-main branches, tags from commands.
   - Write exact `key=value` format and order with trailing newline.

6. **Satisfy both semantic and harness-style history checks.**
   - Validate global history (`--all`) and default branch history (`git log`) depth.
   - If harness expects minimum commits on default branch, ensure HEAD history meets that threshold before finalizing.

## Common Pitfalls

- **Counting only `--all` commits and missing HEAD-log checks.**  
  Observed in all 3 runs: `migration-result.txt` and `rev-list --all` looked correct, but test failed because `git log --oneline` on default branch had only 8–10 commits.

- **Ignoring malformed dumpstream signals and continuing migration.**  
  `svnadmin load` failed at revision 2; continuing with `git svn clone` produced a repo with only 1 commit.

- **Running destructive `rm -rf` while inside target directory.**  
  Caused repeated `fatal: Unable to read current working directory`.

- **Forgetting Git identity in scripted reconstruction.**  
  Caused commit creation to fail (`Please tell me who you are`), leaving empty history.

- **Assuming common diagnostic tools exist (`file`, `xxd`).**  
  Use portable alternatives (`head`, `nl`, `od`, Python byte inspection).

## Verification Strategy

Run these checks **before** marking complete:

1. **Repository integrity**
   - `git -C /home/agent/converted-repo rev-parse --is-inside-work-tree`

2. **History checks**
   - `git -C /home/agent/converted-repo rev-list --all --count` (global)
   - `git -C /home/agent/converted-repo log --oneline | wc -l` (default-branch/HEAD-visible)
   - Ensure both satisfy required minimums for your task/harness.

3. **Branch/tag checks**
   - Non-main branches:  
     `git -C /home/agent/converted-repo for-each-ref --format='%(refname:short)' refs/heads | grep -Ev '^(master|main)$' | wc -l`
   - Tags:  
     `git -C /home/agent/converted-repo tag | wc -l`

4. **Result file consistency**
   - Recompute values, rewrite file, then `cat` it.
   - Confirm exact format/order/newline:
     ```
     commits=<int>
     branches=<int>
     tags=<int>
     ```

5. **Final gate**
   - Run provided test script (or equivalent pytest target) and confirm all pass.
```
