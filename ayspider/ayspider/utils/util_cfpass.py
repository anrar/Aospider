import logging
import random
import re
import execjs
from requests.sessions import Session
from copy import deepcopy
from time import sleep
from .util_config import *

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse


DEFAULT_USER_AGENT = random.choice(CONFIG_USERAGENT_PC)

BUG_REPORT = ("Cloudflare may have changed their technique, or there may be a bug in the script.\n\nPlease read " "https://github.com/Anorov/cloudflare-scrape#updates, then file a "
"bug report at https://github.com/Anorov/cloudflare-scrape/issues.")

def gethtml(session:Session, url, *args, **kwargs):
    resp = request(session, 'get' ,url, *args, **kwargs)
    return str(resp.content, encoding='utf-8')

def request(session:Session, method, url, *args, **kwargs):
    resp = session.request(method, url, *args, **kwargs)

    # Check if Cloudflare anti-bot is on
    if ( resp.status_code == 503
         and resp.headers.get("Server") == "cloudflare-nginx"
         and b"jschl_vc" in resp.content
         and b"jschl_answer" in resp.content
    ):
        return solve_cf_challenge(session,resp, **kwargs)

    # Otherwise, no Cloudflare anti-bot detected
    return resp

def solve_cf_challenge(session:Session, resp, **original_kwargs):
    sleep(5)  # Cloudflare requires a delay before solving the challenge

    body = resp.text
    parsed_url = urlparse(resp.url)
    domain = urlparse(resp.url).netloc
    submit_url = "%s://%s/cdn-cgi/l/chk_jschl" % (parsed_url.scheme, domain)

    cloudflare_kwargs = deepcopy(original_kwargs)
    params = cloudflare_kwargs.setdefault("params", {})
    headers = cloudflare_kwargs.setdefault("headers", {})
    headers["Referer"] = resp.url

    try:
        params["jschl_vc"] = re.search(r'name="jschl_vc" value="(\w+)"', body).group(1)
        params["pass"] = re.search(r'name="pass" value="(.+?)"', body).group(1)

    except Exception as e:
        # Something is wrong with the page.
        # This may indicate Cloudflare has changed their anti-bot
        # technique. If you see this and are running the latest version,
        # please open a GitHub issue so I can update the code accordingly.
        raise ValueError("Unable to parse Cloudflare anti-bots page: %s %s" % (e.message, BUG_REPORT))

    # Solve the Javascript challenge
    params["jschl_answer"] = str(solve_challenge(session,body) + len(domain))

    # Requests transforms any request into a GET after a redirect,
    # so the redirect has to be handled manually here to allow for
    # performing other types of requests even as the first request.
    method = resp.request.method
    cloudflare_kwargs["allow_redirects"] = False
    redirect = session.request(method, submit_url, **cloudflare_kwargs)
    return session.request(method, redirect.headers["Location"], **original_kwargs)

def solve_challenge(session:Session, body):
    try:
        js = re.search(r"setTimeout\(function\(\){\s+(var "
                    "s,t,o,p,b,r,e,a,k,i,n,g,f.+?\r?\n[\s\S]+?a\.value =.+?)\r?\n", body).group(1)
    except Exception:
        raise ValueError("Unable to identify Cloudflare IUAM Javascript on website. %s" % BUG_REPORT)

    js = re.sub(r"a\.value = (parseInt\(.+?\)).+", r"\1", js)
    js = re.sub(r"\s{3,}[a-z](?: = |\.).+", "", js)

    # Strip characters that could be used to exit the string context
    # These characters are not currently used in Cloudflare's arithmetic snippet
    js = re.sub(r"[\n\\']", "", js)

    if "parseInt" not in js:
        raise ValueError("Error parsing Cloudflare IUAM Javascript challenge. %s" % BUG_REPORT)

    # Use vm.runInNewContext to safely evaluate code
    # The sandboxed code cannot use the Node.js standard library
    js = "return require('vm').runInNewContext('%s');" % js

    try:
        node = execjs.get("Node")
    except Exception:
        raise EnvironmentError("Missing Node.js runtime. Node is required. Please read the cfscrape"
            " README's Dependencies section: https://github.com/Anorov/cloudflare-scrape#dependencies.")

    try:
        result = node.exec_(js)
    except Exception:
        logging.error("Error executing Cloudflare IUAM Javascript. %s" % BUG_REPORT)
        raise

    try:
        result = int(result)
    except Exception:
        raise ValueError("Cloudflare IUAM challenge returned unexpected value. %s" % BUG_REPORT)

    return result

def create_scraper(session:Session = None, sess=None, **kwargs):
    """
    Convenience function for creating a ready-to-go requests.Session (subclass) object.
    """
    session = Session()
    if "requests" in session.headers["User-Agent"]:
            # Spoof Firefox on Linux if no custom User-Agent has been set
            session.headers["User-Agent"] = DEFAULT_USER_AGENT

    if sess:
        attrs = ["auth", "cert", "cookies", "headers", "hooks", "params", "proxies", "data"]
        for attr in attrs:
            val = getattr(sess, attr, None)
            if val:
                setattr(session, attr, val)

    return session

def get_tokens(session:Session, url, user_agent=None, **kwargs):
    scraper = create_scraper(session)
    if user_agent:
        scraper.headers["User-Agent"] = user_agent

    try:
        resp = scraper.get(url, **kwargs)
        resp.raise_for_status()
    except Exception as e:
        logging.error("'%s' returned an error. Could not collect tokens." % url)
        raise

    domain = urlparse(resp.url).netloc
    cookie_domain = None

    for d in scraper.cookies.list_domains():
        if d.startswith(".") and d in ("." + domain):
            cookie_domain = d
            break
    else:
        raise ValueError("Unable to find Cloudflare cookies. Does the site actually have Cloudflare IUAM (\"I'm Under Attack Mode\") enabled?")

    return ({
                "__cfduid": scraper.cookies.get("__cfduid", "", domain=cookie_domain),
                "cf_clearance": scraper.cookies.get("cf_clearance", "", domain=cookie_domain)
            },
            scraper.headers["User-Agent"]
           )

def get_cookie_string(session:Session, url, user_agent=None, **kwargs):
    """
    Convenience function for building a Cookie HTTP header value.
    """
    tokens, user_agent = get_tokens(session, url, user_agent=user_agent, **kwargs)
    return "; ".join("=".join(pair) for pair in tokens.items()), user_agent

