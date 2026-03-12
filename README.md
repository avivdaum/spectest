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

