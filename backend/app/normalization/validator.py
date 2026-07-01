ALLOWED_TIMESTAMP_QUALITY = {
    "SOURCE_OCCURRED_AT",
    "BACKFILLED_FROM_CREATED_AT",
    "MISSING_TIMESTAMP",
}

REQUIRED_FIELDS = {
    "event_id",
    "event_type",
    "timestamp_quality",
}


class ValidationResult:
    def __init__(self, is_valid: bool, errors=None):
        self.is_valid = is_valid
        self.errors = errors or []

    def to_dict(self):
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
        }


class EventValidator:
    def validate_rows(self, rows):
        errors = []

        for index, row in enumerate(rows, start=2):
            for field in REQUIRED_FIELDS:
                if not row.get(field):
                    errors.append(f"Row {index}: missing required field '{field}'")

            timestamp_quality = row.get("timestamp_quality")
            if timestamp_quality and timestamp_quality not in ALLOWED_TIMESTAMP_QUALITY:
                errors.append(
                    f"Row {index}: invalid timestamp_quality '{timestamp_quality}'"
                )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
        )