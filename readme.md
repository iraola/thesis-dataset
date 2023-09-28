# Overall

- sampling time = 36 seconds
- typical scenario length = 240 h with 8 cycles
- The "ignore" keyword in setup.json is used to select variables that will be ignored during `isnan` checks and bugged columns (when several consecutive values in a column have the same value).
- The same goes for "ignore_idvs", which points out that a file should be ignored for testing bugged columns if it represents one of these fault scenarios.
- For detection, we will not use all the XMEAS and we will skip the composition ones (from 23 to 41) due to the heavy computation load for the dynamic cases

# Data checking notes


# Dataset split
- train:        90 NOC cases
- train-dev:    8 NOC cases
- val:          1 NOC case, 50 fault cases/fault  (950 fault cases total)
- test:         1 NOC case, 50 fault cases/fault  (950 fault cases total)
