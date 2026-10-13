# Scope parking lot

Things considered that are not in `UPGRADE_PLAN.md`. Not built unless marked
otherwise. Each item: what it is, which spine section it would serve, why it
might be worth doing later.

---

**S-01. HC2 / HC3 leverage-corrected standard errors.** *Built anyway, in B3
(see DECISIONS D-01).* Serves section 3, Inference. Flagged here because it was
outside the plan's list.

**S-02. Explaining the other half of the OLS-to-HAC gap (T3).** T3 found the
deal-day variance gap closes 52%. The rest likely comes from how residual size
covaries with deal size across the 16 days, since HC0 weights each squared
residual by the squared shock. Serves section 3. Worth doing only if a reader
asks; randomization is primary, so it does not change conclusions.
