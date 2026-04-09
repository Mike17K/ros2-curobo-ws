import numpy as np
import matplotlib.pyplot as plt


def pendulum_dynamics(x, u, wind=0.0, noise=0.0):
    """Μη γραμμική δυναμική με άνεμο και θόρυβο"""
    g, L, m, dt = 9.81, 1.0, 1.0, 0.02
    theta, omega = x[0], x[1]

    # Ο άνεμος προσθέτει μια συνεχή ροπή, ο θόρυβος είναι τυχαίος
    total_u = u + wind + np.random.normal(0, noise)

    new_omega = omega + (-(g / L) * np.sin(theta) + total_u / (m * L**2)) * dt
    new_theta = theta + new_omega * dt
    return np.array([new_theta, new_omega])


def get_linearized_dynamics(x, u):
    """Jacobians για το iLQR"""
    g, L, dt = 9.81, 1.0, 0.02
    A = np.array([[1, dt], [-(g / L) * np.cos(x[0]) * dt, 1]])
    B = np.array([[0], [dt / (1.0 * L**2)]])
    return A, B


def run_ilqr():
    N, max_iters = 1500, 15
    x_target = np.array([np.pi, 0])
    x_seq = np.zeros((N + 1, 2))
    u_seq = np.zeros(N)

    Q, R, Qf = np.diag([200, 10]), np.array([[0.1]]), np.diag([1000, 100])

    for _ in range(max_iters):
        for t in range(N):
            x_seq[t + 1] = pendulum_dynamics(x_seq[t], u_seq[t])

        k_seq, K_seq = [], []
        P, p = Qf, Qf @ (x_seq[N] - x_target)

        for t in range(N - 1, -1, -1):
            A, B = get_linearized_dynamics(x_seq[t], u_seq[t])
            Qu, Qx = (R @ [u_seq[t]]) + B.T @ p, (Q @ (x_seq[t] - x_target)) + A.T @ p
            Quu, Qux = R + B.T @ P @ B, B.T @ P @ A

            invQuu = np.linalg.inv(Quu)
            k, K = -invQuu @ Qu, -invQuu @ Qux
            k_seq.insert(0, k)
            K_seq.insert(0, K)

            P = Q + A.T @ P @ A + K.T @ Quu @ K + K.T @ Qux + Qux.T @ K
            p = Qx + K.T @ Quu @ k + K.T @ Qu + Qux.T @ k

        for t in range(N):
            u_seq[t] += 0.5 * k_seq[t] + K_seq[t] @ (
                x_seq[t] - x_seq[t]
            )  # Simplified update

    return x_seq, u_seq, K_seq


def main():
    # Εκτέλεση
    x_ref, u_ref, K_gains = run_ilqr()

    # Προσομοίωση με Ανωμαλίες (Wind & Noise)
    N_sim = 1500
    x_sim = np.zeros((N_sim + 1, 2))
    u_final = []
    wind_force = 1.5  # Σταθερός άνεμος
    noise_lvl = 0.2  # Θόρυβος

    for t in range(N_sim):
        # Υπολογισμός σφάλματος και feedback
        # Χρησιμοποιούμε flatten() για να μετατρέψουμε το (1,1) ή (2,1) σε απλό αριθμό/διάνυσμα
        err = (x_sim[t] - x_ref[t]).reshape(2, 1)
        u_fb = u_ref[t] + (K_gains[t] @ err).flatten()

        u_final.append(u_fb)

        # Dynamics update
        next_state = pendulum_dynamics(x_sim[t], u_fb, wind=wind_force, noise=noise_lvl)
        x_sim[t + 1] = next_state.flatten()  # Διασφάλιση σχήματος (2,)

    # Σχεδίαση Πλούσιου Διαγράμματος
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    time = np.linspace(0, 1500 * 0.02, 1501)

    # Γωνία
    ax1.plot(time, x_ref[:, 0], "k--", label="Ideal Trajectory (iLQR)", alpha=0.5)
    ax1.plot(
        time, x_sim[:, 0], "b", lw=2, label=f"Actual with Wind ({wind_force}Nm) & Noise"
    )
    ax1.axhline(np.pi, color="r", ls=":", label="Target (Upright)")
    ax1.fill_between(
        time,
        x_sim[:, 0] - 0.1,
        x_sim[:, 0] + 0.1,
        color="b",
        alpha=0.1,
        label="Noise Margin",
    )
    ax1.set_ylabel("Angle (rad)", fontsize=12)
    ax1.set_title("iLQR Swing-up under Disturbance", fontsize=14)
    ax1.legend(loc="lower right")
    ax1.grid(True, alpha=0.3)

    # Ροπή
    ax2.step(time[:-1], u_final, "g", label="Control Effort (Torque)")
    ax2.set_ylabel("Torque (Nm)", fontsize=12)
    ax2.set_xlabel("Time (s)", fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.tight_layout()
    plt.show()
