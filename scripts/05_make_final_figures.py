#!/usr/bin/env python
"""Generate publication figures from clean-pipeline summary tables."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter
import numpy as np
import pandas as pd


def save(fig, out: Path, stem: str) -> None:
    fig.tight_layout()
    fig.savefig(out / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(out / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def _remove_obsolete(out: Path) -> None:
    stems = [
        "fig_local_m10_gain_vs_N",
        "fig_local_m10_T300_gain_vs_N",
        "fig_N1600_perturbation_scale",
        "fig_N1600_within_state_scale",
        "fig_N1600_scale_control",
    ]
    for stem in stems:
        for suffix in (".png", ".pdf"):
            path = out / f"{stem}{suffix}"
            if path.exists():
                path.unlink()


def _errorbar_by_n(ax, subset: pd.DataFrame, *, marker: str, label: str) -> None:
    y = 100.0 * subset.gain.to_numpy()
    lower = 100.0 * subset.ci95_lower.to_numpy()
    upper = 100.0 * subset.ci95_upper.to_numpy()
    yerr = np.vstack([y - lower, upper - y])
    ax.errorbar(
        subset.N.to_numpy(),
        y,
        yerr=yerr,
        marker=marker,
        capsize=3,
        linewidth=1.4,
        markersize=6.5,
        label=label,
    )


def _algorithm_points(
    ax,
    subset: pd.DataFrame,
    *,
    x_order: list[int],
    x_values: np.ndarray,
    x_column: str,
    analysis: str,
) -> None:
    """Plot Ridge/HGB point estimates with 95% bootstrap intervals."""
    analysis_subset = subset[subset.analysis == analysis]
    for offset, (algorithm, marker, label) in zip(
        [-0.055, 0.055],
        [("ridge", "o", "Ridge"), ("hgb", "s", "HGB")],
        strict=True,
    ):
        data = analysis_subset[analysis_subset.algorithm == algorithm].set_index(x_column)
        if not all(value in data.index for value in x_order):
            raise ValueError(
                f"{analysis}: missing {algorithm} result(s) for {x_column}={x_order}"
            )
        values = np.array([100.0 * float(data.loc[value].gain) for value in x_order])
        lower = np.array(
            [100.0 * float(data.loc[value].ci95_lower) for value in x_order]
        )
        upper = np.array(
            [100.0 * float(data.loc[value].ci95_upper) for value in x_order]
        )
        ax.errorbar(
            x_values + offset,
            values,
            yerr=np.vstack([values - lower, upper - values]),
            marker=marker,
            linestyle="none",
            capsize=4,
            markersize=7,
            label=label,
        )


def _panel_label(ax, label: str) -> None:
    ax.text(
        0.02,
        0.97,
        label,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontweight="bold",
    )


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", default=str(root / "results" / "final"))
    parser.add_argument("--figures-root", default=str(root / "figures" / "final"))
    args = parser.parse_args()

    tables = Path(args.results_root) / "tables"
    out = Path(args.figures_root)
    out.mkdir(parents=True, exist_ok=True)
    _remove_obsolete(out)

    # ------------------------------------------------------------------
    # Main Figure 1: global structural information across N.
    # ------------------------------------------------------------------
    global_file = tables / "global_information_summary.csv"
    if global_file.is_file():
        data = pd.read_csv(global_file)
        fig, ax = plt.subplots(figsize=(7.2, 4.6))
        specs = [
            ("M0->M1", "o", r"$M_0 \rightarrow M_1$: all global mesostructure"),
            ("P0->Pk", "s", r"$P_0 \rightarrow P_k$: mean degree after nonlinear $\Phi$"),
        ]
        for comparison, marker, label in specs:
            subset = data[data.comparison == comparison].sort_values("N")
            if not subset.empty:
                _errorbar_by_n(ax, subset, marker=marker, label=label)
        ax.set_xscale("log")
        ax.set_xticks([100, 400, 1600], ["100", "400", "1600"])
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_xlabel(r"System size, $N$")
        ax.set_ylabel("Fraction of baseline MSE removed (%)")
        ax.axhline(0, linewidth=0.8, linestyle="--")
        ax.legend(frameon=False)
        save(fig, out, "fig_global_information_gain")

    # ------------------------------------------------------------------
    # Main Figure 2: unified local-information / perturbation-scale result.
    # ------------------------------------------------------------------
    matched_file = tables / "local_matched_horizon_summary.csv"
    if not matched_file.is_file():
        print(f"Final figures written to {out}")
        return

    matched = pd.read_csv(matched_file)
    matched = matched[matched.response_window == 300].copy()

    # A: fixed m=10 across N=400 and N=1600.
    fixed_m10 = matched[(matched.m == 10) & (matched.N.isin([400, 1600]))]
    # B/C: fixed N=1600 across m=10 and m=160.
    n1600 = matched[(matched.N == 1600) & (matched.m.isin([10, 160]))]

    if (
        fixed_m10["N"].nunique() == 2
        and n1600["m"].nunique() == 2
    ):
        fig, axes = plt.subplots(1, 3, figsize=(13.4, 4.35))

        # Panel A: fixed absolute perturbation size across system size.
        x_a = np.array([0.0, 1.0])
        _algorithm_points(
            axes[0],
            fixed_m10,
            x_order=[400, 1600],
            x_values=x_a,
            x_column="N",
            analysis="MG->M2",
        )
        axes[0].set_xticks(x_a, ["400", "1600"])
        axes[0].set_xlabel(r"System size, $N$ ($m=10$)")
        axes[0].set_ylabel(r"$M_G \rightarrow M_2$ gain (%)")
        axes[0].axhline(0, linewidth=0.8, linestyle="--")
        axes[0].set_title(r"Fixed local perturbation, $T=300$")
        _panel_label(axes[0], "A")

        # Panel B: intervention-scale control at fixed N.
        x_bc = np.array([0.0, 1.0])
        _algorithm_points(
            axes[1],
            n1600,
            x_order=[10, 160],
            x_values=x_bc,
            x_column="m",
            analysis="MG->M2",
        )
        axes[1].set_xticks(x_bc, [r"$m=10$", r"$m=160$ ($p=0.1$)"])
        axes[1].set_xlabel(r"Perturbation size, $m$")
        axes[1].set_ylabel(r"$M_G \rightarrow M_2$ gain (%)")
        axes[1].axhline(0, linewidth=0.8, linestyle="--")
        axes[1].set_title(r"Scale control at $N=1600$, $T=300$")
        _panel_label(axes[1], "B")

        # Panel C: within-state control at fixed N.
        _algorithm_points(
            axes[2],
            n1600,
            x_order=[10, 160],
            x_values=x_bc,
            x_column="m",
            analysis="within_state",
        )
        axes[2].set_xticks(x_bc, [r"$m=10$", r"$m=160$ ($p=0.1$)"])
        axes[2].set_xlabel(r"Perturbation size, $m$")
        axes[2].set_ylabel("Within-state gain (%)")
        axes[2].axhline(0, linewidth=0.8, linestyle="--")
        axes[2].set_title(r"Within-state control, $N=1600$")
        _panel_label(axes[2], "C")

        # One legend for the whole local-result figure.
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(
            handles,
            labels,
            frameon=False,
            loc="upper center",
            bbox_to_anchor=(0.5, 1.02),
            ncol=2,
        )
        fig.subplots_adjust(top=0.83, wspace=0.34)
        fig.savefig(
            out / "fig_local_information_scale_summary.png",
            dpi=300,
            bbox_inches="tight",
        )
        fig.savefig(
            out / "fig_local_information_scale_summary.pdf",
            bbox_inches="tight",
        )
        plt.close(fig)

    print(f"Final figures written to {out}")


if __name__ == "__main__":
    main()
