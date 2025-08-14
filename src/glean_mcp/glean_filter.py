"""Glean API response filtering utilities (packaged)."""
from typing import Dict, Any


def filter_result(result: Dict[str, Any]) -> Dict[str, Any]:
    filtered: Dict[str, Any] = {}
    if 'document' in result:
        doc = result['document']
        filtered['id'] = doc.get('id', '')
        filtered['title'] = doc.get('title', '')
        filtered['url'] = doc.get('url', '')
        filtered['docType'] = doc.get('docType', '')
        filtered['datasource'] = doc.get('datasource', '')
        if 'metadata' in doc:
            metadata = doc['metadata']
            filtered['objectType'] = metadata.get('objectType', '')
            filtered['mimeType'] = metadata.get('mimeType', '')
            filtered['createTime'] = metadata.get('createTime', '')
            filtered['updateTime'] = metadata.get('updateTime', '')
            if 'author' in metadata:
                filtered['author'] = metadata['author']
            if 'fileSize' in metadata:
                filtered['fileSize'] = metadata['fileSize']
            if 'customData' in metadata:
                useful_custom = {k: v for k, v in metadata['customData'].items() if v}
                if useful_custom:
                    filtered['customData'] = useful_custom
    if 'snippets' in result:
        snippets = []
        for snippet in result['snippets']:
            snippet_data = {
                'text': snippet.get('text', ''),
                'snippet': snippet.get('snippet', ''),
                'mimeType': snippet.get('mimeType', 'text/plain')
            }
            if snippet_data['text'] or snippet_data['snippet']:
                snippets.append(snippet_data)
        if snippets:
            filtered['snippets'] = snippets
    if 'title' in result and 'title' not in filtered:
        filtered['title'] = result['title']
    if 'url' in result and 'url' not in filtered:
        filtered['url'] = result['url']
    return filtered


def filter_glean_response(response: Dict[str, Any]) -> Dict[str, Any]:
    filtered_response: Dict[str, Any] = {}
    if 'requestID' in response:
        filtered_response['requestID'] = response['requestID']
    if 'backendTimeMillis' in response:
        filtered_response['backendTimeMillis'] = response['backendTimeMillis']
    if 'results' in response:
        filtered_results = []
        for result in response['results']:
            filtered_result = filter_result(result)
            if filtered_result and (
                filtered_result.get('title') or filtered_result.get('snippets') or filtered_result.get('url')
            ):
                filtered_results.append(filtered_result)
        filtered_response['results'] = filtered_results
        filtered_response['total_results'] = len(filtered_results)
    if 'facetResults' in response:
        facets = []
        for facet in response['facetResults']:
            if 'displayName' in facet and 'buckets' in facet:
                facet_data = {'name': facet.get('displayName', ''), 'buckets': []}
                for bucket in facet['buckets']:
                    if 'displayName' in bucket and 'count' in bucket:
                        facet_data['buckets'].append({'name': bucket['displayName'], 'count': bucket['count']})
                if facet_data['buckets']:
                    facets.append(facet_data)
        if facets:
            filtered_response['facets'] = facets
    if 'spellcheck' in response and response['spellcheck']:
        spellcheck = response['spellcheck']
        if 'correctedQuery' in spellcheck:
            filtered_response['spellcheck'] = {'correctedQuery': spellcheck['correctedQuery']}
    if 'hasMoreResults' in response:
        filtered_response['hasMoreResults'] = response['hasMoreResults']
    if 'cursor' in response:
        filtered_response['cursor'] = response['cursor']
    return filtered_response

__all__ = ["filter_result", "filter_glean_response"]
