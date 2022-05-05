build:
	docker build -t text_finder .

up:
	docker-compose up -d

down:
	docker-compose down

test:
	poetry run pytest --cov=app tests

commit:
	cz commit

requirements:
	poetry export -o requirements.txt --dev

upgrade:
	poetry run alembic upgrade head

downgrade:
	poetry run alembic downgrade -1

downgrade_full:
	poetry run alembic downgrade base
