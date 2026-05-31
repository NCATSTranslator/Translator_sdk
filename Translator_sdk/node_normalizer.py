"""
This is a wrapper around the Node Normalizer API.

API docs: https://nodenorm.transltr.io/docs
OpenAPI spec: https://nodenormalization-sri.renci.org/openapi.json

The functions here form three layers:

- :func:`get_normalized_nodes_raw` is a thin layer over the HTTP endpoint. It is
  the only place that knows the endpoint URL and the names of its parameters.
- :func:`_node_from_response` is the only place that knows the shape of a
  NodeNorm response, turning one result object into a :class:`TranslatorNode`.
- :func:`get_normalized_nodes` is the ergonomic entry point most callers want.
"""
import urllib.parse

import requests

from .translator_node import TranslatorNode


URL = 'https://nodenorm.ci.transltr.io/'


def status():
    """
    Returns the status of the Node Normalizer API.
    """
    response = requests.get(f'{URL}status')
    response.raise_for_status()
    return response.json()


def get_normalized_nodes_raw(query: str | list[str],
        mode: str = 'post',
        *,
        conflate: bool = True,
        drug_chemical_conflate: bool = False,
        description: bool = False,
        individual_types: bool = False,
        include_taxa: bool = True,
        url: str | None = None) -> dict:
    """
    Calls the NodeNorm ``get_normalized_nodes`` endpoint and returns its raw JSON.

    This is a thin layer over the HTTP endpoint: it is the single place in the SDK
    that knows the endpoint URL and the names of its parameters. Most callers
    should use :func:`get_normalized_nodes` instead, which parses the response
    into :class:`TranslatorNode` objects.

    Parameters
    ----------
    query : str or list[str]
        A CURIE, or a list of CURIEs, to normalize.
    mode : str
        'post' to send a POST request (recommended for more than a few CURIEs);
        anything else sends a GET request. Default: 'post'.
    conflate : bool
        Apply gene/protein conflation. Default: True.
    drug_chemical_conflate : bool
        Apply drug/chemical conflation. Default: False.
    description : bool
        Ask NodeNorm to include descriptions for the identifiers it knows about.
        Default: False.
    individual_types : bool
        Ask NodeNorm to include the biolink type of each equivalent identifier.
        Default: False.
    include_taxa : bool
        Ask NodeNorm to include taxa for the normalized nodes. Default: True.
    url : str or None
        Base URL of the NodeNorm service. Defaults to the module-level :data:`URL`
        constant (``https://nodenorm.ci.transltr.io/``).

    Returns
    -------
    A dict mapping each queried CURIE to its raw NodeNorm result object, or to
    ``None`` when NodeNorm has no record of that CURIE.
    """
    base = url if url is not None else URL
    path = urllib.parse.urljoin(base if base.endswith('/') else base + '/', 'get_normalized_nodes')
    options = {
        'conflate': conflate,
        'drug_chemical_conflate': drug_chemical_conflate,
        'description': description,
        'individual_types': individual_types,
        'include_taxa': include_taxa,
    }
    if mode == 'post':
        # CURIEs sent to POST must be a list. If a single CURIE is given, we wrap it.
        curies = [query] if isinstance(query, str) else list(query)
        response = requests.post(path, json={'curies': curies, **options})
    else:
        response = requests.get(path, params={'curie': query, **options})
    response.raise_for_status()
    return response.json()


def _node_from_response(raw_node: dict, return_equivalent_identifiers: bool = True) -> TranslatorNode:
    """
    Builds a :class:`TranslatorNode` from a single NodeNorm result object.

    This is the single place in the SDK that knows the shape of a NodeNorm
    ``get_normalized_nodes`` response. ``raw_node`` is the (non-``None``) value
    that NodeNorm returns for one queried CURIE.
    """
    node = TranslatorNode(raw_node['id']['identifier'])
    node.label = raw_node['id'].get('label')
    node.description = raw_node['id'].get('description')
    if 'type' in raw_node:
        node.types = raw_node['type']
    if 'taxa' in raw_node:
        node.taxa = raw_node['taxa']
    if 'information_content' in raw_node:
        node.information_content = raw_node['information_content']
    if return_equivalent_identifiers and 'equivalent_identifiers' in raw_node:
        node.synonyms = [eq.get('label') for eq in raw_node['equivalent_identifiers']]
        node.curie_synonyms = [eq['identifier'] for eq in raw_node['equivalent_identifiers']]
    return node


def get_normalized_nodes(query: str | list[str],
        return_equivalent_identifiers: bool = False,
        mode: str = 'get',
        *,
        conflate: bool = True,
        drug_chemical_conflate: bool = False,
        description: bool = False,
        individual_types: bool = False,
        include_taxa: bool = True):
    """
    Normalizes a CURIE (or a list of CURIEs) using NodeNorm.

    Given a CURIE or a list of CURIEs, this returns either a single
    :class:`TranslatorNode` or a dict mapping each queried CURIE to a
    :class:`TranslatorNode` (or ``None`` when NodeNorm has no record of it).

    Parameters
    ----------
    query : str or list[str]
        A CURIE, or a list of CURIEs, to normalize.
    return_equivalent_identifiers : bool
        Whether to populate the returned node(s) with their equivalent
        identifiers (as ``synonyms`` and ``curie_synonyms``). Default: False.
    mode : str
        'post' to send a POST request (recommended for more than a few CURIEs);
        anything else sends a GET request. Default: 'get'.
    conflate : bool
        Apply gene/protein conflation. Default: True.
    drug_chemical_conflate : bool
        Apply drug/chemical conflation. Default: False.
    description : bool
        Ask NodeNorm to include a description for each normalized node.
        Default: False.
    individual_types : bool
        Ask NodeNorm to include the biolink type of each equivalent identifier.
        Default: False.
    include_taxa : bool
        Ask NodeNorm to include taxa for the normalized nodes. Default: True.

    Returns
    -------
    If query is a single CURIE, returns a single TranslatorNode (or None).

    If query is a list of CURIEs, returns a dict mapping each queried CURIE to a
    TranslatorNode (or None) for every CURIE in the query.

    Examples
    --------
    >>> get_normalized_nodes('MESH:D014867')
    TranslatorNode(curie='CHEBI:15377', label='Water', types=['biolink:SmallMolecule', ...], ...)
    """
    raw_nodes = get_normalized_nodes_raw(query, mode=mode,
        conflate=conflate,
        drug_chemical_conflate=drug_chemical_conflate,
        description=description,
        individual_types=individual_types,
        include_taxa=include_taxa)
    normalized = {
        curie: None if raw_node is None else _node_from_response(raw_node, return_equivalent_identifiers)
        for curie, raw_node in raw_nodes.items()
    }
    if isinstance(query, str):
        return normalized[query]
    return normalized


def get_preferred_names(id_list:list[str], batch_limit=500, **kwargs) -> dict[str, str]:
    """
    Converts a list of CURIEs to their preferred names using NodeNorm. This calls get_normalized_nodes.

    Parameters
    ----------
    query : list
        Query CURIE
    batch_limit: int
        Limit for how many IDs to use in one query. Default: 500
    **kwargs
        Other arguments to `get_normalized_nodes` (e.g. `conflate` for gene-protein conflation, `drug_chemical_conflate` for drug-chemical conflation - see https://nodenorm.transltr.io/docs#/default/get_normalized_node_handler_get_normalized_nodes_get)

    Returns
    -------
    Returns a dict mapping CURIE ids to preferred names.
    """
    name_map = {}
    unmapped_ids = []
    for index in range(0, len(id_list), batch_limit):
        id_sublist = id_list[index:index + batch_limit]
        normalized_nodes = get_normalized_nodes(id_sublist, mode='post', **kwargs)
        for curie in id_sublist:
            if curie not in normalized_nodes or normalized_nodes[curie] is None:
                unmapped_ids.append(curie)
                name_map[curie] = curie
            else:
                label = normalized_nodes[curie].label
                if label is None:
                    print(curie + ": no preferred name")
                    label = curie
                name_map[curie] = label
    if len(unmapped_ids) > 0:
        print("NodeNorm does not know about these identifiers: " + ",".join(unmapped_ids))
    return name_map


def ID_convert_to_preferred_name_nodeNormalizer(id_list):
    '''
    Convert a list of CURIEs to their preferred names using NodeNorm.
    Arg:
        id_list: list of CURIEs to be converted
    Returns:
        dic_id_map: dictionary mapping CURIEs to their preferred names
    Example:
        dic_id_map = ID_convert_to_preferred_name_nodeNormalizer(["NCBIGene:1234", "NCBIGene:5678"])
    '''
    dic_id_map = {}
    unrecoglized_ids = []
    recoglized_ids = []
    # To convert a CURIE to a preferred name, you don't need NameLookup at all -- NodeNorm can
    # do this by itself!
    NODENORM_BASE_URL = "https://nodenorm.transltr.io"  # Adjust this if you need NodeNorm TEST, CI or DEV.
    NODENORM_BATCH_LIMIT = 900                          # Adjust this if you start getting errors from NodeNorm.
    NODENORM_GENE_PROTEIN_CONFLATION = True             # Change to False if you don't want gene/protein conflation.
    NODENORM_DRUG_CHEMICAL_CONFLATION = False           # Change to True if you want drug/chemical conflation.

    # split id_list into batches of at most NODENORM_BATCH_LIMIT entries
    for index in range(0, len(id_list), NODENORM_BATCH_LIMIT):
        id_sublist = id_list[index:index + NODENORM_BATCH_LIMIT]

        # print(f"id_sublist: {id_sublist}")

        # Query NodeNorm with https://nodenorm.transltr.io/docs#/default/get_normalized_node_handler_get_normalized_nodes_get
        response = requests.post(NODENORM_BASE_URL + '/get_normalized_nodes', json={
            "curies": id_sublist,
            "description": False,   # Change to True if you want descriptions from any identifiers we know about.
            "conflate": NODENORM_GENE_PROTEIN_CONFLATION,
            "drug_chemical_conflate": NODENORM_DRUG_CHEMICAL_CONFLATION,
        })
        if not response.ok:
            raise RuntimeError("Error: NodeNorm request failed with status code " + str(response.status_code))

        results = response.json()
        for curie in id_sublist:
            if curie in results and results[curie]:
                identifier = results[curie].get('id', {})
                if 'identifier' in identifier and identifier['identifier'] != curie:
                    recoglized_ids.append(curie)
                    #print(f"NodeNorm normalized {curie} to {identifier['identifier']} " +
                    #      f"with gene-protein conflation {NODENORM_GENE_PROTEIN_CONFLATION} and " +
                    #      f"with drug-chemical conflation {NODENORM_DRUG_CHEMICAL_CONFLATION}.")
                label = identifier.get('label')
                dic_id_map[curie] = label
                if not label:
                    print(curie + ": no preferred name")
                    dic_id_map[curie] = curie
            else:
                unrecoglized_ids.append(curie)

                dic_id_map[curie] = curie
    if len(unrecoglized_ids) > 0:
        print("NodeNorm does not know about these identifiers: " + ",".join(unrecoglized_ids))

    return dic_id_map
