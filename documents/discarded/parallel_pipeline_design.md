# Design Specification: Parallel & Resumable Pipelines

## 1. Problem Statement
As the featurization pipeline grows, sequential execution of independent feature engineering stages (e.g., separate logic for Borrower, Lender, and Property) becomes a performance bottleneck. Furthermore, if a pipeline fails at stage 9 of 10, the current architecture requires a full re-run, wasting computational resources and time.

## 2. Approach
The design moves from a **State-Mutation** model (where stages modify a global context in-place) to a **Functional Producer** model. Stages within a parallel block operate on read-only views of the data and return "Feature Patches." An orchestration layer manages execution state via a persistent Runbook.

## 3. Design Components
- **Execution Blocks**: The configuration will distinguish between `sequential` blocks (dependent) and `parallel` blocks (independent).
- **Feature Patches**: Parallel stages return a DataFrame containing only new columns, indexed identically to the source data.
- **The Runbook**: A `runbook.json` file tracks the UUID of the run, stage status (success/failed), execution time, and error traces.
- **Reconciliation (The Joiner)**: A system-level stage that horizontally concatenates successful feature patches back to the primary data matrix.

## 4. Solution Architecture
1. **Isolation**: Use `concurrent.futures.ProcessPoolExecutor` to spawn separate processes for parallel stages.
2. **Immutability**: The primary `context["data"]` is treated as read-only during parallel execution to avoid race conditions.
3. **Resume Logic**: The `PipelineRunner` consults the Runbook before execution. If a `--resume` flag is present, it skips stages marked as `success`.

## 5. Paths of Execution

### Happy Path
1. Runner identifies a parallel block in `featurizer_config.yaml`.
2. Stages are dispatched to the process pool.
3. All stages return status `success` and a `FeaturePatch`.
4. The Joiner merges patches into the main DataFrame.
5. Runbook is updated and the pipeline continues to the next block.

### Error Path
1. One or more stages in a parallel block raise an exception.
2. The Runner catches the exception, kills pending tasks, and logs the specific error to the Runbook.
3. The pipeline exits gracefully without saving a corrupted/incomplete dataset.
4. **Resolution**: The user fixes the failing script and executes `run --resume`.
5. The Runner executes *only* the failed stages and then proceeds to the Joiner.

## 6. Testing Strategy
- **Real Data Mandate**: Test using the SBA migration dataset.
- **Concurrency Test**: Verify that independent stages do not interfere with each other's calculations.
- **State Persistence Test**: Manually induce a failure in a custom script, fix it, and verify the `resume` command skips previously successful work.
- **Alignment Test**: Verify that the horizontal concatenation correctly aligns rows based on the index after parallel processing.

## 7. Implementation Note
This design is to be implemented **after** the transition of individual stages to return explicit results rather than mutating the shared context.