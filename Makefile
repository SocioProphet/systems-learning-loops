.PHONY: validate validate-sources validate-lawful-learning-pack validate-learning-receipts validate-learning-receipts-negative

validate: validate-sources validate-lawful-learning-pack validate-learning-receipts validate-learning-receipts-negative
	@echo "OK: validate"

validate-sources:
	python3 scripts/validate_sources.py

validate-lawful-learning-pack:
	python3 scripts/validate_lawful_learning_pack.py

validate-learning-receipts:
	python3 scripts/validate_learning_receipts.py

validate-learning-receipts-negative:
	! python3 scripts/validate_learning_receipts.py tests/fixtures/learning_receipt.invalid_missing_claim_boundary.yaml
