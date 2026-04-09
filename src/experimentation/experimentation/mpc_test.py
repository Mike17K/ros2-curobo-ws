import numpy as np
import matplotlib.pyplot as plt


def main():
    # Παράμετροι Προσομοίωσης
    dt = 0.1
    time_steps = 80
    target_h = 10.0
    g = 9.81
    N = 10  # Ορίζοντας πρόβλεψης

    def mpc_control(h, v, wind):
        best_u = g
        min_cost = float("inf")
        # Δοκιμή διαφορετικών τιμών ώσης για εύρεση της βέλτιστης
        for u in np.linspace(0, 20, 30):
            temp_h, temp_v = h, v
            cost = 0
            for _ in range(N):
                accel = u - g - wind
                temp_v += accel * dt
                temp_h += temp_v * dt
                cost += (target_h - temp_h) ** 2 + 0.5 * (u - g) ** 2
            if cost < min_cost:
                min_cost = cost
                best_u = u
        return best_u

    # Δεδομένα για το γράφημα
    history_h, history_u, history_wind = [], [], []
    h, v = 0.0, 0.0

    for t in range(time_steps):
        wind = 3.0 if 30 < t < 60 else 0.0  # Άνεμος μεταξύ 3s και 6s
        u = mpc_control(h, v, wind)

        # Φυσική drone
        accel = u - g - wind
        v += accel * dt
        h += v * dt

        history_h.append(h)
        history_u.append(u)
        history_wind.append(wind)

    # Σχεδίαση με Matplotlib
    plt.figure(figsize=(10, 6))

    # Γράφημα Ύψους
    plt.subplot(2, 1, 1)
    plt.plot(np.arange(time_steps) * dt, history_h, label="Ύψος Drone (m)", lw=2)
    plt.axhline(y=target_h, color="r", linestyle="--", label="Στόχος (10m)")
    plt.ylabel("Ύψος (m)")
    plt.legend()
    plt.grid(True)

    # Γράφημα Ώσης και Ανέμου
    plt.subplot(2, 1, 2)
    plt.step(np.arange(time_steps) * dt, history_u, label="Ώση (Thrust)", color="g")
    plt.plot(
        np.arange(time_steps) * dt,
        history_wind,
        label="Δύναμη Ανέμου",
        color="r",
        alpha=0.5,
    )
    plt.xlabel("Χρόνος (s)")
    plt.ylabel("Δύναμη")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()
