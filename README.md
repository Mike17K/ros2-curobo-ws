# RULES
1. Development is done inside Docker Dev Container ( plugin: Dev Containers )
2. Understand all the commands of Makefile as is the main way of interacting with workspace


# Docs
[Workspace Setup First Time](./docs/system_setup.md)


# Notes
Debug CPP Package: 
1. Breakpoints: Άνοιξε το .cpp αρχείο σου και βάλε την κόκκινη τελεία εκεί που θέλεις.
2. Επιλογή: Στην καρτέλα "Run and Debug", επίλεξε το "ROS 2: Debug C++ Node".
3. F5: Ο debugger θα ξεκινήσει, θα τρέξει το binary από το install/ folder και θα σταματήσει στο breakpoint.
4. Variables: Στα αριστερά θα βλέπεις όλα τα C++ objects, τους pointers και τα ROS 2 messages ζωντανά.
