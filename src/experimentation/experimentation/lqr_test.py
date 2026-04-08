import numpy as np
import scipy.linalg as la
import matplotlib.pyplot as plt


def main():
    # 1. Παράμετροι Συστήματος (Μοντέλο Drone - Κατακόρυφη Κίνηση)
    m = 1.0  # Μάζα σε kg
    g = 9.81  # Επιτάχυνση βαρύτητας (m/s^2)
    dt = 0.02  # Χρονικό βήμα (s)
    t_end = 10.0
    t_eval = np.arange(0, t_end, dt)

    # Σύστημα Χώρου Κατάστασης (State-Space)
    # x = [ύψος, ταχύτητα]^T
    # u = δύναμη (Thrust)
    A = np.array([[0, 1], [0, 0]])
    B = np.array([[0], [1 / m]])

    # 2. Σχεδιασμός LQR
    # Q: Πίνακας κόστους κατάστασης (ύψος, ταχύτητα)
    Q = np.diag([100, 10])
    # R: Πίνακας κόστους ελέγχου (ενέργεια μοτέρ)
    R = np.array([[0.1]])

    # Επίλυση της Αλγεβρικής Εξίσωσης Riccati για εύρεση του βέλτιστου K
    P = la.solve_continuous_are(A, B, Q, R)
    K = la.inv(R) @ B.T @ P

    print("Optimal LQR Gain K:", K.flatten())

    # 3. Προσομοίωση
    x = np.array([0.0, 0.0])  # Αρχική κατάσταση (έδαφος, ακίνητο)
    target_height = 5.0  # Επιθυμητό ύψος (m)

    states = []
    inputs = []

    # Προσθήκη θορύβου και διαταραχών
    np.random.seed(42)  # Για σταθερά αποτελέσματα
    noise_std = 0.05  # Τυπική απόκλιση θορύβου (5cm)
    wind_force = -3.0  # Δύναμη ανέμου (Newtons)
    wind_start, wind_end = 4.0, 5.0  # Χρονικό παράθυρο ριπής

    for t in t_eval:
        # 1. Μέτρηση με θόρυβο (Αυτό που "βλέπει" ο ελεγκτής)
        measured_x = x + np.random.normal(0, noise_std, size=x.shape)

        # 2. Υπολογισμός σφάλματος και σήματος ελέγχου LQR
        error = measured_x - np.array([target_height, 0])
        u = -K @ error + m * g
        u = np.clip(u, 0, 2 * m * g)

        # 3. Εξωτερική διαταραχή (Ριπή ανέμου μεταξύ 4s και 5s)
        current_dist = wind_force if wind_start <= t <= wind_end else 0.0

        # 4. Φυσική συστήματος με τη διαταραχή
        # x_dot = Ax + B(u - mg + wind)
        x_dot = A @ x + B @ (u - m * g + current_dist)
        x = x + x_dot * dt

        states.append(x)
        inputs.append(u)

    states = np.array(states)
    inputs = np.array(inputs)

    # 4. Οπτικοποίηση (Matplotlib)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # Γράφημα Καταστάσεων (States)
    ax1.plot(t_eval, states[:, 0], label="Ύψος (m)", lw=2.5, color="#1f77b4")
    ax1.axhline(target_height, color="red", linestyle="--", label="Στόχος", alpha=0.6)
    ax1.plot(
        t_eval, states[:, 1], label="Ταχύτητα (m/s)", lw=1.5, color="#ff7f0e", alpha=0.8
    )
    ax1.set_ylabel("Κατάσταση (States)")
    ax1.set_title("Προσομοίωση Drone LQR: Μετάβαση σε Ύψος 5m", fontsize=14)
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)

    # Γράφημα Εισόδου (Input / Thrust)
    ax2.plot(t_eval, inputs, label="Thrust (N)", lw=2, color="#2ca02c")
    ax2.axhline(
        m * g, color="black", linestyle=":", label="Hover (Βαρύτητα)", alpha=0.5
    )
    ax2.set_xlabel("Χρόνος (s)")
    ax2.set_ylabel("Ισχύς (Input)")
    ax2.legend(loc="upper right")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()
