# AdaptiveAndParallelMismatchAttack
Some basic Python scripts used to generate Figure 2 and 3 in the preprint of the paper "The Perils of Limited Key Reuse: Adaptive and Parallel Mismatch Attacks with Post-processing Against Kyber", available on ePrint as [ePrint number to be added].

To generate Figure 2 (including some subfigures not included in the paper), simply run the Python script QueryPerformancePlot.py.

To generate the different subfigures in Figure 3, simply run the Python script QueryComplexityTradeoff.py. Set kyberVersion to KYBER512, KYBER768 or KYBER1024 depending on which version of Kyber you want to generate the subfigure for.

The script QueryComplexityTradeoff.py uses pre-computed values for the estimated cost of solving the underlying LWE problem of the different Kyber versions, as a function of the remaining number of unknown coefficients of the secret key. This makes the computation significantly faster.

To compute these numbers yourself, use the function getSecurityLevels(). This function in turn uses the Lattice Estimator (https://github.com/malb/lattice-estimator) to compute these numbers. The version of the estimator used for the pre-computed numbers is included in this repo. To run it you need to have Sage installed. 
