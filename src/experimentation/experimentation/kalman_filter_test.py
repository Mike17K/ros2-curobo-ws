import numpy as np
import matplotlib.pyplot as plt


def main():
    # 1. Αρχικοποίηση Παραμέτρων
    true_temp = 25.0  # Η πραγματική σταθερή θερμοκρασία
    n_samples = 50  # Πόσες μετρήσεις θα πάρουμε
    z = true_temp + np.random.normal(
        0, 2, n_samples
    )  # Μετρήσεις με θόρυβο (±2 βαθμούς)

    # Μεταβλητές Kalman
    x_est = 20.0  # Η αρχική μας πρόβλεψη (έστω 20 βαθμοί)
    p_est = 1.0  # Η αρχική μας αβεβαιότητα (πόσο σίγουροι είμαστε)
    q = 0.1  # Θόρυβος διαδικασίας (πόσο αλλάζει η θερμοκρασία μόνη της)
    r = 2.0  # Θόρυβος μέτρησης (πόσο "παίζει" ο αισθητήρας)

    kalman_results = []

    # 2. Ο Βρόχος του Kalman (The Loop)
    for measurement in z:
        # --- Φάση Πρόβλεψης (Predict) ---
        # x_pred = x_est (υποθέτουμε ότι η θερμοκρασία μένει ίδια)
        p_pred = p_est + q

        # --- Φάση Ενημέρωσης (Update) ---
        # Υπολογισμός Kalman Gain
        k_gain = p_pred / (p_pred + r)

        # Διόρθωση της εκτίμησης με τη νέα μέτρηση
        x_est = x_est + k_gain * (measurement - x_est)

        # Ενημέρωση της αβεβαιότητας
        p_est = (1 - k_gain) * p_pred

        kalman_results.append(x_est)

    # 3. Οπτικοποίηση
    plt.plot(z, "ro", alpha=0.5, label="Μετρήσεις Αισθητήρα (Θόρυβος)")
    plt.plot(kalman_results, "b-", linewidth=2, label="Εκτίμηση Kalman (Φιλτραρισμένο)")
    plt.axhline(true_temp, color="g", linestyle="--", label="Πραγματική Τιμή")
    plt.legend()
    plt.title("Kalman Filter: Θερμοκρασία Δωματίου")
    plt.show()
