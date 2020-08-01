
dev-setup:
	pip install pip-tools black pytype
	pip install -rrequirements.txt

pip-compile:
	pip-compile -o requirements.txt requirements.in

fmt:
	black monitoro/

lint:
	pytype monitoro/

run:
	python -m monitoro
