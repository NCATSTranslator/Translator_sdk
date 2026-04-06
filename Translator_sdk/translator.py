# A TranslatorSystem encapsulates a particular instance of a Translator system.
# This is valuable for two reasons:
#   1. It allows someone to choose to run TranslatorSDK on CI vs Test vs Prod
#      to compare newly deployed systems versus production versions.
#   2. During major changes, it can be used to store information on how particular
#      information can be accessed (e.g. via TRAPI calls versus direct API calls).

class TranslatorSystem:
    """
    Encapsulates a particular instance of a Translator system for SDK usage.
    """

    # For now, we'll just store the instance information in here, but in the
    # future it might be better to store this in an external YAML file.
    INSTANCE_INFO = {
        'dev': {
            'id': 'dev',
        },
        'ci': {
            'id': 'ci',
        },
        'test': {
            'id': 'test',
        },
        'prod': {
            'id': 'prod',
        },
    }

    def __init__(self, instance_id='prod'):
        """

        :param instance_id:
        """

        if instance_id not in TranslatorSystem.INSTANCE_INFO:
            raise ValueError(f"Invalid instance_id: {instance_id}. Supported values: {list(TranslatorSystem.INSTANCE_INFO.keys())}.")

        self.instance = TranslatorSystem.INSTANCE_INFO[instance_id]

    def id(self):
        return self.instance['id']

    def nameres_url(self):
        return self.instance['nameres_url']
