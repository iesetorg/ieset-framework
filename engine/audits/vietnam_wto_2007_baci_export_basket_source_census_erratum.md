# Vietnam WTO BACI source-census erratum — before flow-value access

The original registration is `e86a993760bd8bc463ff8687a458e55fe6710388` and the first, path-only runner correction is `bebb591ff7cec043a054b0c3df65bfec55e14e82`. The first `extract` attempt after that correction stopped at its frozen raw-row census before writing a source slice or analyzing any BACI flow. The original key-only scan counted the 55 nonexistent-destination rows but omitted additional historical variants with `country_exists_o=0`. This note and the runner census correction are committed before a source slice or result exists.

An independent recount of source **keys and country-existence flags only**, using the same pinned CEPII Gravity V202211 ZIP SHA-256 `7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1`, gives:

| Row class | Count |
| --- | ---: |
| Both countries existing | 495 |
| Origin nonexistent only | 297 |
| Destination nonexistent only | 55 |
| Both countries nonexistent | 33 |
| Total raw rows matching the frozen origin, destination and year grid | 880 |

The 495 existing-country rows cover all 495 registered origin–destination–year keys exactly once; there are no missing or duplicate valid keys. The registered selection rule already requires both `country_exists_o=1` and `country_exists_d=1`. This correction changes only the expected raw/excluded census (550/55 to 880/385) and the custody guard needed for a second pre-value amendment. It does not change the selected keys, treatment, donors, destinations, years, source vintage, estimand, thresholds, or verdict rules. No BACI flow magnitude or sign was inspected in either key-only recount or the failed extraction, and no source slice or result had been written at the time of this note.
