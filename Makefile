.PHONY: validate score test loop observe

validate:
	python3 engine/validate.py

score:
	python3 engine/score.py

observe:
	python3 engine/observe.py

test:
	python3 -m unittest discover -s engine -p 'test_*.py' -v

loop: validate score observe
