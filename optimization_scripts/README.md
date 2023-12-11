## Optimization Scripts
These optimization scripts were written to be instrument-specific, so they require individual implementation.
When correctly implemented, they basically give the user control over instrument parameter optimization, with the option to test specific configurations or run a global optimization subject to some constraints. 
Output for each run is automatically calculated and a FoM is determined, which is then written to an output file along with the input parameters.

This code was written specifically to minimize the discrepancy ratio of the McStas simulation of the HFIR CG-2 beamline
