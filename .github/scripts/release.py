"""Publish only validated, immutable binary tags; no private-repository access."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request
import zipfile


def gh(*args, check=True):
    return subprocess.run(["gh", *args], text=True, capture_output=True, check=check)


tag = os.environ["RELEASE_TAG"]
match = re.fullmatch(r"v(\d+\.\d+\.\d+)-build\.(\d+)\.(\d+)", tag)
if not match:
    raise ValueError("Not a valid immutable build tag")
version, build, attempt = match[1], int(match[2]), int(match[3])
metadata = json.loads(Path("artifacts/release.json").read_text())
artifact = Path("artifacts/CreateVC-Core.jar")
with artifact.open("rb") as binary:
    digest = hashlib.file_digest(binary, "sha256").hexdigest()
if metadata != {"version": version, "tag": tag, "sha256": digest, "build": build, "attempt": attempt}:
    raise ValueError("Release tag, metadata and artifact do not match")
if Path("artifacts/CreateVC-Core.jar.sha256").read_text().strip() != f"{digest}  CreateVC-Core.jar":
    raise ValueError("Checksum file does not match")
with zipfile.ZipFile(artifact) as jar:
    bad_entry = jar.testzip()
    if bad_entry or "META-INF/neoforge.mods.toml" not in jar.namelist():
        raise ValueError("Invalid mod JAR")
    mod_info = jar.read("META-INF/neoforge.mods.toml").decode()
    if f'version="{version}"' not in mod_info:
        raise ValueError("Mod version does not match the release")

repo = os.environ["GH_REPO"]
latest = gh("api", f"repos/{repo}/releases/latest", check=False)
make_latest = True
if latest.returncode == 0:
    previous = re.fullmatch(r"v\d+\.\d+\.\d+-build\.(\d+)\.(\d+)", json.loads(latest.stdout)["tag_name"])
    if previous:
        make_latest = (build, attempt) >= (int(previous[1]), int(previous[2]))
elif "404" not in latest.stderr:
    raise RuntimeError(latest.stderr)

existing = gh("release", "view", tag, "--json", "isDraft,assets", check=False)
if existing.returncode != 0:
    if "release not found" not in existing.stderr.lower():
        raise RuntimeError(existing.stderr)
    # Draft until all assets are uploaded; Packwiz cannot discover an incomplete release.
    gh("release", "create", tag, "--verify-tag", "--target", "main", "--draft",
       "--title", f"CreateVC Core {version} — build {build}.{attempt}",
       "--notes", "CreateVC Core for NeoForge 1.21.1. Binary-only build; source remains private.\n\n"
       "Install with `packwiz github add Jammersmurph/CreateVC-Core-Releases --regex "
       "'^CreateVC-Core\\.jar$'`. Update the pack with `packwiz update --all`.\n\n"
       f"SHA-256: `{digest}`")
    existing_data = {"isDraft": True, "assets": []}
else:
    existing_data = json.loads(existing.stdout)

if existing_data["isDraft"]:
    gh("release", "upload", tag, str(artifact), "artifacts/CreateVC-Core.jar.sha256",
       "artifacts/release.json", "--clobber")
    gh("release", "edit", tag, "--draft=false", f"--latest={'true' if make_latest else 'false'}")
elif make_latest:
    # A retry never replaces published assets.
    gh("release", "edit", tag, "--latest=true")

# Verify the public asset itself, not a private API-only download.
release = json.loads(gh("release", "view", tag, "--json", "assets,url").stdout)
asset = next(asset for asset in release["assets"] if asset["name"] == "CreateVC-Core.jar")
with urllib.request.urlopen(asset["url"], timeout=60) as response:
    actual = hashlib.sha256(response.read()).hexdigest()
if actual != digest:
    raise ValueError("Public release asset does not match the build")
summary = f"Published {release['url']}\nSHA-256: {digest}\nLatest: {make_latest}\n"
print(summary)
if "GITHUB_STEP_SUMMARY" in os.environ:
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as output:
        output.write(summary)
