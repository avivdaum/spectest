# RF Automation

Python automation framework for validating RF behavior across three modes:

- `no_hardware`: no RSA, no USRP (replay traces first, synthetic fallback)
- `rsa_only`: RSA connected, no USRP (analyzer health and pipeline checks)
- `full_hw`: RSA + USRP connected (end-to-end RF validation)

## Quick start

```powershell
python -m pip install -e .[dev]
python -m rf_automation --profile configs/run_profile.json --cases configs/cases.json
```

## Pytest markers

```powershell
pytest -m unit
pytest -m no_hardware
pytest -m rsa_only
pytest -m full_hw
```

## Lint and format

```powershell
black --check src tests
flake8 src tests
pytest -q -m "not full_hw and not rsa_only"
```

## CI/CD

- CI workflow (`.github/workflows/ci.yml`) runs Black, Flake8, and non-hardware tests on pushes and pull requests.
- Package workflow (`.github/workflows/package.yml`) builds distributables on tag pushes (`v*`) and publishes to PyPI if `PYPI_API_TOKEN` is configured in repository secrets.
