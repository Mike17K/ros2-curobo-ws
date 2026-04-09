import numpy as np
import matplotlib.pyplot as plt


def main():
    # 1. Παράμετροι
    dt = 0.005
    T = 3.0
    N = int(T / dt)
    g, L, m = 9.81, 1.0, 1.0

    # Διακριτοποιημένα Dynamics (Linearized around vertical down)
    A = np.array([[1, dt], [(g / L) * dt, 1]])
    B = np.array([[0], [dt / (m * L**2)]])

    # 2. Τροχιά Στόχος (Target Trajectory)
    t_range = np.linspace(0, T, N)
    freq = 1.5
    target_angle = 1.2 * np.sin(2 * np.pi * freq * t_range)
    # Υπολογισμός ταχύτητας στόχου (παράγωγος) για σωστό state vector
    target_vel = 1.2 * (2 * np.pi * freq) * np.cos(2 * np.pi * freq * t_range)
    X_d = np.vstack([target_angle, target_vel])

    # 3. Παράμετροι Κόστους
    Q = np.diag([2000.0, 10.0])
    R = np.array([[0.01]])
    Qf = np.diag([5000.0, 100.0])
    torque_limit = 25.0  # Αυξήθηκε λίγο λόγω της επιθετικής συχνότητας

    # --- TVLQR Backward Pass (Riccati + Adjoint Equation) ---
    K_tvlqr = [None] * N
    v = [None] * N  # Feedforward term

    P = Qf
    s = -Qf @ X_d[:, -1]  # Terminal condition για το affine term

    for i in range(N - 1, -1, -1):
        # Optimal Gain K
        K = np.linalg.inv(R + B.T @ P @ B) @ B.T @ P @ A
        K_tvlqr[i] = K

        # Feedforward Gain v
        # u = -K*x + v
        v_gain = -np.linalg.inv(R + B.T @ P @ B) @ B.T @ s
        v[i] = v_gain

        # Update P and s for next step (moving backwards)
        P = Q + A.T @ P @ (A - B @ K)
        s = A.T @ (s + P @ B @ v_gain) - Q @ X_d[:, i]

    # 4. Προσομοίωση
    x_tv = np.zeros((2, N))
    u_tv_log = []

    for i in range(N - 1):
        # Control Law: u = -K*x + v
        # Σημείωση: Εδώ το x είναι το absolute state
        u_tv = -K_tvlqr[i] @ x_tv[:, i] + v[i]
        u_tv = np.clip(u_tv, -torque_limit, torque_limit)
        u_tv_log.append(u_tv)

        # Dynamics update
        x_tv[:, i + 1] = A @ x_tv[:, i] + B.flatten() * u_tv

    # 5. Οπτικοποίηση
    plt.figure(figsize=(10, 6))
    plt.subplot(2, 1, 1)
    plt.plot(t_range, target_angle, "k--", label="Target", alpha=0.6)
    plt.plot(t_range, x_tv[0, :], "b", label="TVLQR with Feedforward")
    plt.title("Corrected TVLQR Tracking")
    plt.legend()
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.step(t_range[:-1], u_tv_log, "g", label="Torque")
    plt.axhline(torque_limit, color="r", linestyle="--")
    plt.ylabel("Torque (Nm)")
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    main()
