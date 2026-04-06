import pytest

from Translator_sdk.translator import TranslatorSystem
from Translator_sdk.name_resolver import NameResolver
from Translator_sdk.node_normalizer import NodeNormalizer
from Translator_sdk.node_annotator import NodeAnnotator


# Test instances.
def test_translator_instance_setup():
    # Should support: exp, dev, ci, test, prod
    for instance_id in ['exp', 'dev', 'ci', 'test', 'prod']:
        instance = TranslatorSystem(instance_id)
        assert instance.instance
        assert instance.id() == instance_id

    # Should not support: error
    with pytest.raises(ValueError, match="error_instance"):
        TranslatorSystem('error_instance')


def test_translator_url_accessors():
    ci = TranslatorSystem('ci')
    assert ci.nameres_url() == 'https://name-lookup.ci.transltr.io/'
    assert ci.nodenorm_url() == 'https://nodenorm.ci.transltr.io/'

    prod = TranslatorSystem('prod')
    assert prod.nameres_url() == 'https://name-lookup.transltr.io/'
    assert prod.nodenorm_url() == 'https://nodenorm.transltr.io/'


def test_translator_factory_methods():
    ci = TranslatorSystem('ci')

    nr = ci.name_resolver()
    assert isinstance(nr, NameResolver)
    assert nr.base_url == 'https://name-lookup.ci.transltr.io/'

    nn = ci.node_normalizer()
    assert isinstance(nn, NodeNormalizer)
    assert nn.base_url == 'https://nodenorm.ci.transltr.io/'

    na = ci.node_annotator()
    assert isinstance(na, NodeAnnotator)
    assert na.base_url == 'https://annotator.transltr.io/'


def test_service_class_default_urls():
    assert NameResolver().base_url == NameResolver.DEFAULT_URL
    assert NodeNormalizer().base_url == NodeNormalizer.DEFAULT_URL
    assert NodeAnnotator().base_url == NodeAnnotator.DEFAULT_URL


def test_service_class_custom_url():
    custom = 'https://name-lookup.test.transltr.io/'
    nr = NameResolver(base_url=custom)
    assert nr.base_url == custom
