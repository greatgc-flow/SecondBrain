# SecondBrain

SecondBrain preserves personal files on one local computer without changing their sources.
The owner captures, finds, opens, and verifies originals with recorded acquisition context.
One user-managed backup folder supports a verified restore into an empty local root.

See [docs/design.md](docs/design.md) and [docs/decisions.md](docs/decisions.md) for architecture and design records.

## Quickstart

SecondBrain provides six exact commands via `sb` (or `python -m secondbrain`):

```bash
# 1. Capture: Preserve a file or folder into content-addressed objects and versioned receipts
sb capture "C:\Inbox\contract.txt"
sb capture "C:\Inbox"

# 2. Verify: Integrity check over all receipts and content objects
sb verify

# 3. Find: Search filenames, acquisition context, and extracted text (Korean & English)
sb find "contract"
sb find "기획서"

# 4. Open: Verify integrity and open a protected read-only working copy
sb open cap-20261012t000000z-ba7816bf
sb open cap-20261012t000000z-ba7816bf --print-path

# 5. Backup: Append-only mirror to a user-managed backup root (e.g. Google Drive / OneDrive)
sb backup --backup-root "D:\GoogleDrive\SecondBrainBackup"

# 6. Restore: Restore repository from backup root into an empty local directory
sb restore "D:\GoogleDrive\SecondBrainBackup" --to "D:\Recovered"
```

All commands support `--root <PATH>` to specify a custom repository data root (default: `D:\SecondBrain`) and `--json` for structured JSON output. Exit codes: `0` = OK, `1` = integrity failure (missing, corrupt, orphan), `2` = usage/IO error (locked files, invalid arguments).

## Legacy

The R7-R13 line (`brain`, `profiles/`) is frozen reference material at tag `legacy-r13-final`; it does not define v0.1 behaviour. See `docs/README.md`.
