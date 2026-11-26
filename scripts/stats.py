"""Write distribution.json: the Distribution numbers on the homepage, as GitHub, the Terraform Registry and PyPI report them.

Run once a day by .github/workflows/stats.yml (or by hand: python3 scripts/stats.py). Standard library only.
GITHUB_TOKEN, when set, raises GitHub's rate limit; every call reads public data only.
"""
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xmlrpc.client

USER = "cloudformer"
MODULE = "cloudformer/infra/aws"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "distribution.json")


def get(url, token=None, _retry=True):
    """(JSON body, Link header) of a GET. One retry on transient trouble (5xx, 429, dropped
    connection); a definitive answer like 404 is returned to the caller to interpret."""
    headers = {"User-Agent": "cloudformer-stats", "Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
            return json.loads(r.read()), r.headers.get("Link", "")
    except urllib.error.HTTPError as e:
        if _retry and (e.code >= 500 or e.code == 429):
            time.sleep(5)
            return get(url, token, _retry=False)
        raise
    except urllib.error.URLError:
        if _retry:
            time.sleep(5)
            return get(url, token, _retry=False)
        raise


def github_count(url, token):
    """How many items a GitHub list has: ask for one per page, read the last page number from the Link header."""
    sep = "&" if "?" in url else "?"
    body, link = get(f"{url}{sep}per_page=1", token)
    last = re.search(r'[?&]page=(\d+)>; rel="last"', link)
    return int(last.group(1)) if last else len(body)


def github(token):
    user, _ = get(f"https://api.github.com/users/{USER}", token)
    repos, page = [], 1
    while True:
        batch, _ = get(f"https://api.github.com/users/{USER}/repos?type=owner&per_page=100&page={page}", token)
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    own = [r for r in repos if not r["fork"] and not r["private"]]
    since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    commits_30d = tags = 0
    for r in own:
        if r["size"] == 0:     # an empty repository has no commits (the API answers 409)
            continue
        commits_30d += github_count(f"https://api.github.com/repos/{USER}/{r['name']}/commits?since={since}", token)
        tags += github_count(f"https://api.github.com/repos/{USER}/{r['name']}/tags", token)
    return {"public_repos": user["public_repos"], "commits_30d": commits_30d, "tags": tags}


def registry():
    module, _ = get(f"https://registry.terraform.io/v1/modules/{MODULE}")
    versions, _ = get(f"https://registry.terraform.io/v1/modules/{MODULE}/versions")
    return {"modules": len(module.get("submodules") or []), "versions": len(versions["modules"][0]["versions"]),
            "downloads": module["downloads"]}


def downloads_30d(name):
    """pypistats has no entry until a package's first downloads are counted: its 404 means 0, honestly."""
    try:
        recent, _ = get(f"https://pypistats.org/api/packages/{name}/recent")
        return recent["data"]["last_month"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return 0
        raise


def pypi():
    try:
        raw = xmlrpc.client.ServerProxy("https://pypi.org/pypi").user_packages(USER)
    except Exception:  # transient XMLRPC hiccup: one retry, then fail honestly
        time.sleep(5)
        raw = xmlrpc.client.ServerProxy("https://pypi.org/pypi").user_packages(USER)
    packages = sorted({name for _role, name in raw})
    releases = downloads = 0
    for name in packages:
        meta, _ = get(f"https://pypi.org/pypi/{name}/json")
        releases += len(meta["releases"])
        downloads += downloads_30d(name)
    return {"packages": len(packages), "releases": releases, "downloads_30d": downloads}


def mcp():
    """The official MCP Registry: servers under io.github.<USER> and the latest version. The tool
    count has no registry API — the authoritative list is the registered decorators in the public
    source, so count those."""
    data, _ = get(f"https://registry.modelcontextprotocol.io/v0/servers?search=io.github.{USER}")
    mine = [x["server"] for x in data.get("servers", []) if x["server"]["name"].startswith(f"io.github.{USER}/")]
    req = urllib.request.Request(f"https://raw.githubusercontent.com/{USER}/idlefree-mcp/main/idlefree_mcp/server.py",
                                 headers={"User-Agent": "cloudformer-stats"})
    with urllib.request.urlopen(req, timeout=30) as r:
        tools = r.read().decode().count("@server.tool()")
    return {"servers": len(mine), "latest": mine[0]["version"] if mine else "", "tools": tools}


def main():
    """Display data, refreshed daily: a source that fails today keeps yesterday's numbers and is
    retried tomorrow — the run never dies over one source (first ever run excepted: nothing to
    fall back to, so it fails loudly)."""
    try:
        with open(OUT, encoding="utf-8") as f:
            prev = json.load(f)
    except (OSError, ValueError):
        prev = {}
    sections = (("github", lambda: github(os.environ.get("GITHUB_TOKEN"))),
                ("registry", registry), ("pypi", pypi), ("mcp", mcp))
    today = datetime.date.today()
    stats, stale = {"date": today.isoformat()}, {}
    for key, fetch in sections:
        try:
            stats[key] = fetch()
        except Exception as e:  # noqa: BLE001 — any failure: keep yesterday's section
            if key not in prev:
                raise
            stale[key] = prev.get("stale", {}).get(key, today.isoformat())
            print(f"{key}: {type(e).__name__}: {e} — keeping the numbers of {stale[key]}")
            stats[key] = prev[key]
    # hand-maintained numbers live in the json too (the page reads one file for everything):
    # the script never computes them, it carries them forward; edit them in distribution.json.
    stats["plugin"] = prev.get("plugin", {"plugins": 1, "skills": 2, "mcp_servers": 1})
    if stale:
        stats["stale"] = stale
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
        f.write("\n")
    print(json.dumps(stats))
    overdue = {k: v for k, v in stale.items() if (today - datetime.date.fromisoformat(v)).days > 3}
    if overdue:
        print(f"STALE ALARM: falling back for over 3 days — the source likely changed: {overdue}")
        sys.exit(1)


if __name__ == "__main__":
    main()
