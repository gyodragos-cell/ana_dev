"""Package the ANA Antigravity cockpit VSIX without installing it.

This is intentionally stdlib-only. It prepares a local VSIX from
vscode_extension/ so the operator can install/reload later, when chat continuity
is not at risk.
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
SOURCE_DIR = REPO_ROOT / "vscode_extension"
ARTIFACTS_DIR = ANA_ROOT / "dev_artifacts"
TEMPLATE_DIR = ARTIFACTS_DIR / "vsix_template"
CONTENT_TYPES = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension=".js" ContentType="application/javascript"/><Default Extension=".json" ContentType="application/json"/><Default Extension=".md" ContentType="text/markdown"/><Default Extension=".png" ContentType="image/png"/><Default Extension=".vsixmanifest" ContentType="text/xml"/></Types>
"""


def read_package() -> dict:
    package_path = SOURCE_DIR / "package.json"
    return json.loads(package_path.read_text(encoding="utf-8"))


def build_manifest(package: dict) -> str:
    template = TEMPLATE_DIR / "extension.vsixmanifest"
    if template.exists():
        text = template.read_text(encoding="utf-8")
        old_version = _extract_identity_version(text)
        if old_version:
            text = text.replace(f'Version="{old_version}"', f'Version="{package["version"]}"')
        text = text.replace(
            '<Identity Language="en-US" Id="ana-antigravity-chat"',
            f'<Identity Language="en-US" Id="{package["name"]}"',
        )
        text = text.replace('Publisher="ana-ai"', f'Publisher="{package["publisher"]}"')
        text = _replace_xml_element(text, "DisplayName", html.escape(str(package.get("displayName", package["name"]))))
        text = _replace_xml_element(
            text,
            "Description",
            html.escape(str(package.get("description", ""))),
            attrs=' xml:space="preserve"',
        )
        keywords = package.get("keywords") or []
        if keywords:
            text = _replace_xml_element(text, "Tags", html.escape(",".join(str(item) for item in keywords)))
        categories = package.get("categories") or []
        if categories:
            text = _replace_xml_element(text, "Categories", html.escape(",".join(str(item) for item in categories)))
        icon_path = package.get("icon")
        if icon_path:
            text = _ensure_manifest_icon_asset(text, f"extension/{icon_path}")
        text = _ensure_manifest_asset(
            text,
            "Microsoft.VisualStudio.Services.Content.Changelog",
            "extension/CHANGELOG.md",
        )
        text = _ensure_manifest_asset(
            text,
            "Microsoft.VisualStudio.Services.Content.License",
            "extension/LICENSE.md",
        )
        return text

    return f"""<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
  <Metadata>
    <Identity Language="en-US" Id="{package["name"]}" Version="{package["version"]}" Publisher="{package["publisher"]}" />
    <DisplayName>{package["displayName"]}</DisplayName>
    <Description xml:space="preserve">{package["description"]}</Description>
    <GalleryFlags>Public</GalleryFlags>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{package.get("engines", {}).get("vscode", "^1.90.0")}" />
      <Property Id="Microsoft.VisualStudio.Code.ExecutesCode" Value="true" />
      <Property Id="Microsoft.VisualStudio.Services.GitHubFlavoredMarkdown" Value="true" />
      <Property Id="Microsoft.VisualStudio.Services.Content.Pricing" Value="Free"/>
    </Properties>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code"/>
  </Installation>
  <Dependencies/>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/readme.md" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Services.Content.Changelog" Path="extension/CHANGELOG.md" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Services.Content.License" Path="extension/LICENSE.md" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Services.Icons.Default" Path="extension/{package.get("icon", "assets/ana-max-icon.png")}" Addressable="true" />
  </Assets>
</PackageManifest>
"""


def _extract_identity_version(manifest: str) -> str:
    marker = ' Version="'
    identity_pos = manifest.find("<Identity")
    if identity_pos < 0:
        return ""
    version_pos = manifest.find(marker, identity_pos)
    if version_pos < 0:
        return ""
    start = version_pos + len(marker)
    end = manifest.find('"', start)
    return manifest[start:end] if end > start else ""


def _replace_xml_element(text: str, tag: str, value: str, attrs: str = "") -> str:
    start_marker = f"<{tag}"
    start = text.find(start_marker)
    if start < 0:
        return text
    open_end = text.find(">", start)
    close_marker = f"</{tag}>"
    close = text.find(close_marker, open_end)
    if open_end < 0 or close < 0:
        return text
    return text[:start] + f"<{tag}{attrs}>{value}{close_marker}" + text[close + len(close_marker):]


def _ensure_manifest_icon_asset(text: str, icon_path: str) -> str:
    return _ensure_manifest_asset(text, "Microsoft.VisualStudio.Services.Icons.Default", icon_path)


def _ensure_manifest_asset(text: str, asset_type: str, asset_path: str) -> str:
    if asset_type in text:
        return text
    marker = "</Assets>"
    asset = f'    <Asset Type="{html.escape(asset_type)}" Path="{html.escape(asset_path)}" Addressable="true" />\n'
    pos = text.find(marker)
    if pos < 0:
        return text
    return text[:pos] + asset + text[pos:]


def run_node_check(path: Path) -> None:
    node = shutil.which("node")
    if not node:
        print("[WARN] node not found; skipping JS syntax check.")
        return
    result = subprocess.run([node, "--check", str(path)], capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "node --check failed")


def copy_source(build_dir: Path, package: dict) -> None:
    extension_dir = build_dir / "extension"
    extension_dir.mkdir(parents=True, exist_ok=True)
    for name in ["extension.js", "package.json", "README.md"]:
        src = SOURCE_DIR / name
        if not src.exists():
            raise FileNotFoundError(src)
    shutil.copy2(SOURCE_DIR / "extension.js", extension_dir / "extension.js")
    shutil.copy2(SOURCE_DIR / "package.json", extension_dir / "package.json")
    shutil.copy2(SOURCE_DIR / "README.md", extension_dir / "readme.md")
    for optional_name in ["CHANGELOG.md", "LICENSE.md"]:
        optional_src = SOURCE_DIR / optional_name
        if optional_src.exists():
            shutil.copy2(optional_src, extension_dir / optional_name)
    assets_dir = SOURCE_DIR / "assets"
    if assets_dir.exists():
        shutil.copytree(assets_dir, extension_dir / "assets", dirs_exist_ok=True)
    (build_dir / "extension.vsixmanifest").write_text(build_manifest(package), encoding="utf-8")
    content_source = TEMPLATE_DIR / "[Content_Types].xml"
    if content_source.exists():
        shutil.copy2(content_source, build_dir / "[Content_Types].xml")
    else:
        (build_dir / "[Content_Types].xml").write_text(CONTENT_TYPES, encoding="utf-8")


def create_vsix(build_dir: Path, output_path: Path) -> None:
    if output_path.exists():
        output_path.unlink()
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(build_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(build_dir).as_posix())


def verify_vsix(path: Path, package: dict) -> None:
    required = {
        "extension/extension.js",
        "extension/package.json",
        "extension/readme.md",
        "extension/CHANGELOG.md",
        "extension/LICENSE.md",
        "extension.vsixmanifest",
        "[Content_Types].xml",
    }
    icon_path = package.get("icon")
    if icon_path:
        required.add(f"extension/{icon_path}")
    with zipfile.ZipFile(path, "r") as archive:
        names = set(archive.namelist())
        missing = sorted(required - names)
        if missing:
            raise RuntimeError(f"VSIX missing files: {missing}")
        packaged = json.loads(archive.read("extension/package.json").decode("utf-8"))
    if packaged.get("version") != package.get("version"):
        raise RuntimeError(f"Packaged version mismatch: {packaged.get('version')} != {package.get('version')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Package ANA cockpit VSIX without installing it.")
    parser.add_argument("--version", help="Override package.json version for this packaging run.")
    args = parser.parse_args()

    package = read_package()
    if args.version:
        package["version"] = args.version
        package_path = SOURCE_DIR / "package.json"
        package_text = json.loads(package_path.read_text(encoding="utf-8"))
        package_text["version"] = args.version
        package_path.write_text(json.dumps(package_text, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    version = package["version"]
    build_dir = ARTIFACTS_DIR / f"vsix_build_{version}"
    verify_dir = ARTIFACTS_DIR / f"vsix_verify_{version}"
    output_main = ANA_ROOT / f"ana-antigravity-hybrid-{version}.vsix"
    output_copy = SOURCE_DIR / f"ana-antigravity-{version}.vsix"

    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    copy_source(build_dir, package)
    run_node_check(build_dir / "extension" / "extension.js")
    create_vsix(build_dir, output_main)
    verify_vsix(output_main, package)
    shutil.copy2(output_main, output_copy)

    if verify_dir.exists():
        shutil.rmtree(verify_dir)
    verify_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_main, "r") as archive:
        archive.extractall(verify_dir)
    run_node_check(verify_dir / "extension" / "extension.js")
    verify_vsix(output_main, package)

    print(json.dumps({
        "version": version,
        "main_vsix": str(output_main),
        "copy_vsix": str(output_copy),
        "build_dir": str(build_dir),
        "verify_dir": str(verify_dir),
    }, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
