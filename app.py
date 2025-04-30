from flask import Flask, render_template, request
from find_endpoints import extract_js_urls, fetch_and_parse_js, scan_inline_js, save_endpoints
from find_vulnerabilities import test_endpoint_methods
from collections import defaultdict

app = Flask(__name__)


VULNERABILITY_TYPES = {
    200: 'Secure - OK',
    201: 'Secure - Created',
    400: 'Vulnerable - Bad Request',
    401: 'Vulnerable - Unauthorized',
    403: 'Vulnerable - Forbidden',
    404: 'Vulnerable - Not Found',
    405: 'Vulnerable - Method Not Allowed',
    500: 'Vulnerable - Internal Server Error',
    503: 'Vulnerable - Service Unavailable'
}

def classify_vulnerability(status_code):
    return VULNERABILITY_TYPES.get(status_code, 'Unknown Status')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    url = request.form['url'].strip()
    js_urls, inline_js = extract_js_urls(url)
    found_endpoints = set()
    found_endpoints.update(fetch_and_parse_js(js_urls))
    found_endpoints.update(scan_inline_js(inline_js))
    save_endpoints(found_endpoints, url)

    status_summary = defaultdict(list)
    endpoint_results = []

    
    for endpoint in found_endpoints:
        result = test_endpoint_methods(endpoint, base_url=url)
        endpoint_data = {
            'endpoint': endpoint,
            'methods': result,
            'vulnerabilities': {method: classify_vulnerability(status) for method, status in result.items()}
        }
        endpoint_results.append(endpoint_data)

    return render_template('index.html', results=endpoint_results)

if __name__ == '__main__':
    app.run(debug=True)
