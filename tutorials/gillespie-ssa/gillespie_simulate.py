import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
try:
    import prettypyplot as pplt # optional styling
    pplt.use_style()
except Exception:
    prettypyplot = None




def gillespie_from_Q(Q: np.ndarray,
                     n_steps: int = 10_000,
                     warmup: int = 1_000):
    """Simulate from a transition-rate matrix Q.
    Q: (N,N) array where Q[i,j] >= 0 for i!=j, and Q[i,i] = -sum_{j!=i} Q[i,j].
    Returns (flux, net_steps, observed_time) where "net_steps" is net forward
    minus backward moves assuming an ordering of states 0..N-1 and forward = +1.
    """
    Q = np.asarray(Q, dtype=float)
    if Q.ndim != 2 or Q.shape[0] != Q.shape[1]:
        raise ValueError("Q must be a square matrix")

    N = Q.shape[0]

    state = 0
    net = 0
    t_obs = 0.0
    t_total = 0.0
    traj = [(t_total, state)]
    for step in range(n_steps):
        a0 = -Q[state, state]
        if a0 <= 0.0:
            break

        dt = np.random.exponential(1.0 / a0)
        t_total += dt
        # probabilities for jumping to each j != state
        probs = Q[state].copy()
        probs[state] = 0.0
        probs = probs / a0

        # draw next state
        r = np.random.random()
        cum = 0.0
        next_state = state
        for j in range(N):
            cum += probs[j]
            if r < cum:
                next_state = j
                break
        # consider forward as incrementing index by +1 (mod N)
        forward_event = ((next_state - state) % N) == 1
        state = next_state
        if step >= warmup:
            net += 1 if forward_event else -1
            t_obs += dt
            traj.append((t_total, state))

    flux = net / (t_obs * N) if t_obs > 0 else np.nan
    return flux, net, t_obs, traj

if __name__ == "__main__":
    # Example: three-state chain A <-> B <-> C using kf/kb
    kf = np.array([10.0, 10.0, 20.0])  # forward rates (s^-1)
    kb = np.array([2.0, 5.0, 20.0])    # backward rates (s^-1)
    # Build Q matrix for the same three-state chain 
    N = 3
    Q = np.zeros((N, N), dtype=float)
    for i in range(N):
        Q[i, (i + 1) % N] = kf[i]
        Q[i, (i - 1) % N] = kb[i]
    for i in range(N):
        Q[i, i] = -np.sum(Q[i])

    flux_Q, net_Q, t_obs_Q, traj = gillespie_from_Q(Q, n_steps=100, warmup=0)
    print(f"(Q)    flux={flux_Q:.6g} (net={net_Q}, t_obs={t_obs_Q:.4g} s)")
    times, states = zip(*traj)
    plt.step(times, states, where='post', marker='.', linestyle='-')
    plt.xlabel("Time (s)")
    plt.ylabel("State")
    plt.title("Gillespie  Trajectory")
    plt.savefig("gillespie_trajectory.png")
    #Longer Simulation
    flux_Q, net_Q, t_obs_Q, traj_long = gillespie_from_Q(Q, n_steps=100000, warmup=0)

    # Average residence time in each state should be 1/(kf + kb)
    # Compute empirical residence times from the returned trajectory (list of (t, state)).
    res_times = defaultdict(list) # each state maps to list of residence times
    if len(traj_long) >= 2:
        for (t0, s0), (t1, s1) in zip(traj_long[:-1], traj_long[1:]):
            res_times[s0].append(t1 - t0)
    print('\nResidence time (empirical vs theoretical):')
    for i in range(N):
        emp = float('nan')
        if len(res_times[i]) > 0:
            emp = np.mean(res_times[i])
        theo = 1.0 / (-Q[i, i]) if -Q[i, i] > 0 else float('nan')
        print(f" state {i}: emp={emp:.6g} s, theo={theo:.6g} s")
    