# Three-domain family range-order implementation erratum

The first run after source lock stopped before writing results: an endpoint
outside the preregistered admissible range reached `log()` before the same
frozen range gate could exclude its country. This correction moves the
transformation after the existing range check. It does not change endpoint
years, source keys, admissible ranges, status rules, complete-case logic,
model, sample or variation floors, influence limits, holdouts, multiplicity,
verdict rules, or credit. All failed gates remain `INCONCLUSIVE`.

The correction is a separate runner-and-erratum commit after source lock and
before any result packet. The runner verifies that the preregistered files
remain byte-identical and that all code outside the custody check and `frame`
function has the same parsed structure as the preregistration commit. The
first attempt produced no run artifacts.
