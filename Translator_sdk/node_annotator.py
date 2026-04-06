"""
This is a wrapper around the Node Annotator API.

API docs: https://annotator.transltr.io/
"""
import urllib.parse

import requests

URL = 'https://annotator.transltr.io/'
"""This is the root URL for the API."""

def status(url: str = URL):
    """
    Returns the status of the Node Annotator API.
    """
    response = requests.get(f'{url}status')
    response.raise_for_status()
    return response.json()


def lookup_curie(curie: str, url: str = URL, **kwargs):
    return lookup_curies([curie], url=url, **kwargs)[curie]


def lookup_curies(curies: list[str], url: str = URL, **kwargs):
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
    >>> lookup_curies(['MESH:D014867'])
    >>> lookup_curies(['NCIT:C34373', 'NCBIGene:1756'])
    """
    path = urllib.parse.urljoin(url, 'curie')
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


class NodeAnnotator:
    """A configured client for the Node Annotator API."""

    def __init__(self, url: str = URL):
        self.url = url

    def status(self):
        return status(url=self.url)

    def lookup_curie(self, curie: str, **kwargs):
        return lookup_curie(curie, url=self.url, **kwargs)

    def lookup_curies(self, curies: list[str], **kwargs):
        return lookup_curies(curies, url=self.url, **kwargs)
