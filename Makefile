.PHONY: validate score test loop

validate:
	python3 engine/validate.py

score:
	python3 engine/score.py

test:
	python3 -m unittest discover -s engine -p 'test_*.py' -v

loop: validate score
