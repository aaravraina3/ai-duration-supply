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

**S-03. Broad investment-grade universe.** Registered as "next" in
`10_PREREGISTRATION.md`, not in the upgrade plan. Serves sections 2 and 3: it is
the only real fix for power (hundreds of events instead of 16).

**S-04. Detrended cointegration or a time-trend control in C3.** Would test
whether the levels result survives removing the shared trend. Serves section 6.
Not built because it was not registered and would be chosen after seeing the
levels result.

**S-05. Separating the slope's trend from day-to-day timing in C5.** For example,
a detrended slope or a within-year version. Serves section 11 (timing). Same
reason as S-04.

**S-06. Issuer fixed effects in the D1 forecast.** Issuers differ a lot in size;
pooling all five may be what hurts the text rungs. Serves section 8.

**S-07. A placebo for the C4 weekly regression.** C4 used Newey-West only, as
registered, because it is a bound. A weekly placebo would make it comparable.
Serves section 11.

**S-08. Re-deriving the 0.123 reversion constant** behind the 2.56bp signal from
data. Serves section 9. It is inherited and hardcoded (DEBT #7).

**S-09. D3, Bayesian hierarchical event model.** Skipped by instruction.

**S-10. Kiefer-Vogelsang and EWC for the pooled and multi-horizon statistics.**
Only h = 0 to 5 single-horizon versions were built. Serves section 3.
