init:
	cp examples/settings_dev.py settings.py
	poetry install
run-server:
	docker-compose up -d
	DJANGO_SETTINGS_MODULE=settings ./manage.py runserver 8080
lint:
	python -m flake8 **/*.py
format:
	python -m black **/*.py
