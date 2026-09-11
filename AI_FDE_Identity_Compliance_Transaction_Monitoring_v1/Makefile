PYTHON ?= python

.PHONY: install test eval preflight api smoke
install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m pytest -q

eval:
	$(PYTHON) scripts/run_integrated_evals.py

preflight:
	$(PYTHON) scripts/workshop_preflight.py
	$(PYTHON) scripts/run_integrated_evals.py

api:
	$(PYTHON) -m uvicorn src.app:app --host 127.0.0.1 --port 8000

smoke:
	$(PYTHON) scripts/smoke_server.py
