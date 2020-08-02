
dev-setup:
	pip install pip-tools black pytype autoflake isort
	pip install -rrequirements.txt

pip-compile:
	pip-compile -o requirements.txt requirements.in

fmt:
	autoflake -ri --remove-all-unused-imports monitoro/
	isort monitoro/
	black monitoro/

lint:
	pytype monitoro/

run:
	python -m monitoro
