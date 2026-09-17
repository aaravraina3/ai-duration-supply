"""§4.1 Nelson-Siegel-Svensson, §4.2 PCA, §4.3 key rate durations.

Design note on which yields feed which step:
  * NSS is fit to the FRED CMT par grid, as the doc specifies. It is used for
    descriptives and for the curve-shape plot, not for the concession.
  * PCA and the concession run on GSW zero-coupon yields (SVENY01..SVENY30).
    They are zero-coupon (what ACM needs) and give 30 tenor points, which the
    +/-2y exclusion band requires. An 11-point par grid does not survive the band.
"""
import numpy as np, pandas as pd
from config import PROC, FIG, FRED_TENORS, PCA_TENORS, SAMPLE_START, SAMPLE_END

# ---------------------------------------------------------------- loaders
def load_fred():
    d = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
    return d

def load_gsw(start=None, end=None, nmax=30):
    d = pd.read_csv(PROC / "gsw.csv", parse_dates=["Date"]).set_index("Date")
    cols = [f"SVENY{i:02d}" for i in range(1, nmax + 1)]
    z = d[cols].dropna(how="all")
    if start: z = z[z.index >= start]
    if end:   z = z[z.index <= end]
    z.columns = [float(c[-2:]) for c in z.columns]
    z.index.name = "date"
    return z.dropna()

# ---------------------------------------------------------------- NSS
def nss_basis(tau, lam1, lam2):
    tau = np.asarray(tau, float)
    x1, x2 = tau / lam1, tau / lam2
    b1 = (1 - np.exp(-x1)) / x1
    b2 = b1 - np.exp(-x1)
    b3 = (1 - np.exp(-x2)) / x2 - np.exp(-x2)
    return np.column_stack([np.ones_like(tau), b1, b2, b3])

def fit_betas(y, tau, lam1, lam2):
    """Linear in beta given lambda -> plain least squares."""
    X = nss_basis(tau, lam1, lam2)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    return beta, float(resid @ resid)

def grid_lambda(Y, tau, l1grid=None, l2grid=None):
    """Full-sample lambda grid search. Lambdas are fixed once so daily betas stay
    comparable across days (the doc's quirk #2)."""
    l1grid = np.linspace(0.5, 5.0, 24) if l1grid is None else l1grid
    l2grid = np.linspace(2.0, 15.0, 27) if l2grid is None else l2grid
    best = (None, np.inf)
    for l1 in l1grid:
        for l2 in l2grid:
            if l2 <= l1 + 0.25 and l2 < 1e5:   # keep the two humps identified
                continue
            X = nss_basis(tau, l1, l2)
            B, *_ = np.linalg.lstsq(X, Y.T, rcond=None)      # all days at once
            ssr = float(((Y.T - X @ B) ** 2).sum())
            if ssr < best[1]:
                best = ((l1, l2), ssr)
    return best

def fit_nss_panel(df=None, svensson=True, start=SAMPLE_START, end=SAMPLE_END):
    if df is None:
        df = load_fred()
    df = df.loc[start:end]
    tenors = [FRED_TENORS[c] for c in FRED_TENORS]
    Y = df[list(FRED_TENORS)].dropna()
    tau = np.array(tenors)
    if svensson:
        (l1, l2), ssr = grid_lambda(Y.values, tau)
    else:   # plain Nelson-Siegel: drop the second hump by pinning beta3 out
        (l1, l2), ssr = grid_lambda(Y.values, tau, l2grid=np.array([1e6]))
    X = nss_basis(tau, l1, l2)
    if not svensson:
        X = X[:, :3]
    B, *_ = np.linalg.lstsq(X, Y.values.T, rcond=None)
    cols = ["b0", "b1", "b2", "b3"][:X.shape[1]]
    betas = pd.DataFrame(B.T, index=Y.index, columns=cols)
    fitted = pd.DataFrame((X @ B).T, index=Y.index, columns=Y.columns)
    rmse = float(np.sqrt(((Y - fitted) ** 2).values.mean())) * 100  # bp
    betas.attrs["lambda"] = (l1, l2)
    return betas, fitted, Y, (l1, l2), rmse

# ---------------------------------------------------------------- PCA
def pca_factors(z, tenors=None, demean=True):
    """PCA on daily CHANGES (levels are nonstationary -> spurious factor 1)."""
    dz = z.diff().dropna()
    if tenors is not None:
        dz = dz[tenors]
    Xc = dz - dz.mean() if demean else dz
    C = np.cov(Xc.values, rowvar=False)
    w, V = np.linalg.eigh(C)
    idx = np.argsort(w)[::-1]
    w, V = w[idx], V[:, idx]
    V = V * np.sign(V.sum(axis=0))          # orient: level loading positive
    f = pd.DataFrame(Xc.values @ V[:, :3], index=dz.index, columns=["f1", "f2", "f3"])
    return f, V, w / w.sum(), dz

if __name__ == "__main__":
    print("=== NSS on FRED par curve ===")
    betas, fitted, Y, (l1, l2), rmse = fit_nss_panel()
    print(f"  lambda1={l1:.3f}  lambda2={l2:.3f}   in-sample RMSE={rmse:.2f} bp   n={len(Y)}")
    print(f"  beta3 stability: sd={betas.b3.std():.3f}, range=({betas.b3.min():.2f},{betas.b3.max():.2f})")
    print(betas.tail(3).round(3).to_string())
    betas.to_csv(PROC / "nss_betas.csv")

    print("\n=== PCA on GSW zero curve, daily changes ===")
    z = load_gsw(start="2024-01-01")
    f, V, ev, dz = pca_factors(z)
    print(f"  n={len(dz)} days, {z.shape[1]} tenors")
    print(f"  explained variance: {np.round(ev[:5]*100,2)}  (cum3={ev[:3].sum()*100:.2f}%)")
    for k in range(3):
        L = V[:, k]
        print(f"  PC{k+1} loadings 1y/5y/10y/20y/30y: "
              f"{L[0]:+.3f} {L[4]:+.3f} {L[9]:+.3f} {L[19]:+.3f} {L[29]:+.3f}")
    f.to_csv(PROC / "pca_factors.csv")
    np.save(PROC / "pca_loadings.npy", V)
