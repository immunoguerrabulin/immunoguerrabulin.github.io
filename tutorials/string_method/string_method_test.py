import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from mpl_toolkits.mplot3d import Axes3D  
from pathlib import Path
try:
    import prettypyplot as pplt  # optional styling

    pplt.use_style()
except Exception:
    prettypyplot = None

# MB potential parameters 
_A = np.array([-200.0, -100.0, -170.0, 15.0])
_b = np.array([0.0, 0.0, 11.0, 0.6])
_x0 = np.array([1.0, 0.0, -0.5, -1.0])
_a = np.array([-1.0, -1.0, -6.5, 0.7])
_c = np.array([-10.0, -10.0, -6.5, 0.7])
_y0 = np.array([0.0, 0.5, 1.5, 1.0])


def muller_brown_potential(x, y):
    """Müller–Brown potential energy surface V(x,y).
    Accepts scalars or numpy arrays.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    V = np.zeros_like(x, dtype=float)
    for i in range(4):
        dx = x - _x0[i]
        dy = y - _y0[i]
        expo = _a[i] * (dx**2) + _b[i] * dx * dy + _c[i] * (dy**2)
        expo = np.clip(expo, -700.0, 700.0)
        V += _A[i] * np.exp(expo)
    return V


def muller_brown_force(xy):
    """Force = -dV for the MB potential (analytic gradient)."""
    x = float(xy[0])
    y = float(xy[1])
    fx = 0.0
    fy = 0.0
    for i in range(4):
        dx = x - float(_x0[i])
        dy = y - float(_y0[i])
        expo = float(_a[i]) * (dx**2) + float(_b[i]) * dx * dy + float(_c[i]) * (dy**2)
        expo = float(np.clip(expo, -700.0, 700.0))
        common = float(_A[i]) * float(np.exp(expo))
        dfdx = 2.0 * float(_a[i]) * dx + float(_b[i]) * dy
        dfdy = float(_b[i]) * dx + 2.0 * float(_c[i]) * dy
        fx += -common * dfdx
        fy += -common * dfdy
    return np.array([fx, fy], dtype=float)


def overdamped_langevin_step(x, *, dt, kBT, gamma, rng, bias_center=None, kappa=0.0):
    """Overdamped Langevin / Brownian dynamics step in 2D.
    x_{t+dt} = x_t + (F/gamma) dt + sqrt(2 kBT dt / gamma) * N(0, I)
    """
    x = np.asarray(x, dtype=float)
    force = muller_brown_force(x)
    if bias_center is not None and kappa != 0.0:
        force = force - float(kappa) * (x - np.asarray(bias_center, dtype=float))
    noise = float(np.sqrt(2.0 * kBT * dt / gamma)) * rng.normal(size=2)
    return x + (force / gamma) * dt + noise


def estimate_mean_force(center, *, dt, kBT, gamma, kappa, n_equil, n_samples, stride, rng):
    """Estimate mean force at `center` from restrained sampling.
    Uses a harmonic restraint U_bias = (kappa/2)*||x-center||^2 and the umbrella
    integration identity:
        mean_force(center) = -dF(center) = kappa * (center - <x>_bias)
    where <x>_bias is the average position under the biased ensemble.
    """
    center = np.asarray(center, dtype=float)
    x = center.copy()
    for _ in range(int(n_equil)):
        x = overdamped_langevin_step(x, dt=dt, kBT=kBT, gamma=gamma, rng=rng, bias_center=center, kappa=kappa)

    count = 0
    sum_pos = np.zeros(2, dtype=float)
    for step in range(int(n_samples)):
        x = overdamped_langevin_step(x, dt=dt, kBT=kBT, gamma=gamma, rng=rng, bias_center=center, kappa=kappa)
        if step % int(stride) == 0:
            sum_pos += x
            count += 1
    mean_pos = sum_pos / max(count, 1)
    mean_force = float(kappa) * (mean_pos - center)
    return mean_force, mean_pos


def estimate_mean_force_replicas(center, *, n_replicas, dt, kBT, gamma, kappa, n_equil, n_samples, stride, rng):
    forces = np.zeros((int(n_replicas), 2), dtype=float)
    means = np.zeros((int(n_replicas), 2), dtype=float)
    for r in range(int(n_replicas)):
        f, m = estimate_mean_force(
            center,
            dt=dt,
            kBT=kBT,
            gamma=gamma,
            kappa=kappa,
            n_equil=n_equil,
            n_samples=n_samples,
            stride=stride,
            rng=rng,
        )
        forces[r] = f
        means[r] = m
    return forces.mean(axis=0), means.mean(axis=0)


def initialize_string(start, end, n_images):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    t = np.linspace(0.0, 1.0, int(n_images))
    return (1.0 - t)[:, None] * start + t[:, None] * end


def reparameterize(points):
    """Redistribute points uniformly by arc length (linear interpolation)."""
    points = np.asarray(points, dtype=float)
    d = np.linalg.norm(np.diff(points, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(d)])
    if not np.isfinite(s[-1]) or s[-1] == 0.0:
        return points.copy()
    s = s / s[-1]

    t = np.linspace(0.0, 1.0, len(points))
    x_new = np.interp(t, s, points[:, 0])
    y_new = np.interp(t, s, points[:, 1])
    return np.column_stack([x_new, y_new])


def unit_tangents(images):
    images = np.asarray(images, dtype=float)
    tangents = np.zeros_like(images)
    n = len(images)
    for i in range(n):
        if i == 0:
            t = images[1] - images[0]
        elif i == n - 1:
            t = images[-1] - images[-2]
        else:
            t = images[i + 1] - images[i - 1]
        norm = float(np.linalg.norm(t))
        if norm == 0.0 or not np.isfinite(norm):
            tangents[i] = np.array([1.0, 0.0], dtype=float)
        else:
            tangents[i] = t / norm
    return tangents


def project_perpendicular(vec, tangent):
    tangent = np.asarray(tangent, dtype=float)
    vec = np.asarray(vec, dtype=float)
    return vec - float(np.dot(vec, tangent)) * tangent


def mean_force_string_method(
    images,
    *,
    n_iters,
    dtau,
    kBT,
    gamma,
    dt,
    kappa,
    n_replicas,
    n_equil,
    n_samples,
    stride,
    max_step,
    fix_start=True,
    fix_end=True,
    rng,
):
    """Mean-force string method (toy implementation).

    For each image, estimate mean force from restrained sampling, project it
    perpendicular to the string tangent, and update images. Reparameterize after
    each iteration.
    """
    images = np.asarray(images, dtype=float).copy()
    history = [images.copy()]
    n_images = len(images)

    for _ in range(int(n_iters)):
        tangents = unit_tangents(images)
        updated = images.copy()

        for i in range(n_images):
            if (i == 0 and fix_start) or (i == n_images - 1 and fix_end):
                continue

            mean_f, _ = estimate_mean_force_replicas(
                images[i],
                n_replicas=n_replicas,
                dt=dt,
                kBT=kBT,
                gamma=gamma,
                kappa=kappa,
                n_equil=n_equil,
                n_samples=n_samples,
                stride=stride,
                rng=rng,
            )
            mean_f_perp = project_perpendicular(mean_f, tangents[i])
            delta = float(dtau) * mean_f_perp
            step_norm = float(np.linalg.norm(delta))
            if max_step is not None and step_norm > float(max_step):
                delta = delta * (float(max_step) / step_norm)
            updated[i] = images[i] + delta

        if fix_start:
            updated[0] = images[0]
        if fix_end:
            updated[-1] = images[-1]

        updated = reparameterize(updated)
        if fix_start:
            updated[0] = images[0]
        if fix_end:
            updated[-1] = images[-1]

        images = updated
        history.append(images.copy())

    return images, history


def plot_muller_brown_contour(X, Y, Z, *, out_path):
    fig, ax = plt.subplots(figsize=(7, 5))
    cs = ax.contour(X, Y, Z, levels=200, cmap="coolwarm", vmax=20)
    fig.colorbar(cs, ax=ax, label="Energy (arb. units)")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Müller–Brown potential (contours)")
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_muller_brown_surface(X, Y, Z, *, out_path):
    # Downsample for speed/size.
    Xs = X[::5, ::5]
    Ys = Y[::5, ::5]
    Zs = Z[::5, ::5]

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(Xs, Ys, Zs, cmap="viridis", linewidth=0.0, antialiased=True)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("Energy (arb. units)")
    ax.set_title("Müller–Brown potential (surface)")
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def animate_trajectory(X, Y, Z, traj, *, out_path, frame_stride=10, fps=10):
    traj = np.asarray(traj, dtype=float)
    n_steps = len(traj) - 1

    fig, ax = plt.subplots(figsize=(7, 5))
    cs = ax.contour(X, Y, Z, levels=200, cmap="coolwarm", vmax=20)
    fig.colorbar(cs, ax=ax, label="Energy (arb. units)")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Overdamped Langevin trajectory")

    (path_line,) = ax.plot([], [], "-", color="black", linewidth=1.0)
    (point,) = ax.plot([], [], "o", color="red", markersize=4)

    ax.set_xlim(float(X.min()), float(X.max()))
    ax.set_ylim(float(Y.min()), float(Y.max()))

    def update(frame):
        idx = min(int(frame) * int(frame_stride), n_steps)
        path_line.set_data(traj[: idx + 1, 0], traj[: idx + 1, 1])
        point.set_data([traj[idx, 0]], [traj[idx, 1]])
        ax.set_title(f"Overdamped Langevin trajectory (step {idx}/{n_steps})")
        return path_line, point

    n_frames = int(np.ceil((n_steps + 1) / int(frame_stride)))
    ani = FuncAnimation(fig, update, frames=n_frames, interval=1000 / fps, blit=False)
    ani.save(out_path, writer=PillowWriter(fps=fps))
    plt.close(fig)


def animate_string_evolution(X, Y, Z, history, *, start, end, out_path, fps=6):
    history = [np.asarray(h, dtype=float) for h in history]

    fig, ax = plt.subplots(figsize=(7, 5))
    cs = ax.contour(X, Y, Z, levels=200, cmap="coolwarm", vmax=20)
    fig.colorbar(cs, ax=ax, label="Energy (arb. units)")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_xlim(float(X.min()), float(X.max()))
    ax.set_ylim(float(Y.min()), float(Y.max()))

    (line,) = ax.plot([], [], "-o", color="red", markersize=3.5, linewidth=1.0)
    ax.scatter([start[0]], [start[1]], color="black", marker="x", s=40, zorder=5, label="start (fixed)")
    ax.scatter([end[0]], [end[1]], color="black", marker="x", s=40, zorder=5, label="end (fixed)")
    ax.legend(
        frameon=True,
        loc="upper right",
        facecolor="white",
        framealpha=0.85,
        edgecolor="0.7",
    )

    def update(frame):
        images = history[int(frame)]
        line.set_data(images[:, 0], images[:, 1])
        ax.set_title(f"Mean-force string method (iteration {int(frame)})")
        return (line,)

    ani = FuncAnimation(fig, update, frames=len(history), interval=1000 / fps, blit=False)
    ani.save(out_path, writer=PillowWriter(fps=fps))
    plt.close(fig)


def compute_pmf_trapezoid(images, mean_forces):
    """Compute relative PMF A(s) along a string using trapezoid integration.

    Given beads phi_i and mean forces F(phi_i) = -dA(phi_i), integrate

        A(s) - A(0) = -int F_parallel(s) ds

    where F_parallel,i = F(phi_i)·t_i and t_i is the unit tangent.
    """
    phi = np.asarray(images, dtype=float)
    F = np.asarray(mean_forces, dtype=float)
    if phi.ndim != 2 or F.shape != phi.shape:
        raise ValueError("images and mean_forces must both be shape (N, d)")

    ds = np.linalg.norm(np.diff(phi, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(ds)])

    # unit tangents
    t = np.zeros_like(phi)
    t[0] = phi[1] - phi[0]
    t[-1] = phi[-1] - phi[-2]
    t[1:-1] = phi[2:] - phi[:-2]
    t_hat = t / (np.linalg.norm(t, axis=1, keepdims=True) + 1e-12)

    F_par = np.sum(F * t_hat, axis=1)
    dA = -0.5 * (F_par[:-1] + F_par[1:]) * ds
    A = np.concatenate([[0.0], np.cumsum(dA)])
    return s, A


def plot_pmf_along_string(s, A, *, out_path):
    s = np.asarray(s, dtype=float)
    A = np.asarray(A, dtype=float)
    A_rel = A - float(np.nanmin(A))

    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot(s, A_rel, marker="o", markersize=3.5, linewidth=1.2, color="black")
    ax.set_xlabel("Arc length, s")
    ax.set_ylabel("PMF, A(s) (arb. units)")
    ax.set_title("PMF along the converged string (trapezoid rule)")
    ax.grid(True, alpha=0.25)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent

    # Reproducibility
    rng = np.random.default_rng(0)

    # Potential grid (reused across plots/animations)
    x_grid = np.linspace(-1.5, 1.0, 500)
    y_grid = np.linspace(-0.5, 1.75, 700)
    X, Y = np.meshgrid(x_grid, y_grid)
    Z = muller_brown_potential(X, Y)

    # 1) "Just the MB" plots
    plot_muller_brown_contour(X, Y, Z, out_path=out_dir / "muller_brown_contour.png")
    plot_muller_brown_surface(X, Y, Z, out_path=out_dir / "muller_brown_surface.png")

    # 2) Unrestrained 1000-step trajectory from one basin (GIF)
    kBT = 10.0
    gamma = 100.0
    dt = 5e-4
    n_steps = 1000

    # Basin A minimum (classic MB parameterization)
    start_basin = np.array([-0.558, 1.442], dtype=float)
    traj = [start_basin.copy()]
    x = start_basin.copy()
    for _ in range(n_steps):
        x = overdamped_langevin_step(x, dt=dt, kBT=kBT, gamma=gamma, rng=rng)
        traj.append(x.copy())
    animate_trajectory(X, Y, Z, traj, out_path=out_dir / "langevin_trajectory_1000_steps.gif", frame_stride=10, fps=12)

    # 3) Mean-force string method (MFSM) + GIF over iterations
    # Endpoints: two MB minima (A -> B)
    start = np.array([-0.558, 1.442], dtype=float)
    end = np.array([0.623, 0.028], dtype=float)

    n_images = 21
    images0 = initialize_string(start, end, n_images)

    # MFSM hyperparameters (toy, but now follows the mean-force update structure)
    # Note: dtau and the sampling settings below strongly affect stability.
    dtau = 0.01  # string evolution step
    kappa = 200.0  # restraint strength per image
    n_iters = 100

    n_replicas = 4
    # Slightly longer restrained sampling per image (reduces noise in mean force estimates).
    n_equil = 150
    n_samples = 300
    stride = 2
    max_step = 0.10  # cap per-iteration bead displacement

    images_final, history = mean_force_string_method(
        images0,
        n_iters=n_iters,
        dtau=dtau,
        kBT=kBT,
        gamma=gamma,
        dt=dt,
        kappa=kappa,
        n_replicas=n_replicas,
        n_equil=n_equil,
        n_samples=n_samples,
        stride=stride,
        max_step=max_step,
        fix_start=True,  # restrain/hold the first bead (requested)
        fix_end=True,
        rng=rng,
    )

    # Save final string overlay
    fig, ax = plt.subplots(figsize=(7, 5))
    cs = ax.contour(X, Y, Z, levels=200, cmap="coolwarm", vmax=20)
    fig.colorbar(cs, ax=ax, label="Energy (arb. units)")
    ax.plot(images0[:, 0], images0[:, 1], "--", color="0.4", linewidth=1.0, label="initial")
    ax.plot(
        images_final[:, 0],
        images_final[:, 1],
        "-o",
        color="red",
        markersize=3.5,
        linewidth=1.0,
        label="final (MFSM, reparameterized)",
    )
    ax.scatter([start[0], end[0]], [start[1], end[1]], color="black", marker="x", s=40, zorder=5)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Mean-force string method on Müller–Brown potential (toy)")
    ax.legend(
        frameon=True,
        facecolor="white",
        framealpha=0.85,
        edgecolor="0.7",
    )
    out_path = out_dir / "string_method_path.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    animate_string_evolution(
        X,
        Y,
        Z,
        history,
        start=start,
        end=end,
        out_path=out_dir / "string_method_path.gif",
        fps=6,
    )

    # 4) PMF along the final string via trapezoid integration of tangential mean force
    mean_forces_final = np.zeros_like(images_final)
    for i in range(len(images_final)):
        mf, _ = estimate_mean_force_replicas(
            images_final[i],
            n_replicas=n_replicas,
            dt=dt,
            kBT=kBT,
            gamma=gamma,
            kappa=kappa,
            n_equil=n_equil,
            n_samples=n_samples,
            stride=stride,
            rng=rng,
        )
        mean_forces_final[i] = mf

    s, A = compute_pmf_trapezoid(images_final, mean_forces_final)
    plot_pmf_along_string(s, A, out_path=out_dir / "pmf_along_string.png")

    print(f"Saved: {out_dir / 'muller_brown_contour.png'}")
    print(f"Saved: {out_dir / 'muller_brown_surface.png'}")
    print(f"Saved: {out_dir / 'langevin_trajectory_1000_steps.gif'}")
    print(f"Saved: {out_dir / 'string_method_path.png'}")
    print(f"Saved: {out_dir / 'string_method_path.gif'}")
    print(f"Saved: {out_dir / 'pmf_along_string.png'}")
