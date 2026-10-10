
## R13-R — row 16 bounded path-swap stress (WAIVED-SIM, low power)

Windows NTFS, 150 `verify_backup` calls while a thread continuously rename-swapped the
snapshot directory between a good and a byte-flipped copy (plus a junction-swap variant,
rejected up front as `UNSAFE_PATH`). Result: 0 crashes, 0 accepted tampered snapshots,
all 150 fail-closed; control (tampered copy alone) rejected. **Limits:** swap rate and
mixed-read windows were not measured, no success path was observed during the race, so
this shows no defect found, not TOCTOU safety. Row 16 stays `NOT_RUN` for acceptance;
unsupported: hostile parent-directory ABA, atomic directory-swap protection (as stated in R13-K/L).
Rows 15 (power loss) and 11 (external fencing) cannot be simulated here and stay `NOT_RUN`.
