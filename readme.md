# Overall

- sampling time = 36 seconds
- typical scenario length = 240 h with 8 cycles
- The "**ignore**" keyword in setup.json is used to select variables that will be ignored during `isnan` checks and bugged columns (when several consecutive values in a column have the same value).
- The same goes for "**ignore_idvs**", which points out that a file should be ignored for testing bugged columns if it represents one of these fault scenarios. It should not be used since ESD cases should be trimmed if they reach ESD to avoid consecutive equal values, but sometimes a few values saturate due to the disturbance pushing the system to its limits. In these cases, `ignore_idvs` can be helpful if the amount of consecutive equal values is unpredictable.
- For detection, we will not use all the XMEAS and we will skip the composition ones (from 23 to 41) due to the heavy computation load for the dynamic cases

# Data checking notes

Variables that need to always be ignored:
- Actuator percentages XMV(5) and XMV(11), the former being the compressor recycle valve opening; and, the latter, the condenser valve opening. These are not used in the current control strategy and should not change
- The same happens to SP(5) and SP(11), the setpoint variables of the previous valves.
- The rest of ignored setpoints, with indices 5, 11, 12, 13, 14, 15, 16, 17, 19, and 20, correspond to secondary controllers whose setpoint is calculated online by one of the other main controllers.
- Regarding internal inventory variables UCLR_A and UCLS_A are gnored because they represent the A component content in liquid the phase of the reactor and the separator, respectively, and that does not happen in the plant because it is a non-condensable gas.
- For the internal flow variables FMOL(1)_A, FMOL(2)_A are ignored since these represent A flows in the D and E streams, which should have no A content. Similarly, FMOL(11)_A, that represents the A content flow in the separator underflow stream, should be always null.

There are some special cases that made it necessary to consider separately in the dynamic case:

- **ESD-triggering disturbances**: IDV 1, 6, 8 (sometimes), and 13 (rare), compared to the steady-state case in which only IDV6 caused ESD. With dynamic operation, the system works in less favorable conditions and disturbances that were not problematic in the steady-state case cause shutdown conditions now.
- **Disturbances causing some equal consecutive values**: IDV 8 and 19.
    - IDV(8) relates to changes in composition in the C stream (which also contains an amount of A). The "bugged" columns in this case are FMOL(3), FMOL(3)_A, XMEAS(1)_clean. FMOL(3) variables correspond to the A feed molar flow, while XMEAS(1) corresponds to the same measurement in volume flow. Therefore, the bugged behavior is justified: the disturbance causes an excess of the component A in the system and the control tends to decrease the feed, sometimes closing the valve completely.
    - IDV(19) activates sticking in the separator, sump, and steam valves. The sticking can fix the valve opening for an undefined number of time steps. Since the steam flow is proportional to the valve opening, it causes several time steps receiving the same product flow measurement, in this case happening mostly to the internal molar flow variable FMOL(13)

Since we checked these cases manually and verified their limited scope of influence, i.e., it is not an error but normal occurrence, we have added disturbances 1, 6, 8, 13, and 19 to the "ignore_idvs" list in the setup file to avoid the warnings described above. 


# Dataset split
- train:        90 NOC cases
- train-dev:    8 NOC cases
- val:          1 NOC case, 50 fault cases/fault  (950 fault cases total)
- test:         1 NOC case, 50 fault cases/fault  (950 fault cases total)
