class ValidateError(Exception):
	pass


class RequiredFieldError(ValidateError):
	pass


class ExtraFieldError(ValidateError):
	pass


class ModelLoadError(Exception):
	pass
