- sampling time = 36 seconds
- typical scenario length = 25 h
- max consecutive times. data_checker.py checkes for many consecutive files as an error (possibly needed to trim data from an ESD case). The accepted value in setup.jsonis 26. Would be 25 accounting for composition sensors, but there is some weird case for file "plant_mode1009_IDV19_2891.csv" in which FMOL(13) takes the same value 26 consecutive times.

# Raw data

1. Old residuals Rieth data. NOC instances for train and train-dev. Mix of fault and NO for val/test sets.

# Dataset split

1. Train (55 %): 230.000 instancias NOC == 92 archivos 
2. Train-dev (5 %): 20.000 instancias NOC == 8 archivos 
3. Val (20 %): 95.000 instancias == 38 archivos
4. Test (20 %): 95.000 instancias == 38 archivos
