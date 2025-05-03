init:
	cp examples/settings_dev.py settings.py
init-standalone:
	cp examples/settings_dev_standalone.py settings.py
run-server:
	docker-compose up -d
	DJANGO_SETTINGS_MODULE=settings ./manage.py runserver 8080
lint:
	python -m flake8 **/*.py
format:
	python -m black **/*.py
