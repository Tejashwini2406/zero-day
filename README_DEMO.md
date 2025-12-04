Graph Builder demo

This repository contains a small demo that runs the `graph_builder` component
on a tiny, synthetic dataset and writes parquet window outputs.

Files added for demonstration:
- `demo/run_graph_builder_demo.py` — Python demo runner. Run with your project's Python interpreter.
- `scripts/move_unnecessary_to_archive.py` — conservative cleanup helper that moves obvious log/deployment files into `archive/` (safe; does not delete models).

How to run the demo (recommended from WSL or an environment where the repository is accessible):

1) Run the demo script with the repo's Python:

```powershell
# from Windows PowerShell (if using WSL, prefer running inside WSL where Python and packages are available)
python demo/run_graph_builder_demo.py
```

The demo will:
- attempt to install missing Python packages listed in `graph_builder/requirements.txt` if imports fail
- create `demo/sample_input.jsonl`
- run the graph builder and write parquet files to `demo/out/`

Notes and next steps:
- The demo runner makes a minimal environment modification (pip install) if needed. For a clean environment, create a venv first and run the script inside it.
- The cleanup script moves top-level logs into `archive/` for a tidy workspace. Review `archive/` before deleting anything permanently.

If you'd like, I can now:
- run the demo in this environment and fix any runtime errors
- expand the cleanup to archive more files or delete them permanently (after your confirmation)
- package `graph_builder` into a proper installable wheel / add an entry point
