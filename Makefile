lint:
	python -m flake8 **/*.py
format:
	python -m black **/*.py
nix-env:
	@nix-shell --command 'source "$$(pipenv --venv)/bin/activate"; return'