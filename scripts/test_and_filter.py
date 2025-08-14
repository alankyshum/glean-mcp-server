#!/usr/bin/env python3
"""
Comprehensive test and filtering script for Glean MCP Server.

This script allows you to:
1. Test the Glean API with different queries
2. Compare raw vs filtered responses
3. Analyze response structure and content
4. Save results for inspection
"""
import asyncio
import json
import os
import sys
import argparse
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Simple dotenv replacement
def load_dotenv():
    """Simple .env file loader."""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        print(f"Warning: .env file not found at {env_path}")

from glean_client import GleanClient
from glean_filter import filter_glean_response


# NOTE: This file is a utility script, not a pytest test module. Provide a dummy
# variable to discourage pytest from treating async helpers as tests.
__all__ = ["main"]

async def _test_query(client: GleanClient, query: str, page_size: int = 5, max_snippet_size: int = 200, save_results: bool = True):
    """Test a single query and return analysis."""
    print(f"\n{'='*60}")
    print(f"Testing query: '{query}'")
    print('='*60)
    
    try:
        # Get raw results
        raw_results = await client.search(
            query=query,
            page_size=page_size,
            max_snippet_size=max_snippet_size
        )
        
        # Filter the results
        filtered_results = filter_glean_response(raw_results)
        filtered_results["query"] = query
        filtered_results["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Calculate compression
        raw_size = len(json.dumps(raw_results))
        filtered_size = len(json.dumps(filtered_results))
        compression = (1 - filtered_size / raw_size) * 100
        
        print(f"Raw response size: {raw_size:,} characters")
        print(f"Filtered response size: {filtered_size:,} characters")
        print(f"Compression: {compression:.1f}%")
        
        # Show results summary
        print(f"\nResults summary:")
        print(f"- Total results: {filtered_results.get('total_results', 0)}")
        print(f"- Backend time: {filtered_results.get('backendTimeMillis', 0)}ms")
        print(f"- Has more results: {filtered_results.get('hasMoreResults', False)}")
        
        if 'facets' in filtered_results:
            print(f"- Available facets: {len(filtered_results['facets'])}")
            for facet in filtered_results['facets'][:3]:  # Show first 3 facets
                print(f"  - {facet['name']}: {len(facet['buckets'])} options")
        
        # Show results by type
        results = filtered_results.get('results', [])
        if results:
            types = {}
            sources = {}
            for result in results:
                doc_type = result.get('docType', 'unknown')
                datasource = result.get('datasource', 'unknown')
                types[doc_type] = types.get(doc_type, 0) + 1
                sources[datasource] = sources.get(datasource, 0) + 1
            
            print(f"\nResults by type:")
            for doc_type, count in sorted(types.items()):
                print(f"  - {doc_type}: {count}")
            
            print(f"\nResults by source:")
            for source, count in sorted(sources.items()):
                print(f"  - {source}: {count}")
        
        # Show first few results
        for i, result in enumerate(results[:3]):  # Show first 3 results
            print(f"\nResult {i+1}:")
            print(f"  Title: {result.get('title', 'N/A')}")
            print(f"  Type: {result.get('docType', 'N/A')}")
            print(f"  Source: {result.get('datasource', 'N/A')}")
            url = result.get('url', 'N/A')
            print(f"  URL: {url[:80]}{'...' if len(url) > 80 else ''}")
            
            if 'author' in result:
                author = result['author']
                print(f"  Author: {author.get('name', 'N/A')}")
            
            if 'createTime' in result and result['createTime'] != "1970-01-01T00:00:00Z":
                print(f"  Created: {result['createTime']}")
            
            if 'snippets' in result:
                print(f"  Snippets: {len(result['snippets'])}")
                for j, snippet in enumerate(result['snippets'][:2]):  # Show first 2 snippets
                    text = snippet.get('text', snippet.get('snippet', ''))
                    if text:
                        print(f"    {j+1}: {text[:150]}{'...' if len(text) > 150 else ''}")
        
        # Save results if requested
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_query = safe_query.replace(' ', '_').lower()
            
            # Save filtered results
            filtered_filename = f"test_results/filtered_{safe_query}_{timestamp}.json"
            os.makedirs("test_results", exist_ok=True)
            with open(filtered_filename, 'w') as f:
                json.dump(filtered_results, f, indent=2, ensure_ascii=False)
            
            # Save raw results for comparison
            raw_filename = f"test_results/raw_{safe_query}_{timestamp}.json"
            with open(raw_filename, 'w') as f:
                json.dump(raw_results, f, indent=2, ensure_ascii=False)
            
            print(f"\nResults saved:")
            print(f"  Filtered: {filtered_filename}")
            print(f"  Raw: {raw_filename}")
        
        return {
            'query': query,
            'raw_size': raw_size,
            'filtered_size': filtered_size,
            'compression': compression,
            'total_results': filtered_results.get('total_results', 0),
            'backend_time': filtered_results.get('backendTimeMillis', 0)
        }
        
    except Exception as e:
        print(f"Error testing query '{query}': {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test and filter Glean API responses')
    parser.add_argument('queries', nargs='*', default=['documentation', 'API', 'python'], 
                       help='Queries to test (default: documentation, API, python)')
    parser.add_argument('--page-size', type=int, default=5, 
                       help='Number of results per query (default: 5)')
    parser.add_argument('--snippet-size', type=int, default=200, 
                       help='Maximum snippet size (default: 200)')
    parser.add_argument('--no-save', action='store_true', 
                       help='Do not save results to files')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    base_url = os.getenv("GLEAN_BASE_URL")
    cookies = os.getenv("GLEAN_COOKIES")
    
    if not base_url:
        print("Error: GLEAN_BASE_URL environment variable is required")
        return
    if not cookies:
        print("Error: GLEAN_COOKIES environment variable is required")
        return
    
    # Initialize client
    client = GleanClient(base_url=base_url, cookies=cookies)
    
    try:
        print(f"Testing {len(args.queries)} queries with Glean API")
        print(f"Page size: {args.page_size}, Snippet size: {args.snippet_size}")
        
        results = []
        for query in args.queries:
            result = await _test_query(
                client, 
                query, 
                page_size=args.page_size,
                max_snippet_size=args.snippet_size,
                save_results=not args.no_save
            )
            if result:
                results.append(result)
        
        # Summary
        if results:
            print(f"\n{'='*60}")
            print("SUMMARY")
            print('='*60)
            
            total_raw = sum(r['raw_size'] for r in results)
            total_filtered = sum(r['filtered_size'] for r in results)
            avg_compression = sum(r['compression'] for r in results) / len(results)
            
            print(f"Total queries tested: {len(results)}")
            print(f"Total raw response size: {total_raw:,} characters")
            print(f"Total filtered response size: {total_filtered:,} characters")
            print(f"Average compression: {avg_compression:.1f}%")
            print(f"Total results found: {sum(r['total_results'] for r in results)}")
            print(f"Average backend time: {sum(r['backend_time'] for r in results) / len(results):.0f}ms")
            
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
