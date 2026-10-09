# R7 product scope and release gate

**Implemented:** Local Capture-only landing and read-only Evidence Object byte integrity verification.

**Tested locally:** 40 synthetic tests passed on the original R7 source checkout. GitHub CI results are independent and must be checked after the remote push.

**Capture flow:** safely open regular file → copy + fsync → hash and source stability checks → v2 receipt → fsync → .ready last → read-only validation.

**Not implemented:** single-writer Vault publish, Custody RFC 8785 JCS hash chain, Observation/Acquisition transaction, Legal Hold, cloud and backup restore.

**Not verified:** Windows reparse-point adversarial races, production client data, live paid AI workflows, actual legal admissibility.

**Release gate:** NO-GO. This repository does not yet represent an operational evidence vault.
