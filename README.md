# Equity Covariance, PCA & Random Matrix Theory

Analysis workspace inspired by [Laloux et al. (1999)](https://arxiv.org/abs/cond-mat/9810255) — *Random Matrix Theory and Financial Correlations* — and common quant workflows for separating signal from noise in empirical correlation matrices.

## What this does

**Step 1 — Covariance matrices**
- Downloads daily adjusted-close prices for **S&P 500** (~500 stocks) and **Nasdaq-100** (~100 stocks) from **2020-01-01** onward
- Computes daily log returns and builds sample **covariance** and **correlation** matrices

**Step 2 — PCA + Random Matrix Theory**
- Eigendecomposes the correlation matrix (PCA)
- Compares the empirical eigenvalue spectrum to the **Marchenko-Pastur** distribution
- Classifies eigenvalues as **signal** (λ > λ₊) vs **noise** (within the MP bulk)
- Produces scree plots, eigenvalue spectrum plots, and top-PC loading charts

## Quick start

```bash
pip install -r requirements.txt
python run_analysis.py
```

Results are written to `outputs/`:
- `{universe}_covariance.parquet` / `{universe}_correlation.parquet`
- `{universe}_pca_eigenvalues.parquet` / `{universe}_pca_eigenvectors.parquet`
- `{universe}_rmt_summary.json`
- `{universe}_eigenvalue_spectrum.png`, `{universe}_pca_scree.png`, `{universe}_pca_loadings.png`

Cached price data lives in `data/`.

## Method notes

- **q = N/T** where N is the number of stocks and T is the number of return observations
- MP bounds: λ± = σ²(1 ± √q)²
- σ² is fit to the bulk eigenvalues (excluding the market mode), following Laloux
- Eigenvalues above λ₊ are treated as carrying genuine correlation structure (sectors, factors, market mode)

## Reference

Laloux, L., Cizeau, P., Bouchaud, J.-P., & Potters, M. (1999). Random matrix theory and financial correlations. *International Journal of Theoretical and Applied Finance*.
