
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
	SMALLD_TOKEN=$$(cat .token) python -m monitoro
