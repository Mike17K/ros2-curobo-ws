# Troubleshooting

## Docker

- Αν έχεις πρόβλημα με το GUI (π.χ. RViz, Gazebo) μέσα στο Docker, βεβαιώσου ότι έχεις εκτελέσει την εντολή `xhost +local:docker` στο terminal του host (έξω από το docker) για να επιτρέψεις την πρόσβαση στο X server από τα containers.
