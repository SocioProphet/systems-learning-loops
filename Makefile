.PHONY: validate validate-sources validate-lawful-learning-pack

validate: validate-sources validate-lawful-learning-pack
	@echo "OK: validate"

validate-sources:
	python3 scripts/validate_sources.py

validate-lawful-learning-pack:
	python3 scripts/validate_lawful_learning_pack.py
