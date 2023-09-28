# Overall

- sampling time = 36 seconds
- typical scenario length = 25 h
- The "ignore" keyword in setup.json is used to select variables that will be ignored during `isnan` checks and bugged columns (when several consecutive values in a column have the same value).

# Data checking notes

- `test_bugged_cols` checks for many consecutive files as an error (possibly needed to trim data from an ESD case). The accepted value in setup.json is 25. I am deliberately ignoring disturbances 6, 8 and 19 because they produce weird null values mostly in FMOL(3) and FMOL(13) variables.
- `test_cols` test is not passed here due to plant files having XMEAS_clean columns and res files not having them. We ignore this test for the moment.

# Raw data

1. Old residuals Rieth data. NOC instances for train and train-dev. Mix of fault and NO for val/test sets.

# Dataset split

1. Train (55 %): 230.000 instances NOC == 92 files 
2. Train-dev (5 %): 20.000 instances NOC == 8 files 
3. Val (20 %): 95.000 instances == 38 files
4. Test (20 %): 95.000 instances == 38 files
