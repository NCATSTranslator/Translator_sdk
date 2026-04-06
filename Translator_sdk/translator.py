# A TranslatorSystem encapsulates a particular instance of a Translator system.
# This is valuable for two reasons:
#   1. It allows someone to choose to run TranslatorSDK on CI vs Test vs Prod
#      to compare newly deployed systems versus production versions.
#   2. During major changes, it can be used to store information on how particular
#      information can be accessed (e.g. via TRAPI calls versus direct API calls).

from .name_resolver import NameResolver
from .node_normalizer import NodeNormalizer
from .node_annotator import NodeAnnotator


class TranslatorSystem:
    """
    Encapsulates a particular instance of a Translator system for SDK usage.
    """

    # URLs sourced from https://github.com/TranslatorSRI/babel-validation/blob/main/tests/targets.ini
    # NodeAnnotator does not have per-environment URLs in that file; prod is used for all environments.
    INSTANCE_INFO = {
        'exp': {
            'id': 'exp',
            'nameres_url': 'https://name-resolution-exp.apps.renci.org/',
            'nodenorm_url': 'https://nodenormalization-exp.apps.renci.org/',
            'annotator_url': 'https://annotator.transltr.io/',
        },
        'dev': {
            'id': 'dev',
            'nameres_url': 'https://name-resolution-sri.renci.org/',
            'nodenorm_url': 'https://nodenormalization-sri.renci.org/',
            'annotator_url': 'https://annotator.transltr.io/',
        },
        'ci': {
            'id': 'ci',
            'nameres_url': 'https://name-lookup.ci.transltr.io/',
            'nodenorm_url': 'https://nodenorm.ci.transltr.io/',
            'annotator_url': 'https://annotator.transltr.io/',
        },
        'test': {
            'id': 'test',
            'nameres_url': 'https://name-lookup.test.transltr.io/',
            'nodenorm_url': 'https://nodenorm.test.transltr.io/',
            'annotator_url': 'https://annotator.transltr.io/',
        },
        'prod': {
            'id': 'prod',
            'nameres_url': 'https://name-lookup.transltr.io/',
            'nodenorm_url': 'https://nodenorm.transltr.io/',
            'annotator_url': 'https://annotator.transltr.io/',
        },
    }

    def __init__(self, instance_id='prod'):
        """
        :param instance_id: One of 'exp', 'dev', 'ci', 'test', 'prod'.
        """

        if instance_id not in TranslatorSystem.INSTANCE_INFO:
            raise ValueError(f"Invalid instance_id: {instance_id}. Supported values: {list(TranslatorSystem.INSTANCE_INFO.keys())}.")

        self.instance = TranslatorSystem.INSTANCE_INFO[instance_id]

    def id(self):
        return self.instance['id']

    def nameres_url(self):
        return self.instance['nameres_url']

    def nodenorm_url(self):
        return self.instance['nodenorm_url']

    def annotator_url(self):
        return self.instance['annotator_url']

    def name_resolver(self) -> NameResolver:
        """Return a NameResolver configured for this Translator instance."""
        return NameResolver(url=self.instance['nameres_url'])

    def node_normalizer(self) -> NodeNormalizer:
        """Return a NodeNormalizer configured for this Translator instance."""
        return NodeNormalizer(url=self.instance['nodenorm_url'])

    def node_annotator(self) -> NodeAnnotator:
        """Return a NodeAnnotator configured for this Translator instance."""
        return NodeAnnotator(url=self.instance['annotator_url'])
