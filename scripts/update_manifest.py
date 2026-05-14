"""Update the manifest file."""
import json
import os
import sys


def update_manifest():
    """Update the manifest file."""
    version = "0.0.0"
    for index, value in enumerate(sys.argv):
        if value in ["--version", "-V"]:
            version = sys.argv[index + 1]

    # pylint: disable=unspecified-encoding
    with open(
        f"{os.getcwd()}/custom_components/ev_smart_charging/manifest.json"
    ) as manifestfile:
        manifest = json.load(manifestfile)

    manifest["version"] = version

    ordered_manifest = {}
    if "domain" in manifest:
        ordered_manifest["domain"] = manifest["domain"]
    if "name" in manifest:
        ordered_manifest["name"] = manifest["name"]

    for key in sorted(key for key in manifest if key not in {"domain", "name"}):
        ordered_manifest[key] = manifest[key]

    with open(
        f"{os.getcwd()}/custom_components/ev_smart_charging/manifest.json", "w"
    ) as manifestfile:
        manifestfile.write(json.dumps(ordered_manifest, indent=2))
        manifestfile.write("\n")


update_manifest()
