.PHONY: validate validate-sources validate-lawful-learning-pack validate-learning-receipts validate-learning-receipts-negative validate-experience-records validate-experience-records-negative

validate: validate-sources validate-lawful-learning-pack validate-learning-receipts validate-learning-receipts-negative validate-experience-records validate-experience-records-negative
	@echo "OK: validate"

validate-sources:
	python3 scripts/validate_sources.py

validate-lawful-learning-pack:
	python3 scripts/validate_lawful_learning_pack.py

validate-learning-receipts:
	python3 scripts/validate_learning_receipts.py

validate-learning-receipts-negative:
	! python3 scripts/validate_learning_receipts.py tests/fixtures/learning_receipt.invalid_missing_claim_boundary.yaml

validate-experience-records:
	python3 scripts/validate_experience_records.py

validate-experience-records-negative:
	! python3 scripts/validate_experience_records.py tests/fixtures/experience_record.invalid_active_below_min_n.json
	! python3 scripts/validate_experience_records.py tests/fixtures/experience_record.invalid_improvement_without_delta.json
	! python3 scripts/validate_experience_records.py tests/fixtures/experience_record.invalid_tampered_delta.json
