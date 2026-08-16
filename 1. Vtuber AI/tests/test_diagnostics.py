from aina_companion.diagnostics import module_available


def test_nested_optional_module_can_be_missing_without_crashing():
    assert module_available("package_that_does_not_exist.child") is False
