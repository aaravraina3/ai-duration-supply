"""Tests for the curve layer. A silent NSS/PCA failure poisons everything
downstream, so these run before any result is believed."""
import numpy as np, pandas as pd, sys
import curve as C
from eventlist import mod_duration

OK = True
def check(name, cond, detail=""):
    global OK
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")
    OK = OK and bool(cond)

def t_nss_recovers_known_curve():
    tau = np.array([0.25,0.5,1,2,3,5,7,10,20,30])
    true_b, l1, l2 = np.array([4.0, -1.5, 2.0, -1.0]), 1.5, 8.0
    y = C.nss_basis(tau, l1, l2) @ true_b
    bh, ssr = C.fit_betas(y, tau, l1, l2)
    check("NSS recovers betas on noiseless synthetic curve",
          np.allclose(bh, true_b, atol=1e-8), f"max err={np.abs(bh-true_b).max():.2e}")

def t_nss_asymptote():
    tau = np.array([1.0, 1e6])
    b = np.array([4.2, -1.0, 0.5, 0.3])
    y = C.nss_basis(tau, 1.5, 8.0) @ b
    check("beta0 is the long-run asymptote", abs(y[-1] - b[0]) < 1e-3, f"y(inf)={y[-1]:.6f} b0={b[0]}")

def t_lambda_grid_finds_truth():
    tau = np.array([0.25,0.5,1,2,3,5,7,10,20,30])
    l1, l2 = 1.087, 6.0
    rng = np.random.default_rng(0)
    B = rng.normal(size=(200,4)) @ np.diag([0.3,0.5,0.8,0.6]) + np.array([4,-1,1,0.5])
    Y = (C.nss_basis(tau, l1, l2) @ B.T).T
    (h1, h2), _ = C.grid_lambda(Y, tau)
    check("lambda grid search recovers true decay", abs(h1-l1) < 0.35 and abs(h2-l2) < 1.5,
          f"got ({h1:.3f},{h2:.3f}) vs true ({l1},{l2})")

def t_pca_shapes():
    z = C.load_gsw(start="2024-01-01")
    f, V, ev, dz = C.pca_factors(z)
    check("PC1-3 explain >98% of curve variance", ev[:3].sum() > 0.98, f"{ev[:3].sum()*100:.2f}%")
    L1, L2, L3 = V[:,0], V[:,1], V[:,2]
    check("PC1 is level (all loadings same sign)", np.all(L1 > 0), f"min={L1.min():.3f}")
    rho = np.corrcoef(np.arange(len(L2)), L2)[0,1]
    check("PC2 is slope (monotone in tenor)", rho < -0.9, f"corr(tenor,load)={rho:.3f}")
    check("PC3 is curvature (sign change, humped)", (L3[0]>0) and (L3.min()<0) and (L3[-1]>0),
          f"1y={L3[0]:+.3f} min={L3.min():+.3f} 30y={L3[-1]:+.3f}")
    check("factors are orthogonal", abs(np.corrcoef(f.f1, f.f2)[0,1]) < 1e-8,
          f"corr(f1,f2)={np.corrcoef(f.f1,f.f2)[0,1]:.2e}")

def t_pca_on_levels_is_wrong():
    """The doc's quirk: PCA on levels produces a factor driven by the nonstationary
    trend. The right diagnostic is persistence of the factor scores, not their
    variance share -- a trend factor has an AR(1) coefficient at ~1."""
    z = C.load_gsw(start="2024-01-01")
    Xl = z - z.mean()
    _, Vl = np.linalg.eigh(np.cov(Xl.values, rowvar=False))
    s_lv = pd.Series(Xl.values @ Vl[:, -1], index=z.index)
    f, _, _, _ = C.pca_factors(z)
    ar = lambda x: pd.Series(x).autocorr(1)
    check("levels PC1 scores are near-unit-root (spurious trend factor)",
          ar(s_lv) > 0.95, f"AR(1)={ar(s_lv):.4f}")
    check("changes PC1 scores are stationary", abs(ar(f.f1)) < 0.30, f"AR(1)={ar(f.f1):.4f}")

def t_duration():
    check("par bond duration < maturity", mod_duration(10, 4.5) < 10, f"D={mod_duration(10,4.5):.3f}")
    check("10y par duration in 7.5-8.5", 7.5 < mod_duration(10, 4.5) < 8.5, f"{mod_duration(10,4.5):.3f}")
    check("30y duration > 10y duration", mod_duration(30,5.0) > mod_duration(10,4.5),
          f"{mod_duration(30,5.0):.2f} vs {mod_duration(10,4.5):.2f}")
    check("floater has ~zero rate duration", mod_duration(5, None, True) <= 0.25)
    zero = mod_duration(2, 0.0)
    check("zero-coupon duration == maturity", abs(zero - 2.0) < 1e-9, f"{zero:.6f}")

def t_gsw_sane():
    z = C.load_gsw(start="2024-01-01")
    check("GSW has 30 tenors", z.shape[1] == 30, f"{z.shape}")
    check("GSW yields in plausible range", z.values.min() > 0 and z.values.max() < 10,
          f"[{z.values.min():.2f},{z.values.max():.2f}]")
    d = z.diff().abs().max().max()
    check("no absurd daily jumps (<75bp)", d < 0.75, f"max |dy|={d*100:.1f}bp")

if __name__ == "__main__":
    for fn in [t_nss_recovers_known_curve, t_nss_asymptote, t_lambda_grid_finds_truth,
               t_pca_shapes, t_pca_on_levels_is_wrong, t_duration, t_gsw_sane]:
        print(f"\n{fn.__name__}:"); fn()
    print("\n" + ("ALL CURVE TESTS PASSED" if OK else "SOME TESTS FAILED"))
    sys.exit(0 if OK else 1)
