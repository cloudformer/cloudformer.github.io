"""Write distribution.json: the Distribution numbers on the homepage, as GitHub, the Terraform Registry and PyPI report them.

Run once a day by .github/workflows/stats.yml (or by hand: python3 scripts/stats.py). Standard library only.
GITHUB_TOKEN, when set, raises GitHub's rate limit; every call reads public data only.
"""
import datetime
import json
import os
import re
import urllib.request
import xmlrpc.client

USER = "cloudformer"
MODULE = "cloudformer/infra/aws"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "distribution.json")


def get(url, token=None):
    """(JSON body, Link header) of a GET."""
    headers = {"User-Agent": "cloudformer-stats", "Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return json.loads(r.read()), r.headers.get("Link", "")


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


def pypi():
    packages = sorted({name for _role, name in xmlrpc.client.ServerProxy("https://pypi.org/pypi").user_packages(USER)})
    releases = downloads_30d = 0
    for name in packages:
        meta, _ = get(f"https://pypi.org/pypi/{name}/json")
        releases += len(meta["releases"])
        recent, _ = get(f"https://pypistats.org/api/packages/{name}/recent")
        downloads_30d += recent["data"]["last_month"]
    return {"packages": len(packages), "releases": releases, "downloads_30d": downloads_30d}


def mcp():
    """The official MCP Registry: how many servers under io.github.<USER>, and the latest version."""
    data, _ = get(f"https://registry.modelcontextprotocol.io/v0/servers?search=io.github.{USER}")
    mine = [x["server"] for x in data.get("servers", []) if x["server"]["name"].startswith(f"io.github.{USER}/")]
    return {"servers": len(mine), "latest": mine[0]["version"] if mine else ""}


def main():
    stats = {"date": datetime.date.today().isoformat(), "github": github(os.environ.get("GITHUB_TOKEN")),
             "registry": registry(), "pypi": pypi(), "mcp": mcp()}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
        f.write("\n")
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
