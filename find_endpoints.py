import validators
from collections import defaultdict
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from find_vulnerabilities import test_endpoint_methods
import csv

# Take input URL
# page_url = input("Enter the website URL: ").strip()

# Add http if missing


def extract_js_urls(page_url):
    external_js_url = []
    inline_scripts = []
    try:
        response = requests.get(page_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script')

        for script in scripts:
            if script.get('src'):
                src = urljoin(page_url, script['src'])
                external_js_url.append(src)
            elif script.string:
                inline_scripts.append(script.string)

        # js_urls = [urljoin(page_url, script['src']) for script in scripts]
        # return js_urls

    except Exception as e:
        print(f"Error fetching/parsing HTML: {e}")
    return external_js_url, inline_scripts

def find_api_endpoints(js_code):
    # Regex to find API endpoints (common patterns)
    # Matches: "https://...", '/api/endpoint', fetch("/api"), axios.get('/api')
    regex_patterns = [
        r"['\"](https?:\/\/[^\s'\"<>]+)['\"]",       # Full URLs
        r"['\"](\/api\/[^\s'\"<>]+)['\"]",            # /api/...
        r"fetch\(\s*['\"]([^'\"]+)['\"]",             # fetch('/api/...')
        r"axios\.\w+\(\s*['\"]([^'\"]+)['\"]",        # axios.get('/api/...')
        r"XMLHttpRequest\s*\(\s*['\"]([^'\"]+)['\"]", # Legacy XHR
    ]

    endpoints = set()
    for pattern in regex_patterns:
        matches = re.findall(pattern, js_code)
        for match in matches:
            if is_probable_api(match):
                endpoints.add(match)
            # if 'http' in match or match.startswith('/'):
            #     endpoints.add(match)

    return endpoints
def is_probable_api(url):
    # Ignore URLs with extensions like images, fonts, styles
    excluded_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2', '.ttf', '.css', '.ico', '.js')

    if any(url.lower().endswith(ext) for ext in excluded_extensions):
        return False

    # Prefer URLs that contain 'api', 'auth', 'user', etc.
    probable_keywords = ['api', 'auth', 'login', 'register', 'user', 'account', 'session', 'token', 'data']

    if any(keyword in url.lower() for keyword in probable_keywords):
        return True

    # If the URL looks RESTful (has /something/something without file extensions)
    if '/' in url and not '.' in url.split('/')[-1]:
        return True

    return False

def fetch_and_parse_js(js_urls):
    all_endpoints = set()
    for js_url in js_urls:
        try:
            response = requests.get(js_url)
            content = response.text
            print(f"\n🔍 Scanning: {js_url}")
            print(content[:50])  # Print first 50 characters
            endpoints = find_api_endpoints(content)
            if endpoints:
                print(f"✅ Found endpoints in {js_url}:")
                for ep in endpoints:
                    print("   ➤", ep)
                all_endpoints.update(endpoints)
            else:
                print("⚠️  No endpoints found.")
        except Exception as e:
            print(f"Error fetching {js_url}: {e}")
    return all_endpoints

def scan_inline_js(scripts):
    all_endpoints = set()
    for idx, js_code in enumerate(scripts):
        print(f"\n🔍 Scanning inline JS block #{idx+1}")
        endpoints = find_api_endpoints(js_code)
        if endpoints:
            print(f"✅ Found endpoints:")
            for ep in endpoints:
                print("   ➤", ep)
            all_endpoints.update(endpoints)
        else:
            print("⚠️  No endpoints found.")
    return all_endpoints

def save_endpoints(endpoints, base_url,filename = "found_endpoints.txt"):
    try:
        with open(filename,"+a") as f:
            for ep in sorted(endpoints):
                full_url = urljoin(base_url, ep)
                f.write(full_url + "\n")
        print(f"\n💾 Saved {len(endpoints)} endpoints to '{filename}'")
    except Exception as e:
        print(f"❌ Error writing to file: {e}")

def read_endpoints(filename = "found_endpoints.txt"):
    with open(filename, "r") as f:
        endpoints = [line.strip() for line in f if line.strip()]
    return endpoints

if __name__ == "__main__":
    user_url = input("Enter a URL: ").strip()
    js_urls, inline_js_blocks = extract_js_urls(user_url)
    all_found_endpoints = set()
    all_found_endpoints.update(fetch_and_parse_js(js_urls))
    all_found_endpoints.update(scan_inline_js(inline_js_blocks))
    status_summary = defaultdict(list)
    if all_found_endpoints:
        print("\n 🔗 All API endpoints found:")
        save_endpoints(all_found_endpoints, base_url=user_url)
        for ep in all_found_endpoints:
            print(" -",ep)
        # test_choice = input("\n🚀 Do you want to test each endpoint with HTTP methods? (y/n): ").strip().lower()
        # if test_choice == 'y':
        #     for endpoint in sorted(all_found_endpoints):
        #         methods_status = test_endpoint_methods(endpoint, base_url= user_url)
        #         for method, status in methods_status.items():
        #             status_summary[(method, status)].append(endpoint)
    else:
        print("\n🚫 No API endpoints found.")

    endpoints = read_endpoints("found_endpoints.txt")
    for endpoint in endpoints:
        print(f"🔍 Checking endpoint: {endpoint}")
        result = test_endpoint_methods(endpoint, base_url = user_url)
        for method, status in result.items():
            status_summary[(method, status)].append(endpoint)

    
    print("\n 📊 Summary Report:")
    print("-"*40)

    # for(method, status_code), endpoints in sorted(status_summary.items(), key= lambda x: (x[0][0], int (x[0][1]))):
    #     count = len(endpoints)
    #     print(f"{method:6} {status_code} ➤ {count} endpoint(s)")

    summary_csv = 'summary_report.csv'
    with open(summary_csv, mode='w', newline = '') as file:
        writer = csv.writer(file)
        writer.writerow(['HTTP Method','Status Code','Number of Endpoints'])
        for(method, status_code), endpoints in status_summary.items():
            try:
                status_code_int = int(status_code)
                writer.writerow([method, status_code_int, len(endpoints)])
                print(f"  ➔ {method:6} {status_code_int:3} → {len(endpoints)} endpoints")
            except ValueError:
                print(f"⚠️ Skipping error entry: {method}")
            # count = len(endpoints)
            # writer.writerow([method, status_code, count])
    print("-"*40)
    print(f"\n✅ Summary report saved to '{summary_csv}'")

