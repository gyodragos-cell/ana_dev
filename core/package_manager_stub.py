"""AI OS package manager stub."""

from __future__ import annotations


class PackageManagerStub:
    """Install/uninstall package metadata without real downloads."""

    def __init__(self) -> None:
        """Initialize package registry."""
        self.packages: dict[str, str] = {}

    def install(self, name: str, version: str) -> dict[str, str | bool]:
        """Install package metadata."""
        self.packages[name] = version
        return {"success": True, "name": name, "version": version}

    def uninstall(self, name: str) -> dict[str, str | bool]:
        """Uninstall package metadata."""
        existed = self.packages.pop(name, None) is not None
        return {"success": existed, "name": name}


__all__ = ["PackageManagerStub"]
