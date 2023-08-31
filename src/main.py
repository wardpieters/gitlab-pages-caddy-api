from flask import Flask, request
import requests
import os

app = Flask(__name__)


@app.route('/', methods=['GET'])
def default():
    # return a html format string that is rendered in the browser
	return "It's working!"


@app.route('/api', methods=['GET'])
def on_demand_tls():
	domain = request.args.get('domain')

	if domain is None:
		return "Error: domain argument is not set", 500
    
	# Always return 200 OK when crazy mode is enabled.
	# pls don't use this in production :D
	if os.getenv('CRAZY_MODE', 'False').lower() == 'true':
		return "", 200

	# Check if the domain ends in GITLAB_PAGES_DOMAIN
	gitlab_pages_domain = os.environ.get('GITLAB_PAGES_DOMAIN')
	is_gitlab_pages = domain == gitlab_pages_domain
	has_no_subdomains = "." not in domain.replace(f".{gitlab_pages_domain}", "")
	ends_with_gitlab_pages = domain.endswith(f".{gitlab_pages_domain}")

	if is_gitlab_pages or (ends_with_gitlab_pages and has_no_subdomains):
		return "", 200

	# Get all the domains from the gitlab API
	try:
		domains = get_gitlab_pages_domains()
	except Exception as e:
		return f"Error: {e}", 500
	
	# Check if the domain is in the list of domains
	if domain in domains:
		return "", 200

	return "", 404


def get_gitlab_pages_domains():
	gitlab_token = os.environ.get('GITLAB_TOKEN')
	gitlab_domain = os.environ.get('GITLAB_DOMAIN')
    
	if gitlab_token is None:
		raise Exception("GITLAB_TOKEN is not set")

	if gitlab_domain is None:
		raise Exception("GITLAB_DOMAIN is not set")

	try:
		response = requests.get(
			f"https://{gitlab_domain}/api/v4/pages/domains",
			headers={'PRIVATE-TOKEN': gitlab_token}
		)
	except Exception as e:
		raise Exception(f"GitLab request failed: {e}")

	if response.status_code == 200:
		return [x['domain'] for x in response.json()]
	
	raise Exception(f"GitLab returned status code {response.status_code}")

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=5000)
