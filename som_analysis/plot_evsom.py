"""
Evolution SOM Diagnostic Plots for NYC Flash Flood Analysis
By: Ty Janoski

Generates animated GIFs (one per node) showing the synoptic evolution
over N hours, plus a static key-hours panel and standard diagnostics
(U-matrix, hit map, monthly histogram).

Usage:
    python -m som_analysis.plot_evsom --moisture-var thetae
    python -m som_analysis.plot_evsom --moisture-var thetae --n-hours 24 --fps 4
    python -m som_analysis.plot_evsom --moisture-var thetae --skip-anim
"""

import argparse
import os
from itertools import combinations

import cartopy.crs as ccrs
import cmweather  # noqa: F401
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from scipy.stats import chi2_contingency

from .config import MOISTURE_CONFIGS, SOM_INTERMEDIATE_PATH, get_evsom_paths, setup_plotting
from .helpers import add_map_features, get_node_indices, load_moist_var


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate diagnostic plots for a trained evolution SOM."
    )
    parser.add_argument(
        "--moisture-var",
        required=True,
        choices=list(MOISTURE_CONFIGS.keys()),
        help="Moisture variable (IVT, tcwv, thetae).",
    )
    parser.add_argument(
        "--n-hours",
        type=int,
        default=24,
        help="Number of hourly frames used during training (default: 24).",
    )
    parser.add_argument(
        "--moisture-weight",
        type=float,
        default=1,
        help="Moisture weight used during training (default: 1).",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=4,
        help="Frames per second for animated GIFs (default: 4).",
    )
    parser.add_argument(
        "--key-hours",
        type=int,
        nargs="+",
        default=None,
        help=(
            "Hour offsets (relative to event time T=0) to show in the key-hours panel. "
            "Default: evenly spaced selection from the window."
        ),
    )
    parser.add_argument(
        "--skip-anim",
        action="store_true",
        help="Skip animated GIF generation.",
    )
    return parser.parse_args()


def _default_key_hours(n_hours, n_panels=4):
    """Return n_panels evenly spaced hour offsets ending at 0."""
    offsets = np.arange(n_hours) - (n_hours - 1)  # T-(n-1) ... T+0
    indices = np.round(np.linspace(0, n_hours - 1, n_panels)).astype(int)
    return [int(offsets[i]) for i in indices]


def main():
    args = parse_args()
    setup_plotting()

    cfg = MOISTURE_CONFIGS[args.moisture_var]
    paths = get_evsom_paths(args.moisture_var, args.moisture_weight, args.n_hours)
    fig_dir = paths["fig_dir"]
    _lbl = paths["file_label"]
    moist_label = cfg["label"]
    moist_label_short = cfg["label_short"]
    pfx = cfg["file_prefix"]
    var_name = cfg["var_name"]

    xdim, ydim = 2, 2
    n_hours = args.n_hours
    hour_offsets = np.arange(n_hours) - (n_hours - 1)  # T-(n-1) ... T+0

    os.makedirs(f"{fig_dir}/node-animations", exist_ok=True)
    os.makedirs(f"{fig_dir}/key-hours", exist_ok=True)

    # ── Load cached SOM results ───────────────────────────────────────────────
    cache_path = os.path.join(fig_dir, ".cache", "som_results.npz")
    print(f"Loading SOM results from {cache_path} ...")
    cached = np.load(cache_path)
    z500_nodes = cached["z500_nodes"]   # (xdim, ydim, n_hours, lat_z, lon_z)
    moist_nodes = cached["moist_nodes"] # (xdim, ydim, n_hours, lat_m, lon_m)
    bmus = cached["bmus"]
    u_matrix = cached["u_matrix"]
    hit_map = cached["hit_map"]
    coords = cached["coords"]
    lat_z = cached["lat_z"]
    lon_z = cached["lon_z"]
    lat_m = cached["lat_m"]
    lon_m = cached["lon_m"]

    # Use Z500 coordinates for all plotting (they share the same domain)
    lat = lat_z
    lon = lon_z

    # ── U-matrix and hit map ──────────────────────────────────────────────────
    print("Plotting U-matrix and hit map ...")
    fig, axes = plt.subplots(1, 2, layout="constrained", figsize=(6, 3), dpi=600)

    im0 = axes[0].imshow(u_matrix, cmap="viridis", origin="lower")
    axes[0].set_title("U-Matrix (Mean Inter-Node Distance)", fontsize=7)
    fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04, shrink=0.7)

    im1 = axes[1].imshow(hit_map, cmap="plasma", origin="lower")
    axes[1].set_title("Hit Map (Samples per Node)", fontsize=7)
    fig.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04, shrink=0.7)

    for ax in axes:
        ax.set_xticks(np.arange(xdim))
        ax.set_yticks(np.arange(ydim))
        ax.set_xlabel("X-index", fontsize=6)
        ax.set_ylabel("Y-index", fontsize=6)

    plt.savefig(f"{fig_dir}/Z500_{_lbl}_evsom_u_matrix_hit_map.png")
    plt.close()

    # ── Animated GIFs (one per node) ─────────────────────────────────────────
    if not args.skip_anim:
        print("Generating animated GIFs ...")
        levels_z = np.arange(-1.4, 1.41, 0.2)
        levels_m = cfg["levels_weights"]

        for i in range(xdim):
            for j in range(ydim):
                print(f"  Node ({i},{j}) ...")
                fig, ax = plt.subplots(
                    1, 1,
                    figsize=(5, 3.2),
                    subplot_kw={"projection": ccrs.PlateCarree()},
                    dpi=150,
                )

                # Draw first frame to anchor the colorbar
                z_frame0 = z500_nodes[i, j, 0]
                m_frame0 = moist_nodes[i, j, 0]

                cf0 = ax.contourf(
                    lon_z, lat_z, m_frame0,
                    levels=levels_m, cmap="balance",
                    transform=ccrs.PlateCarree(), extend="both",
                )
                ax.contour(
                    lon_z, lat_z, z_frame0,
                    levels=levels_z, colors="black", linewidths=0.5,
                    transform=ccrs.PlateCarree(),
                )
                add_map_features(ax)
                cbar = fig.colorbar(cf0, ax=ax, orientation="horizontal", pad=0.04,
                                    fraction=0.046, shrink=0.9)
                cbar.set_label(f"Standardized {moist_label_short} Anomaly", fontsize=6)
                cbar.ax.tick_params(labelsize=5)
                ax.set_title(
                    f"Node ({i},{j})  —  T{int(hour_offsets[0]):+d}h", fontsize=7
                )

                fig.tight_layout()

                def _hour_label(h_off):
                    if h_off < 0:
                        return f"T{h_off:+d}h"
                    elif h_off == 0:
                        return "T+0h"
                    return f"T+{h_off}h"

                def update(frame_idx, ax=ax, i=i, j=j):
                    ax.cla()  # clear axis; colorbar stays on figure
                    add_map_features(ax)

                    z_fr = z500_nodes[i, j, frame_idx]
                    m_fr = moist_nodes[i, j, frame_idx]
                    ax.contourf(
                        lon_z, lat_z, m_fr,
                        levels=levels_m, cmap="balance",
                        transform=ccrs.PlateCarree(), extend="both",
                    )
                    ax.contour(
                        lon_z, lat_z, z_fr,
                        levels=levels_z, colors="black", linewidths=0.5,
                        transform=ccrs.PlateCarree(),
                    )
                    h_off = int(hour_offsets[frame_idx])
                    ax.set_title(
                        f"Node ({i},{j})  —  {_hour_label(h_off)}", fontsize=7
                    )
                    return []

                anim = animation.FuncAnimation(
                    fig, update, frames=n_hours, interval=1000 // args.fps, blit=False
                )
                gif_path = f"{fig_dir}/node-animations/node_{i}_{j}_evsom.gif"
                writer = animation.PillowWriter(fps=args.fps)
                anim.save(gif_path, writer=writer)
                plt.close(fig)
                print(f"    Saved {gif_path}")
    else:
        print("Skipping animated GIFs (--skip-anim).")

    # ── Static key-hours panel ────────────────────────────────────────────────
    print("Plotting key-hours panel ...")
    if args.key_hours is not None:
        key_hours = args.key_hours
    else:
        key_hours = _default_key_hours(n_hours, n_panels=4)

    # Map hour offset → index into n_hours axis
    offset_to_idx = {int(h): k for k, h in enumerate(hour_offsets)}
    key_indices = []
    for h in key_hours:
        if h not in offset_to_idx:
            # Find closest available
            closest = min(offset_to_idx.keys(), key=lambda x: abs(x - h))
            print(f"  Warning: hour_offset={h} not in data; using {closest} instead.")
            h = closest
        key_indices.append(offset_to_idx[h])
    key_hours_actual = [int(hour_offsets[k]) for k in key_indices]

    n_cols = len(key_indices)
    n_rows = xdim * ydim  # one row per node

    levels_z = np.arange(-1.4, 1.41, 0.2)
    levels_m = cfg["levels_weights"]

    fig, axes = plt.subplots(
        n_rows, n_cols,
        figsize=(2.5 * n_cols, 2.2 * n_rows),
        subplot_kw={"projection": ccrs.PlateCarree()},
        constrained_layout=True,
        dpi=300,
    )
    if n_rows == 1:
        axes = axes[np.newaxis, :]
    if n_cols == 1:
        axes = axes[:, np.newaxis]

    for row, (i, j) in enumerate([(a, b) for a in range(xdim) for b in range(ydim)]):
        for col, (h_idx, h_off) in enumerate(zip(key_indices, key_hours_actual)):
            ax = axes[row, col]
            z_fr = z500_nodes[i, j, h_idx]
            m_fr = moist_nodes[i, j, h_idx]

            im = ax.contourf(
                lon_z, lat_z, m_fr,
                levels=levels_m, cmap="balance",
                transform=ccrs.PlateCarree(), extend="both",
            )
            ax.contour(
                lon_z, lat_z, z_fr,
                levels=levels_z, colors="black", linewidths=0.4,
                transform=ccrs.PlateCarree(),
            )
            add_map_features(ax)

            if row == 0:
                t_str = f"T{h_off:+d}h" if h_off != 0 else "T+0h"
                ax.set_title(t_str, fontsize=6)
            if col == 0:
                n_ev = int(hit_map.T[i, j])
                ax.set_ylabel(f"({i},{j}) N={n_ev}", fontsize=5, labelpad=2)

    # Shared colorbar
    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.5, pad=0.02)
    cbar.set_label(f"Standardized {moist_label_short} Anomaly", fontsize=6)
    cbar.ax.tick_params(labelsize=5)

    plt.suptitle(
        f"Evolution SOM Key Hours: Z500 (contoured) + {moist_label_short} (shaded)",
        fontsize=8,
    )
    out_key = f"{fig_dir}/key-hours/key_hours_{_lbl}.png"
    plt.savefig(out_key, bbox_inches="tight")
    plt.close()
    print(f"  Saved {out_key}")

    # ── Monthly histograms ────────────────────────────────────────────────────
    print("Plotting monthly histograms ...")
    bmu_df = pd.read_csv(paths["bmu_csv_path"])
    months = pd.to_datetime(bmu_df["timestamp"]).dt.month.to_numpy()

    month_counts = {}
    for i in range(xdim):
        for j in range(ydim):
            idx = get_node_indices(bmus, i, j)
            node_months = months[idx]
            month_counts[(i, j)] = np.bincount(node_months, minlength=13)[1:]

    month_labels = ["May", "Jun", "Jul", "Aug", "Sep", "Oct"]
    fig, axes = plt.subplots(
        ydim, xdim, figsize=(6, 3.7), constrained_layout=True, dpi=600
    )

    for i in range(xdim):
        for j in range(ydim):
            ax = axes[j, i]
            monthly = month_counts[(i, j)][4:10]
            ax.bar(month_labels, monthly, color="teal", alpha=0.9, width=0.8)
            ax.set_title(f"({i},{j})  N={monthly.sum()}", fontsize=6)
            ax.tick_params(axis="x", bottom=False, labelsize=5)
            ax.set_ylim(0, 18)
            ax.set_yticks(np.arange(0, 17, 2))
            ax.grid(True, linewidth=0.3, alpha=0.5, axis="y")

    plt.suptitle(
        "Warm-Season (May\u2013Oct) Event Distribution per Evolution SOM Node",
        fontsize=8,
        y=1.04,
    )
    plt.savefig(
        f"{fig_dir}/Z500_{_lbl}_evsom_monthly_counts.png", bbox_inches="tight"
    )
    plt.close()

    print(f"\nAll plots saved to {fig_dir}/")


if __name__ == "__main__":
    main()
