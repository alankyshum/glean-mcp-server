"""
Glean API response filtering utilities.
"""

from typing import Dict, Any


def filter_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter a single search result to extract only useful information.

    Args:
        result: Raw search result from Glean API

    Returns:
        Filtered result with only useful fields
    """
    filtered = {}

    # Basic document information
    if "document" in result:
        doc = result["document"]
        filtered["id"] = doc.get("id", "")
        filtered["title"] = doc.get("title", "")
        filtered["url"] = doc.get("url", "")
        filtered["docType"] = doc.get("docType", "")
        filtered["datasource"] = doc.get("datasource", "")

        # Extract useful metadata
        if "metadata" in doc:
            metadata = doc["metadata"]
            filtered["objectType"] = metadata.get("objectType", "")
            filtered["mimeType"] = metadata.get("mimeType", "")
            filtered["createTime"] = metadata.get("createTime", "")
            filtered["updateTime"] = metadata.get("updateTime", "")

            # Extract author information if available
            if "author" in metadata:
                filtered["author"] = metadata["author"]

            # Extract file size if available
            if "fileSize" in metadata:
                filtered["fileSize"] = metadata["fileSize"]

            # Extract custom data that might be useful
            if "customData" in metadata:
                custom_data = metadata["customData"]
                # Only include non-empty custom data
                useful_custom = {k: v for k, v in custom_data.items() if v}
                if useful_custom:
                    filtered["customData"] = useful_custom

    # Extract snippets (the actual content)
    if "snippets" in result:
        snippets = []
        for snippet in result["snippets"]:
            snippet_data = {
                "text": snippet.get("text", ""),
                "snippet": snippet.get("snippet", ""),
                "mimeType": snippet.get("mimeType", "text/plain"),
            }
            # Only include snippets with actual content
            if snippet_data["text"] or snippet_data["snippet"]:
                snippets.append(snippet_data)

        if snippets:
            filtered["snippets"] = snippets

    # Include title and URL from top level if not already included
    if "title" in result and "title" not in filtered:
        filtered["title"] = result["title"]
    if "url" in result and "url" not in filtered:
        filtered["url"] = result["url"]

    return filtered


def filter_glean_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter the entire Glean API response to extract only useful information.

    Args:
        response: Raw response from Glean API

    Returns:
        Filtered response with only useful fields
    """
    filtered_response = {}

    # Include basic response metadata
    if "requestID" in response:
        filtered_response["requestID"] = response["requestID"]

    if "backendTimeMillis" in response:
        filtered_response["backendTimeMillis"] = response["backendTimeMillis"]

    # Filter results
    if "results" in response:
        filtered_results = []
        for result in response["results"]:
            filtered_result = filter_result(result)
            # Only include results that have useful content
            if filtered_result and (
                filtered_result.get("title")
                or filtered_result.get("snippets")
                or filtered_result.get("url")
            ):
                filtered_results.append(filtered_result)

        filtered_response["results"] = filtered_results
        filtered_response["total_results"] = len(filtered_results)

    # Include facet results if they exist (useful for filtering)
    if "facetResults" in response:
        facets = []
        for facet in response["facetResults"]:
            if "displayName" in facet and "buckets" in facet:
                facet_data = {"name": facet.get("displayName", ""), "buckets": []}
                for bucket in facet["buckets"]:
                    if "displayName" in bucket and "count" in bucket:
                        facet_data["buckets"].append(
                            {"name": bucket["displayName"], "count": bucket["count"]}
                        )
                if facet_data["buckets"]:
                    facets.append(facet_data)

        if facets:
            filtered_response["facets"] = facets

    # Include spell check suggestions if available
    if "spellcheck" in response and response["spellcheck"]:
        spellcheck = response["spellcheck"]
        if "correctedQuery" in spellcheck:
            filtered_response["spellcheck"] = {
                "correctedQuery": spellcheck["correctedQuery"]
            }

    # Include pagination info
    if "hasMoreResults" in response:
        filtered_response["hasMoreResults"] = response["hasMoreResults"]

    if "cursor" in response:
        filtered_response["cursor"] = response["cursor"]

    return filtered_response
