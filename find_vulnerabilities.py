import requests
from urllib.parse import urljoin
def test_endpoint_methods(endpoint, base_url):
    methods = ['GET', 'POST', 'PUT', 'DELETE']
    results = {}

    # Make full URL if it's a relative path
    if base_url and endpoint.startswith('/'):
        url = urljoin(base_url, endpoint)
    else:
        url = endpoint

    print(f"\n🔎 Testing methods for: {url}")

    # Use OPTIONS to check allowed methods first
    try:
        opt = requests.options(url, timeout=5)
        allow = opt.headers.get('Allow')
        if allow:
            print(f"📋 Allow header: {allow}")
    except:
        pass

    for method in methods:
        try:
            response = requests.request(method, url, timeout=5)
            results[method] = response.status_code
            print(f"  {method:6} ➤ {response.status_code}")
            # return response.status_code
        except Exception as e:
            results[method] = str(e)
            print(f"  {method:6} ➤ Error: {e}")
            # return None

    return results
