# JARVIS — Windows environment setup

## Recommended Python version

Use **Python 3.12.x (64-bit)** for the project environment. Avoid reusing a virtual environment created with another Python version.

## Fresh installation

Run these commands from the `JARVIS` project root in Command Prompt or PowerShell:

```bat
py -3.12 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

If `py -3.12` is not recognized, install Python 3.12 (64-bit) and make sure the Python Launcher is enabled, or create the environment with the full path to the Python 3.12 executable.

## Verify installation and run the Phase 2/3 integration tests

```bat
python -m pip --version
python -m pytest --version
python -m pytest agent_engine\tests\integration\ -q
```

To run the targeted state-integrity tests:

```bat
python -m pytest agent_engine\tests\unit\test_state_manager_checkpoints.py agent_engine\tests\unit\test_state_manager_registry.py agent_engine\tests\integration\test_decision_state_bridge.py -q
```

## Notes

- Always use `python -m pip` and `python -m pytest` after activating `venv`; this ensures packages are installed into and run from the same interpreter.
- PyTorch is a large dependency. Installation time and wheel availability depend on the Python version, Windows architecture, and CPU/CUDA setup. The requirements file uses the standard pip package; if you specifically need a CUDA build, follow the official PyTorch selector for your machine.
- Hugging Face model weights/tokenizers are separate from Python packages. A model-backed feature may need model assets downloaded/configured before it can run. The Phase 2/3 integration tests use failure-isolation/fallback paths and do not imply that all optional model assets are present.
- If installation fails, copy the **first error above the final pip error**; that line usually identifies the actual package or interpreter incompatibility.
