# Argentina core-CPI source-custody disposition — 2026-10-09

The local new-ID core-CPI follow-up was committed before its value run and
replayed exactly. It is **excluded from the consolidated public hypothesis
ledger** because the full pinned 39-entry fetch manifest contained two
unrelated absolute macOS home paths in other publishers' raw-file metadata.
The public OPSEC check rejected the tracked manifest. Those paths are not
repeated here.

The preregistration at `ec22102a8e3bca7bb783ebcf1097b8457b7be7b3` pinned the manifest's full SHA-256 and
required its exact first-addition bytes before candidate index access. The run
at `580340397c2aa8df9612d488d6e6061501dd5322` depended on that gate. Editing the manifest after the run would
break the registered source contract and stored replay packets. The review
branch therefore reversed the run and preregistration at `d477a22cb99502b9018d003b1e45247f2db30ba9` and
`5fcfdf106d73f1c31c359fb580b34fa826d34cfd`, respectively, and regenerated the ledger without this ID. The
current audited count is 440 public of 1,974 hypotheses, including 389
calibration and 51 featured records. The Argentina result receives no public,
causal, or school-score credit.

The original commits and manifest remain in **local Git history** for forensic
review even though the current tree passes `check_public_opsec.py`. This review
branch must not be pushed or published before separate history cleanup and an
independent custody review. A future sanitized re-registration made after
outcome access must be disclosed as such; it cannot automatically inherit
prospective status from the rejected packet.
