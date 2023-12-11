# Overall

Data is extracted from `02.complete_dyn_set/original/SS-dyn` and preprocessed to `02.complete_dyn_set/SS-dyn`, so that we can always go back to the original data (this step already performed for `tep-short` branch). Some adjustments need to be done since the start of the pulses is not exactly the same, so we trim every file to start when the first setpoint changes. This is done by `data_prep.py`.

**Parameters:**

- sampling time = 36 seconds
- typical scenario length:
  - SHORT PULSE: 5 h with 8 cycles (30 min/cycle)
  - LONG PULSE: 20 h with 6 cycles (200 min/cycle)
- `n_consecutive` (see next) = 39

Note that a cycle is made up by 30 min, equivalent to 50 timesteps of 36 s (**11 of burn and 39 of dwell**). Some values (especially internal tritium XINT inventories) go to zero during dwell, therefore `n_consecutive` will be close to this number.

**Other considerations:**

- The "**ignore**" keyword in setup.json is used to select variables that will be ignored during `isnan` checks and bugged columns (when several consecutive values in a column have the same value).
- The same goes for "**ignore_idvs**", which points out that a file should be ignored for testing bugged columns if it represents one of these fault scenarios. It should not be used since ESD cases should be trimmed if they reach ESD to avoid consecutive equal values, but sometimes a few values saturate due to the disturbance pushing the system to its limits. In these cases, `ignore_idvs` can be helpful if the amount of consecutive equal values is unpredictable.


# Preprocessing

The only preprocessing done to the data is the **alignment of pulses** between plant and model data to generate residuals, and trimming the end of model data if its plant counterpart did not end the simulation due to an emergency shutdown.

Although we could do further preprocessing trying to center and scale model data with respect to NOC plant data, we prefer not doing so to avoid removing physical meaning when modifying **flow rates and compositions**. We then prefer to do a pure model prediction, though mostly wrong, and then correct it afterwards with historical plant data analysis.


# Features dropped

- Detection: 
  * Sub permeators of the first stage because the model did not had them: XMEAS(4) to XMEAS(9). The only left is XMEAS(3), which contains the sum of the other, since the model only had one permeator but the plant had seven.
  * All XMEAS (also XMEAS_clean) for compositions of HD and HT (not used in the model ultimately): 34, 35, 41, 42, 48, 49, 55, 56, 62, 63, 68, 69, 74, 75. Not all of them are exactly zero but extremely low values due to simulation numerical errors (from 1e-10 to 1e-20).
  * Surge valves XMV(15) to XMV(19), not in the model.
  * Internal variables (XINT): should not be used as knowledge for anomaly detection.
  * Clean variables (XMEAS_clean): should not be used as knowledge for anomaly detection.
  * All SPs except SP(1), that marks the dynamics of the system.


# Features ignored

Variables that need to always be **ignored**:
- Sub permeators of the first stage (see above): XMEAS(4) to XMEAS(9).
- All XMEAS (also XMEAS_clean) for compositions of HD and HT (see above).
- All setpoints (SP) since most of them do not change. Even SP(1), which indeed changes, is zero for residuals since remains constant among model and plant.
- XMV(15) to XMV(18): surge valves are almost always zero.
- XINT(12), XINT(14), and XINT(15) are the undesired permeation flows for broken pipes and only appear in IDVs 11, 12, and 13.

Especial cases (see below):
- XMEAS(60)
- XMV(5)



# Notes on disturbances

- **ESD-triggering disturbances**: IDV 7, 11 (sometimes), 16 (sometimes). Added to "ignore_idvs" list in the setup file.
- **IDV(1)** (pressure valve sticking in S3) causes output composition of impurities, **XMEAS(60)**, to be always almost 100 %
- **IDV(18)** (short ramp permeation through equipment in S1) causes **XMV(5)** to open at 100 % for long periods (to be investigated).


# Dataset split

In total, there are 10 NOC cases and 10 fault cases per disturbance, except for IDV(15) for which there are only 9 cases. Since we have 18 disturbances, the total number of short pulse files is 189.
 
- train:        7 NOC cases
- train-dev:    1 NOC cases
- val:          1 NOC case, 5 fault cases/fault  (90 fault cases total)
- test:         1 NOC case, 5 fault cases/fault  (89 fault cases total), We leave the one IDV(15) missing file to this case, therefore 89 instead of 90 disturbance cases.
