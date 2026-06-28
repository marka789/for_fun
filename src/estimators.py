"""Hedge-ratio estimators for pairs trading.

Three estimators are implemented so we can reproduce the head-to-head
comparison from Palomar (2025), Chapter 15.6 -- the exact reference RuujSs
builds his article on:

  1. rolling_ols      - classic rolling least-squares (the baseline RuujSs
                        criticises: arbitrary window, discontinuous jumps).
  2. kalman_basic     - state = (mu_t, gamma_t), random-walk transition.
                        Book eq. (15.3).
  3. kalman_momentum  - state = (mu_t, gamma_t, gamma_dot_t). Book eq. (15.4).

All estimators are *causal*: the hedge ratio / intercept used to evaluate the
spread at time t depends only on information up to time t-1 (the Kalman
predicted state alpha_{t|t-1}), so there is no look-ahead bias.

Regression convention: y1 ~ mu + gamma * y2  (y1 is the dependent leg).
Every estimator returns a DataFrame indexed by the original dates with
columns: gamma, mu, spread, and (for Kalman) innovation, innovation_var,
kalman_z, p_trace.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def rolling_ols(y1: pd.Series, y2: pd.Series, lookback: int = 504) -> pd.DataFrame:
    """Causal rolling OLS hedge ratio and intercept.

    lookback defaults to ~2 years (504 trading days), matching the book's
    rolling-LS configuration. The estimate at t uses the window [t-lookback, t)
    i.e. strictly past data, so the spread at t has no look-ahead.
    """
    idx = y1.index
    v1 = y1.astype(float).values
    v2 = y2.astype(float).values
    n = len(v1)
    gamma = np.full(n, np.nan)
    mu = np.full(n, np.nan)

    for i in range(lookback, n):
        wy1 = v1[i - lookback : i]
        wy2 = v2[i - lookback : i]
        m2 = wy2.mean()
        m1 = wy1.mean()
        var2 = ((wy2 - m2) ** 2).sum()
        if var2 <= 0:
            continue
        g = ((wy2 - m2) * (wy1 - m1)).sum() / var2
        gamma[i] = g
        mu[i] = m1 - g * m2

    spread = v1 - gamma * v2 - mu
    norm_spread = spread / (1.0 + np.abs(gamma))
    return pd.DataFrame(
        {"gamma": gamma, "mu": mu, "spread": spread, "norm_spread": norm_spread},
        index=idx,
    )


def kalman_basic(y1: pd.Series, y2: pd.Series, alpha: float = 1e-5,
                 t_ls: int = 252) -> pd.DataFrame:
    """Basic Kalman hedge ratio, book eq. (15.3)."""
    return _run_kalman(y1, y2, alpha=alpha, t_ls=t_ls, momentum=False)


def kalman_momentum(y1: pd.Series, y2: pd.Series, alpha: float = 1e-6,
                    t_ls: int = 252) -> pd.DataFrame:
    """Kalman with hedge-ratio velocity, book eq. (15.4)."""
    return _run_kalman(y1, y2, alpha=alpha, t_ls=t_ls, momentum=True)


# --------------------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------------------

def _ls_seed(y1, y2, t_ls):
    n = min(t_ls, len(y1))
    a = y2[:n]
    b = y1[:n]
    m2 = a.mean()
    m1 = b.mean()
    var2 = ((a - m2) ** 2).sum()
    g = ((a - m2) * (b - m1)).sum() / var2
    mu = m1 - g * m2
    resid = b - (mu + g * a)
    var_eps = resid.var(ddof=1)
    var_y2 = y2.var(ddof=1)
    return g, mu, float(var_eps), float(var_y2), n


def _run_kalman(y1s: pd.Series, y2s: pd.Series, alpha, t_ls, momentum) -> pd.DataFrame:
    idx = y1s.index
    y1 = y1s.astype(float).values
    y2 = y2s.astype(float).values
    g0, mu0, var_eps, var_y2, n = _ls_seed(y1, y2, t_ls)
    T = len(y1)

    R = var_eps
    s_mu2 = alpha * var_eps
    s_gamma2 = alpha * var_eps / var_y2

    if not momentum:
        x = np.array([mu0, g0], dtype=float)
        P = np.diag([var_eps / n, var_eps / var_y2 / n]).astype(float)
        F = np.eye(2)
        Q = np.diag([s_mu2, s_gamma2])
    else:
        x = np.array([mu0, g0, 0.0], dtype=float)
        P = np.diag([var_eps / n, var_eps / var_y2 / n,
                     var_eps / var_y2 / n]).astype(float)
        F = np.array([[1.0, 0.0, 0.0],
                      [0.0, 1.0, 1.0],
                      [0.0, 0.0, 1.0]])
        Q = np.diag([s_mu2, s_gamma2, s_gamma2])

    gamma_pred = np.full(T, np.nan)
    mu_pred = np.full(T, np.nan)
    innov = np.full(T, np.nan)
    innov_var = np.full(T, np.nan)
    p_trace = np.full(T, np.nan)

    for t in range(T):
        # Predict (alpha_{t|t-1})
        x = F @ x
        P = F @ P @ F.T + Q

        if not momentum:
            H = np.array([1.0, y2[t]])
        else:
            H = np.array([1.0, y2[t], 0.0])

        mu_pred[t] = x[0]
        gamma_pred[t] = x[1]
        p_trace[t] = np.trace(P)

        # Innovation against predicted state
        e = y1[t] - H @ x
        S = H @ P @ H.T + R
        innov[t] = e
        innov_var[t] = S

        # Update (alpha_{t|t})
        K = (P @ H) / S
        x = x + K * e
        P = P - np.outer(K, H @ P)

    spread = y1 - gamma_pred * y2 - mu_pred
    norm_spread = spread / (1.0 + np.abs(gamma_pred))
    return pd.DataFrame(
        {
            "gamma": gamma_pred,
            "mu": mu_pred,
            "spread": spread,
            "norm_spread": norm_spread,
            "innovation": innov,
            "innovation_var": innov_var,
            "kalman_z": innov / np.sqrt(innov_var),
            "p_trace": p_trace,
        },
        index=idx,
    )
