import numpy as np
import scipy.linalg as la
from scipy.signal import place_poles  # Νέα βιβλιοθήκη για Pole Placement
import matplotlib.pyplot as plt


def main():
    # 1. Παράμετροι Συστήματος
    m = 1.0
    g = 9.81
    dt = 0.02
    t_end = 10.0
    t_eval = np.arange(0, t_end, dt)

    # Σύστημα Χώρου Κατάστασης (State-Space)
    A = np.array([[0, 1], [0, 0]])
    B = np.array([[0], [1 / m]])

    # 2. Σχεδιασμός Pole Placement (Αντί για LQR)
    # Επιλέγουμε επιθυμητούς πόλους (Desired Closed-Loop Poles)
    # Για ένα drone, θέλουμε αρνητικούς πραγματικούς πόλους για ευστάθεια.
    # Πιο αρνητικοί πόλοι = Πιο γρήγορη απόκριση αλλά μεγαλύτερη απαίτηση ισχύος.
    desired_poles = np.array([-2.0, -2.5])

    # Υπολογισμός του Gain K ώστε οι ιδιοτιμές του (A - BK) να είναι οι desired_poles
    placement_results = place_poles(A, B, desired_poles)
    K = getattr(placement_results, "gain_matrix")  # placement_results.gain_matrix

    print(f"Desired Poles: {desired_poles}")
    print(f"Calculated Gain K: {K.flatten()}")

    # 3. Προσομοίωση (Ίδια με πριν)
    x = np.array([0.0, 0.0])
    target_height = 5.0

    states = []
    inputs = []

    np.random.seed(42)
    noise_std = 0.05
    wind_force = -3.0
    wind_start, wind_end = 4.0, 5.0

    for t in t_eval:
        measured_x = x + np.random.normal(0, noise_std, size=x.shape)

        # Ο νόμος ελέγχου παραμένει u = -K * error + gravity_compensation
        error = measured_x - np.array([target_height, 0])
        u = -K @ error + m * g
        u = np.clip(u, 0, 2 * m * g)

        current_dist = wind_force if wind_start <= t <= wind_end else 0.0

        x_dot = A @ x + B @ (u - m * g + current_dist)
        x = x + x_dot * dt

        states.append(x)
        inputs.append(u)

    states = np.array(states)
    inputs = np.array(inputs)

    # 4. Οπτικοποίηση
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    ax1.plot(
        t_eval, states[:, 0], label="Ύψος (m)", lw=2.5, color="#d62728"
    )  # Κόκκινο για Pole Placement
    ax1.axhline(target_height, color="black", linestyle="--", label="Στόχος", alpha=0.6)
    ax1.set_ylabel("Κατάσταση (Height)")
    ax1.set_title(
        f"Drone Control via Pole Placement (Poles: {desired_poles})", fontsize=14
    )
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)

    ax2.plot(t_eval, inputs, label="Thrust (N)", lw=2, color="#9467bd")
    ax2.set_xlabel("Χρόνος (s)")
    ax2.set_ylabel("Ισχύς (Input)")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
