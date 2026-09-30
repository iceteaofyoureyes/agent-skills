# Kit packaging contract

tooling/lib/ba_kit.py is the shared standard-library installer. The ba manifest keeps its original fields and root-skill lookup. Optional manifest fields generalize packaging for kits that bundle runtime files:

- skill_sources maps declared skill ids to repository-relative source directories; ids without an entry still resolve from the repository root.
- files contains explicit source/destination entries for regular runtime files. No wildcard copy rules are supported. Paths are relative POSIX paths and cannot escape source or target roots.
- capabilities, dependencies, and prerequisites hold kit-owned operator and provenance metadata.
- agents lists supported native install targets. generic remains available with an explicit --target.
- install_metadata asks the generic installer to record source repository/revision, manifest schema version, pinned dependencies, and declared capabilities in the kit install record.
- integrity optionally pins a durable authority artifact and a separately versioned payload digest.

For an integrity-enabled kit, `.{kit_id}-kit/kit.yaml` is the one canonical installed package definition. Test Kit uses `.test-kit/kit.yaml`; Doctor reads that installed copy and does not search for manifests. The manifest pins the authority file SHA-256 and payload digest. The durable authority artifact is generated from the resolved source allowlist, stored as an explicit package file, and checked against both manifest pins before install/package validation.

For Test Kit, the checked-in authority source is `kits/test/package-authority.json`; the manifest installs it at `.test-kit/package-authority.json`. Regenerate its inventory from source payloads and update both manifest pins together when package inputs change.

The authority contains kit and manifest identity plus the exact payload path/hash/classification entries, count, payload algorithm, and payload digest. The install record is the install journal: it stores ownership, capabilities, local conflicts, and duplicated identities for operational checks. Doctor validates the authority against manifest pins, compares the record's exact inventory to the authority, then checks installed bytes against authority hashes. The authority and root definition are explicitly owned through the install record's `files` section; neither is in its own payload inventory.

Reinstall updates managed content only when its actual hash still matches the prior expected hash. A local edit is preserved and returned as a managed-file conflict; the authority keeps the package hash, so doctor continues to report drift. Unrelated files are not recorded or removed.

Ownership is positive and exact. A valid legacy BA record without `files` means that record owns no manifest files; it still owns only the skills named in its `skills` map. Missing ownership sections never imply ownership of arbitrary paths. Invalid records fail safe by preserving potentially shared content. Schema version 1 remains backward compatible; `files` and `managed_files` are optional for legacy records and validated when present.

## Test Kit V1 inclusion

kits/test/kit.yaml is the complete allowlist. The installed tree includes the Test Kit workflow skill, exact pinned TEA and Katalon skills, core Python runtime and handoff contract helper, pin data, optional projection code and locks, operator documentation, license notices, and the install provenance record.

The package does not copy benchmark/, tooling/tests/, caches, node_modules/, generated projections, or machine-specific skill trees. Optional projection dependencies are bootstrapped by explicit operator commands after installation.

## Inventory and digest

Run the inventory helper against an installed target:

    python -m tooling.lib.package --kit test --target <skills-directory> --output .work/packaging/test-kit-v1-inventory.csv

`TEST_KIT_PACKAGE_PAYLOAD_V1` hashes only resolved skill files and explicit runtime files. It excludes `.test-kit/kit.yaml`, `package-authority.json`, and the generated install record. This versioned domain avoids circular hashes. The manifest's `authority.sha256` pins the exact authority bytes; `payload.sha256` independently pins the payload inventory digest. The helper also reports `INSTALLED_TREE_SHA256` using `INSTALLED_TREE_SHA256_V1`, which includes every regular file in the installed target, including the root definition, authority, and install record. These are three distinct digest domains. Symlinks and non-regular files are rejected.

For each file, normalize its relative path to Unicode NFC and POSIX slash separators, encode that path as UTF-8, compute lowercase SHA-256 over raw file bytes, and emit:

    normalized-path-utf8 NUL lowercase-file-sha256 LF

Sort records bytewise by normalized-path UTF-8 bytes. Each tree digest is lowercase SHA-256 of the concatenated records. Digests exclude directory entries, file timestamps, permissions, owners, and ACL metadata. Case-insensitive normalized path collisions are rejected so the tree remains portable to Windows.

The installed manifest and authority are ordinary files in the candidate inventory, classified as `PACKAGE_MANIFEST` and `PACKAGE_AUTHORITY`; the install record is `INSTALLED_PROVENANCE`. They are excluded only from the payload digest, not from the installed-tree digest. Candidate inventories classify each row and name its source. An `UNDECLARED_FILE` makes the inventory command fail.

The package manifest is the V1 local package-definition root of trust. Doctor detects corruption and drift relative to that definition. Cryptographic authenticity of the package definition itself is outside V1 scope. Doctor reports `PACKAGE_DEFINITION_INVALID`, `PACKAGE_AUTHORITY_INVALID`, `PACKAGE_METADATA_INVALID`, `MISSING_MANAGED_FILE`, `MODIFIED_MANAGED_FILE`, or `DEPENDENCY_MISSING`. Reinstall preserves edited files and keeps their authoritative expected hash; it does not make the installation healthy by adopting the local edit. Missing optional projection dependencies are reported without blocking the core workflow. Missing Codex CLI blocks native invocation readiness.

## Installed smoke

tooling/tests/run_installed_package_smoke.ps1 installs into an OS-temp Codex skills folder, bootstraps optional dependencies explicitly from the installed locks, and runs the self-contained fixture with a temporary Codex JavaScript stub. Pass a portable Node directory with -NodeHome; the smoke rejects C:\nvm4w and cleans its OS-temp destination after completion.
