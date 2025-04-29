from playwright.sync_api import sync_playwright
def auto_scroll(page):
    page.evaluate("""
                  async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 100;
                        const timer = setInterval(() => {
                            window.scrollBy(0,distance);
                            totalHeight += distance;
                  
                            if(totalHeight >= document.body.scrollHeight){
                                clearInterval(timer);
                                resolve();
                            }
                        },300);
                  });
    }
""")
# Function to discover API endpoints dynamically
def discover_api_endpoints(url):
    api_endpoints = set()

    # Launch the browser (headless mode, no UI)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set headless=False to see the browser
        context = browser.new_context()
        page = context.new_page()

        # Function to capture every network request
        def handle_request(request):
            req_url = request.url
            if '/api/' in req_url or 'api.' in req_url:  # Look for 'api' in URL (customize as needed)
                api_endpoints.add(req_url)
                print(f"🔍 Found API request: {req_url}")

        # Attach the request handler to the page
        page.on("request", handle_request)

        # Go to the page URL
        print(f"🌐 Visiting page: {url}")
        page.goto(url)

        page.wait_for_selector('body')  # Replace with a specific element

        auto_scroll(page)
        page.wait_for_timeout(5000)

        # Optional: Scroll the page to load more dynamic content (if needed)
        # page.evaluate('window.scrollTo(0, document.body.scrollHeight)')

        # Optional: Click a button to trigger an API call (if the button appears on the page)
        try:
            page.click('section.wrap.t-centre a', timeout=10000)  # wait max 5 seconds
        except Exception as e:
            print(f"Button not found or clickable: {e}")
        # page.click('header a.btn-primary')  # Replace with the actual button selector

        # Optional: Wait for new content or requests (after interaction)
        # page.wait_for_selector('#dynamic-content')  # Replace with the content you expect

        # Optional: Click any other interaction to trigger more API calls
        try:
            page.click('#cc-ad.feature-ad a', timeout=5000)  # wait only 5 seconds
        except Exception as e:
            print(f"Button not found or not clickable: {e}")
        # page.click('#cc-ad.feature-ad a')

        # Wait for the page to load fully (adjust wait time if necessary)
        page.wait_for_timeout(8000)  # Wait 8 seconds (increase for slow sites)

        # Close the browser when done
        browser.close()

    return api_endpoints

def save_endpoints(endpoints, filename = "found_endpoints.txt"):
    with open(filename, "w") as f:
        for endpoint in endpoints:
            f.write(endpoint + "\n")
    print(f"\n ✅ Endpoints saved to {filename}")

# Example usage: run the dynamic scanner
if __name__ == "__main__":
    site_url = input("Enter the website URL to scan: ").strip()
    endpoints = discover_api_endpoints(site_url)
    
    if endpoints:
        print("\n✅ API Endpoints found:")
        for ep in endpoints:
            print(f"- {ep}")
    else:
        print("\n🚫 No API endpoints found.")
    
    save_endpoints(endpoints)
