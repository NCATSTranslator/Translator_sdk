
# used May 30, 2025

import requests
import json
import pandas as pd

"""This is the root URL for the resource."""
URL = 'https://smart-api.info/api/query?q=tags.name:translator'

def get_translator_kp_info() -> tuple[pd.DataFrame, dict[str, str]]:
    """
    Get the SmartAPI Translator KP info from the smart-api.info API.
    Returns a DataFrame with the SmartAPI Translator KP info.

    Returns
    -------
    smartapi_df : pandas.DataFrame
        Dataframe containing information about the APIS [TODO]

    APInames : dict
        dict of API names to URLs


    Examples
    --------
    >>> Translator_KP_info, APInames = get_translator_kp_info()
    >>> print(Translator_KP_info.head())
    """
    # Get x-bte smartapi specs
    url = "https://smart-api.info/api/query?q=tags.name:translator AND tags.name:trapi&size=1000&sort=_seq_no&raw=1&fields=paths,servers,tags,components.x-bte*,info,_meta"
    response = requests.get(url)
    try:
        response.raise_for_status()
    except Exception:
        print(f"error downloading smartapi specs: {response.status_code}")
        exit()

    content = json.loads(response.content)
    smartapis = content["hits"]

    id_list = []
    title_list = []
    prod_url_list = []
    ci_url_list = []
    test_url_list = []
    for api in smartapis:
        
        
        ci_found = False
        test_found = False
        prod_found = False
        for i in range(len(api['servers'])):
            
            server = api['servers'][i]
            if 'x-maturity' not in server:
                print(f"Skipping server without x-maturity: {server}")
                
            else:
                if server['x-maturity'] == 'production':
                    # if prod_ur is not ars-prod.transltr.io
                    if server['url'] == 'https://ars-prod.transltr.io':
                        prod_url = server['url'] + '/ars/api/submit/'
                    else:
                        # if prod_url does not end with /, add '/query/' to the end
                        if server['url'].endswith('/'):
                            prod_url = server['url'] + 'query/'
                        else:
                            # if prod_url does not end with /, add '/query/' to the end
                            prod_url = server['url'] + '/query/'
                    
                    prod_found = True
                
                if server['x-maturity'] == 'staging' or server['x-maturity'] == 'development':
                    # if ci_url is not ars.ci.transltr.io
                    if server['url'] == 'https://ars.ci.transltr.io':
                        ci_url = server['url'] + '/ars/api/submit/'
                    else:
                        # if ci_url does not end with /, add '/query/' to the end
                        if server['url'].endswith('/'):
                            ci_url = server['url'] + 'query/'
                        else:
                            # if ci_url does not end with /, add '/query/' to the end
                            ci_url = server['url'] + '/query/'
                    ci_found = True

                if server['x-maturity'] == 'testing':
                    # if test_url is not ars-test.transltr.io
                    if server['url'] == 'https://ars.test.transltr.io':
                        test_url = server['url'] + '/ars/api/submit/'
                    else:
                        # if test_url does not end with /, add '/query/' to the end
                        if server['url'].endswith('/'):
                            test_url = server['url'] + 'query/'
                        else:
                            # if test_url does not end with /, add '/query/' to the end
                            test_url = server['url'] + '/query/'

                    test_found = True

        if not (prod_found or ci_found or test_found):
            print(api['info']['title'])
            print(f"Skipping server without production, staging or testing: {server}")
        else:
            id_list.append('https://smart-api.info/ui/'+api['_id'])
            title_list.append(api['info']['title'])
            if prod_found:
                prod_url_list.append(prod_url)
            else:
                prod_url = prod_url_list.append(None)

            if ci_found:
                ci_url_list.append(ci_url)
            else:
                ci_url = ci_url_list.append(None)
            if test_found:
                test_url_list.append(test_url)
            else:
                test_url = test_url_list.append(None)
                
    # write all the smartapis to a dataframe

    smartapi_df = pd.DataFrame({
        'id': id_list,
        'title': title_list,
        'prod_url': prod_url_list,
        'ci_url': ci_url_list,
        'test_url': test_url_list,
    })
    
    APInames = {}
    for i in range(len(smartapi_df)):
        if prod_url_list[i] is not None:
            #APInames[smartapi_df['title'][i]] = smartapi_df['prod_url'][i] + 'query/'
            APInames[smartapi_df['title'].values[i]] = prod_url_list[i]
        else:
            APInames[smartapi_df['title'].values[i]] = ci_url_list[i] 
    return smartapi_df, APInames
