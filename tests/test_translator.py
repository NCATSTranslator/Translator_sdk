import pytest

from Translator_sdk.translator import TranslatorSystem


# Test instances.
def test_translator_instance_setup():
    # Should support: dev, ci, test, prod
    for instance_id in ['dev', 'ci', 'test', 'prod']:
        instance = TranslatorSystem(instance_id)
        assert instance.instance
        assert instance.id() == instance_id

    # Should not support: error
    with pytest.raises(ValueError, match="error_instance"):
        TranslatorSystem('error_instance')
