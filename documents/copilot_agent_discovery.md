Since you are using [GitHub Copilot](https://github.com/features/copilot), you have a major advantage:  =Copilot natively looks for a repo-level instruction file to understand your workspace context= . You do not need to stand up any running servers or build specialized integration plugins. [1, 2]

By utilizing the files that are already visible in your `rajivsam/featurization` workspace tree, you can make Copilot context-aware in just a few specific steps.

---

## Step 1: Initialize the Copilot Instruction Anchor

GitHub Copilot automatically searches for a specific file pattern at the root of your repository to act as its guiding system prompt. [1, 2]

Create a directory named `.github` in your root directory if it does not already exist, and create a file inside it called `copilot-instructions.md`:
`your_project_root/.github/``copilot-instructions.md` [3, 4]

## Step 2: Write the Discovery Manifest inside `copilot-instructions.md`

Populate the file with exact instructions telling Copilot what your package does, when it should be invoked, and where the core logic lives.

Paste this tailored, markdown-native configuration directly into `.github/``copilot-instructions.md`:

```markdown
# KMDS Featurization Pipeline Context

## Core Capabilities
This repo is a local data-engineering CLI for turning tabular data into model-ready datasets using a horizontal-merge architecture.

## Tool Execution Rules
- Always refer to `featurizer_config.yaml` for data paths.
- All operations must be relative to the `working_dir`.

## Required File Context Mapping
When handling pipeline tasks, instruct Copilot to read:
1. Cross-Sectional Data: `documents/user_guide_cs_featurization.md`
2. Survival Analysis: `documents/survival_featurization_pipeline.md`
3. Logic: `src/` and `featurization_scripts/featurization.py`

## CLI Commands
- Initialize: `featurization-cli init --working-dir <dir> --metadata-file <file> --data-file <file>`
- Bootstrap: `featurization-cli bootstrap --working-dir <dir> --metadata-file <file> --data-file <file>`
- Run: `featurization-cli run --working-dir <dir>`
- Test: `pytest -q tests/test_sba_pipeline.py`
```

---

## Step 3: Verify the Copilot Settings in Your IDE

Ensure Copilot loads your instruction file automatically: [1, 5]

* VS Code: Works natively upon opening the repository.
* Visual Studio: Enable *"Custom instructions from .github/copilot-instructions.md"* in Tools > Options > GitHub > Copilot > Copilot Chat. [1, 4, 6]

---

## How Your Workflow Changes

Copilot will now automatically use the rules in `.github/``copilot-instructions.md` to guide its suggestions, such as referencing the correct documentation files for specific tasks. [1, 2]

Would you like to build an automated GitHub Action that validates your pipeline configuration format every time a new push or pull request occurs?

[1] [https://www.youtube.com](https://www.youtube.com/watch?v=BdZWFlFiHHY&t=10)

[2] [https://code.visualstudio.com](https://code.visualstudio.com/docs/copilot/customization/custom-instructions)

[3] [https://github.com](https://github.com/orgs/community/discussions/182842)

[4] [https://www.youtube.com](https://www.youtube.com/watch?v=zwIlqbTHjac)

[5] [https://www.youtube.com](https://www.youtube.com/watch?v=6-QsbsHAN4g&t=9)

[6] [https://learn.microsoft.com](https://learn.microsoft.com/en-us/ssms/github-copilot/custom-instructions)
