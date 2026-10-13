# Decisions

Every judgment call the plan did not specify. Entries where I would have stopped
to ask are marked **NEEDS REVIEW** at the top. "Reversible" means how hard it is to
undo.

---

## Retroactive, made before the run-to-the-end instruction (2026-10-12)

**D-01. HC2 and HC3 added in B3.** Plan B3 asked for EWC and Kiefer-Vogelsang
fixed-b. I also computed HC0, HC2 and HC3 because the B3 diagnosis pointed at
leverage on 16 days. Alternatives: leave them out. Why: they test the specific
explanation found (few high-leverage days). This is a technique not in the plan;
logged in SCOPE.md too. Reversible: easy, three table columns.

**D-02. Kiefer-Vogelsang critical values simulated, not from the published
polynomial.** Simulated 5000 draws of the fixed-b null at the sample's T and M.
Alternative: the KV (2005) cubic approximation. Why: gives a p-value, not only a
5% cutoff, and avoids transcribing coefficients from memory. Reversible: easy.

**D-03. Bandwidths for EWC and fixed-b set to the LLSW (2018) rules,
B = 0.4 T^(2/3) and M = 1.3 T^(1/2).** The plan named the methods, not the
bandwidths. Reversible: easy.

**D-04. "Deal days" in diagnostics = the 16 largest values of the regressor.**
For the daily `dD` target, dD is nonzero almost every day, so "nonzero" was wrong
(that was a bug, fixed). Reversible: easy.

**D-05. T1 primary residuals from the controls-only model.** Explained in the
preregistration: the full model mechanically shrinks deal-day residuals.
Reversible: easy.

---

## Run-to-the-end decisions (2026-10-13 onward)

**NEEDS REVIEW. D-06. The "cannot be a persistent 30bp" claim is withdrawn.**
Traced to the local projections (day-5 b × 2026 supply = 2.4bp), not to a
retired level spec. Under the primary inference (timing-matched placebo, sd 0.101
at h = 5) the 95% upper bound on what persists from 2026 supply is about 41bp;
under Newey-West about 28bp. So this sample does not rule out a persistent 30bp
effect. Chosen: remove "rules out" wording from the paper and README; report the
point estimate and both bounds; leave the stock question to C3. Alternatives: keep
the claim on the Newey-West bound (rejected: Newey-West is comparison only), or
keep the point-estimate claim without a bound (rejected: overclaims). This changes
a main conclusion. Reversible: easy (wording).

**D-07. T4 window correction uses Holm.** Decision 1 asked for "the multiple-
window correction". Chosen: Holm across the three windows, Bonferroni reported
alongside. Holm is uniformly at least as powerful as Bonferroni with the same
guarantee. Reversible: easy.

**D-08. Interview guide synced beyond the two requested edits.** Asked: remove the
"quieter days" line and add T1 to T4. Also changed, because the guide would
otherwise contradict the repo: persistence wording (approved A2 phrase), the
withdrawn 30bp claim (D-06), the Newey-West explanation (B3 showed it is not
autocorrelation), "replicates" to "is consistent with" (A9), and 8 of 11 to the
all-16 result. A final sync happens at the end of the run. The guide is a local
file outside the repo. Reversible: easy.
