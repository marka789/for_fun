"""Covariance matrices, PCA, and Marchenko-Pastur random matrix theory."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.optimize import minimize_scalar

from config import MP_GRID_POINTS, N_BINS_EIGENVALUE_HIST, OUTPUT_DIR


@dataclass
class UniverseResult:
    label: str
    n_assets: int
    n_observations: int
    q_ratio: float
    sigma2: float
    lambda_minus: float
    lambda_plus: float
    n_signal_eigenvalues: int
    n_noise_eigenvalues: int
    variance_explained_signal: float
    top_eigenvalue: float
    top_pc_variance_share: float


def sample_covariance(returns: pd.DataFrame) -> pd.DataFrame:
    """Unbiased sample covariance of return columns."""
    x = returns.values
    t = x.shape[0]
    centered = x - x.mean(axis=0, keepdims=True)
    cov = (centered.T @ centered) / (t - 1)
    return pd.DataFrame(cov, index=returns.columns, columns=returns.columns)


def correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """Pearson correlation matrix."""
    return returns.corr()


def marchenko_pastur_bounds(q: float, sigma2: float = 1.0) -> tuple[float, float]:
    """Upper and lower edges of the MP bulk for a q = N/T correlation matrix."""
    root = np.sqrt(q)
    lambda_minus = sigma2 * (1.0 - root) ** 2
    lambda_plus = sigma2 * (1.0 + root) ** 2
    return float(lambda_minus), float(lambda_plus)


def marchenko_pastur_pdf(
    lambdas: np.ndarray, q: float, sigma2: float = 1.0
) -> np.ndarray:
    """
    Marchenko-Pastur density for eigenvalues of a random correlation matrix.

    Laloux et al. (1999) formulation with Q = T/N (time over assets).
    We use q = N/T, so Q = 1/q.
    """
    q_inv = 1.0 / q
    lambda_minus, lambda_plus = marchenko_pastur_bounds(q, sigma2)

    density = np.zeros_like(lambdas, dtype=float)
    mask = (lambdas > lambda_minus) & (lambdas < lambda_plus)
    if not np.any(mask):
        return density

    lam = lambdas[mask]
    numerator = q_inv * np.sqrt((lambda_plus - lam) * (lam - lambda_minus))
    density[mask] = numerator / (2.0 * np.pi * sigma2 * lam)
    return density


def fit_mp_sigma2(eigenvalues: np.ndarray, q: float) -> float:
    """
    Fit sigma^2 in the MP law to bulk eigenvalues (excluding the market mode).

    Matches Laloux: choose sigma^2 so MP density best fits the empirical bulk.
    """
    evals = np.sort(eigenvalues)
    # Exclude the largest eigenvalue (market mode) from the fit.
    bulk = evals[:-1] if len(evals) > 1 else evals
    lam_minus, lam_plus = marchenko_pastur_bounds(q, sigma2=1.0)
    bulk = bulk[(bulk >= lam_minus) & (bulk <= lam_plus)]
    if bulk.size < 5:
        bulk = evals[1:] if len(evals) > 2 else evals

    def neg_log_likelihood(sigma2: float) -> float:
        if sigma2 <= 0:
            return 1e12
        pdf = marchenko_pastur_pdf(bulk, q=q, sigma2=sigma2)
        pdf = np.clip(pdf, 1e-12, None)
        return -float(np.sum(np.log(pdf)))

    result = minimize_scalar(
        neg_log_likelihood,
        bounds=(0.05, 1.5),
        method="bounded",
    )
    return float(result.x) if result.success else 1.0


def pca_eigendecomposition(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    PCA via eigendecomposition of a symmetric matrix.

    Returns eigenvalues (descending) and eigenvector matrix (columns).
    """
    evals, evecs = np.linalg.eigh(matrix)
    order = np.argsort(evals)[::-1]
    return evals[order], evecs[:, order]


def classify_eigenvalues(
    eigenvalues: np.ndarray, q: float, sigma2: float
) -> tuple[np.ndarray, np.ndarray]:
    """Split eigenvalues into signal (above MP upper edge) and noise bulk."""
    _, lambda_plus = marchenko_pastur_bounds(q, sigma2)
    signal_mask = eigenvalues > lambda_plus
    return signal_mask, ~signal_mask


def analyze_universe(
    returns: pd.DataFrame,
    label: str,
    output_dir: Path | None = None,
) -> UniverseResult:
    """
    Step 1: covariance / correlation matrices.
    Step 2: PCA eigendecomposition + Marchenko-Pastur RMT diagnostics.
    """
    output_dir = output_dir or OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    n_assets = returns.shape[1]
    n_obs = returns.shape[0]
    q = n_assets / n_obs

    # --- Step 1: covariance and correlation ---
    cov = sample_covariance(returns)
    corr = correlation_matrix(returns)

    cov_path = output_dir / f"{label}_covariance.parquet"
    corr_path = output_dir / f"{label}_correlation.parquet"
    cov.to_parquet(cov_path)
    corr.to_parquet(corr_path)

    # --- Step 2: PCA on correlation matrix (Laloux convention) ---
    corr_np = corr.values
    eigenvalues, eigenvectors = pca_eigendecomposition(corr_np)

    sigma2 = fit_mp_sigma2(eigenvalues, q=q)
    lam_minus, lam_plus = marchenko_pastur_bounds(q, sigma2)
    signal_mask, noise_mask = classify_eigenvalues(eigenvalues, q, sigma2)

    n_signal = int(signal_mask.sum())
    n_noise = int(noise_mask.sum())
    variance_explained_signal = float(eigenvalues[signal_mask].sum() / eigenvalues.sum())
    top_eigenvalue = float(eigenvalues[0])
    top_pc_share = float(eigenvalues[0] / eigenvalues.sum())

    # Save PCA outputs
    pc_df = pd.DataFrame(
        eigenvectors,
        index=returns.columns,
        columns=[f"PC{i+1}" for i in range(n_assets)],
    )
    eval_df = pd.DataFrame(
        {
            "eigenvalue": eigenvalues,
            "variance_share": eigenvalues / eigenvalues.sum(),
            "cumulative_variance_share": np.cumsum(eigenvalues) / eigenvalues.sum(),
            "is_signal": signal_mask,
        }
    )
    pc_df.to_parquet(output_dir / f"{label}_pca_eigenvectors.parquet")
    eval_df.to_parquet(output_dir / f"{label}_pca_eigenvalues.parquet")

    result = UniverseResult(
        label=label,
        n_assets=n_assets,
        n_observations=n_obs,
        q_ratio=q,
        sigma2=sigma2,
        lambda_minus=lam_minus,
        lambda_plus=lam_plus,
        n_signal_eigenvalues=n_signal,
        n_noise_eigenvalues=n_noise,
        variance_explained_signal=variance_explained_signal,
        top_eigenvalue=top_eigenvalue,
        top_pc_variance_share=top_pc_share,
    )

    summary_path = output_dir / f"{label}_rmt_summary.json"
    summary_path.write_text(json.dumps(asdict(result), indent=2))

    _plot_eigenvalue_spectrum(
        eigenvalues=eigenvalues,
        q=q,
        sigma2=sigma2,
        label=label,
        result=result,
        output_dir=output_dir,
    )
    _plot_pca_scree(eigenvalues, label, output_dir)
    _plot_top_pc_loadings(pc_df, label, output_dir, n_components=5)

    return result


def _plot_eigenvalue_spectrum(
    eigenvalues: np.ndarray,
    q: float,
    sigma2: float,
    label: str,
    result: UniverseResult,
    output_dir: Path,
) -> None:
    """Empirical eigenvalue density vs Marchenko-Pastur law (Laloux Figure 1 style)."""
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(12, 7))

    # Histogram of eigenvalues (excluding market mode for clearer bulk view).
    bulk_evals = eigenvalues[1:]
    ax.hist(
        bulk_evals,
        bins=N_BINS_EIGENVALUE_HIST,
        density=True,
        alpha=0.65,
        color="steelblue",
        edgecolor="white",
        label="Empirical eigenvalues (excl. market mode)",
    )

    lam_grid = np.linspace(
        max(result.lambda_minus * 0.5, 1e-4),
        result.lambda_plus * 1.05,
        MP_GRID_POINTS,
    )
    mp_density = marchenko_pastur_pdf(lam_grid, q=q, sigma2=sigma2)
    ax.plot(
        lam_grid,
        mp_density,
        color="crimson",
        linewidth=2.5,
        label=f"Marchenko-Pastur (q={q:.3f}, σ²={sigma2:.3f})",
    )

    ax.axvline(result.lambda_minus, color="gray", linestyle="--", alpha=0.8, label="λ₋")
    ax.axvline(result.lambda_plus, color="gray", linestyle="-.", alpha=0.8, label="λ₊")

    # Market mode inset annotation
    ax.annotate(
        f"Market mode λ₁ = {result.top_eigenvalue:.1f}\n"
        f"({100 * result.top_pc_variance_share:.1f}% of variance)",
        xy=(0.98, 0.95),
        xycoords="axes fraction",
        ha="right",
        va="top",
        fontsize=11,
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
    )

    ax.set_title(f"{label.upper()}: Eigenvalue Spectrum vs Marchenko-Pastur (since 2020)")
    ax.set_xlabel("Eigenvalue λ")
    ax.set_ylabel("Density")
    ax.legend(loc="upper left", fontsize=10)
    fig.tight_layout()
    fig.savefig(output_dir / f"{label}_eigenvalue_spectrum.png", dpi=150)
    plt.close(fig)


def _plot_pca_scree(eigenvalues: np.ndarray, label: str, output_dir: Path) -> None:
    """Scree plot for principal components."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    n_show = min(30, len(eigenvalues))
    axes[0].bar(range(1, n_show + 1), eigenvalues[:n_show], color="steelblue")
    axes[0].set_title("Top eigenvalues (scree)")
    axes[0].set_xlabel("Component")
    axes[0].set_ylabel("Eigenvalue")

    cumvar = np.cumsum(eigenvalues) / eigenvalues.sum()
    axes[1].plot(range(1, n_show + 1), cumvar[:n_show], marker="o", color="darkgreen")
    axes[1].axhline(0.8, color="gray", linestyle="--", alpha=0.6, label="80%")
    axes[1].set_title("Cumulative variance explained")
    axes[1].set_xlabel("Number of components")
    axes[1].set_ylabel("Cumulative share")
    axes[1].legend()

    fig.suptitle(f"{label.upper()} PCA Scree Plot")
    fig.tight_layout()
    fig.savefig(output_dir / f"{label}_pca_scree.png", dpi=150)
    plt.close(fig)


def _plot_top_pc_loadings(
    pc_df: pd.DataFrame,
    label: str,
    output_dir: Path,
    n_components: int = 5,
) -> None:
    """Bar chart of largest absolute loadings for top PCs."""
    fig, axes = plt.subplots(
        n_components, 1, figsize=(12, 3 * n_components), sharex=False
    )
    if n_components == 1:
        axes = [axes]

    for i, ax in enumerate(axes):
        pc = pc_df.iloc[:, i]
        top = pc.abs().sort_values(ascending=False).head(15)
        colors = ["crimson" if pc[t] < 0 else "steelblue" for t in top.index]
        ax.barh(top.index[::-1], pc[top.index][::-1], color=colors[::-1])
        ax.set_title(f"PC{i+1} — top 15 loadings by |weight|")
        ax.axvline(0, color="black", linewidth=0.8)

    fig.suptitle(f"{label.upper()}: Principal Component Loadings")
    fig.tight_layout()
    fig.savefig(output_dir / f"{label}_pca_loadings.png", dpi=150)
    plt.close(fig)
