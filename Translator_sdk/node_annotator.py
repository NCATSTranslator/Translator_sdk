"""
This is a wrapper around the Node Annotator API.

API docs: https://annotator.transltr.io/
"""
import urllib.parse

import requests


class NodeAnnotator:
    """A configured client for the Node Annotator API."""

    DEFAULT_URL = 'https://annotator.transltr.io/'

    def __init__(self, base_url: str = DEFAULT_URL):
        self.base_url = base_url

    def status(self):
        """
        Returns the status of the Node Annotator API.
        """
        response = requests.get(f'{self.base_url}status')
        response.raise_for_status()
        return response.json()

    def lookup_curie(self, curie: str, **kwargs):
        return self.lookup_curies([curie], **kwargs)[curie]

    def lookup_curies(self, curies: list[str], **kwargs):
        """
        A wrapper around the `curies` API endpoint. Given a list of CURIEs, this returns a dictionary where each
        CURIE is mapped to a list of annotations.

        Parameters
        ----------
        curies : list[str]
            A list of CURIEs to look up.
        **kwargs
            Other arguments to `curie`. Some possible arguments: `raw=true` returns annotation fields in their original
            data structure before transformation, `fields` can be used to provide a comma-separated list of annotation fields
            you are interested in, and `include_extra=true` (default true) uses external APIs to provide additional annotations.

        Returns
        -------
        A dictionary with keys as the input CURIEs and the values as dictionaries of annotations and their values.

        Examples
        --------
        >>> NodeAnnotator().lookup_curies(['MESH:D014867'])
        >>> NodeAnnotator().lookup_curies(['NCIT:C34373', 'NCBIGene:1756'])
        """
        path = urllib.parse.urljoin(self.base_url, 'curie')
        response = requests.post(path, json={'ids': curies, **kwargs})
        response.raise_for_status()

        result = response.json()
        if len(result) == 0:
            raise LookupError('No matching CURIE found for the given string ' + curies)

        results = response.json()

        for curie in results:
            # NodeAnnotator sometimes return a list of a single item. If so, we can unwrap it here.
            if len(results[curie]) == 1:
                results[curie] = results[curie][0]

        return results


# ---------------------------------------------------------------------------
# Deprecated module-level functions
# These delegate to NodeAnnotator and will be removed before v1.0.
# ---------------------------------------------------------------------------

def status(base_url: str = NodeAnnotator.DEFAULT_URL):
    return NodeAnnotator(base_url).status()


def lookup_curie(curie: str, base_url: str = NodeAnnotator.DEFAULT_URL, **kwargs):
    return NodeAnnotator(base_url).lookup_curie(curie, **kwargs)


def lookup_curies(curies: list[str], base_url: str = NodeAnnotator.DEFAULT_URL, **kwargs):
    return NodeAnnotator(base_url).lookup_curies(curies, **kwargs)
