"""
Load the only file in /home/eiraola/data/data_tritium/03.tep_short_pulse/model
and plot the column 'XINT(11)'
"""

import os
import matplotlib.pyplot as plt
import pandas as pd
from numpy import polyval


def main():
    # Load
    n_plot = 100
    src_dir = 'model'
    assert os.path.exists(src_dir)
    filepaths = os.listdir(src_dir)
    assert len(filepaths) == 1
    filepath = os.path.join(src_dir, filepaths[0])
    assert os.path.exists(filepath)
    df = pd.read_csv(filepath, index_col=0)
    # Plot
    plt.plot(df['XINT(11)'].iloc[:n_plot], label='smoothed')

    # Use polynomial to alter the data
    poly_terms = [-0.0000037582288, 0.0017814484381, -0.1024837046314,
                  1.3035245331334, 1.840910138786]
    """poly_terms = [  # This no
        0.0000000222186,
        -0.0000040682179,
        0.0002985720785,
        -0.0112186660135,
        0.229809112366,
        -2.542260690836,
        13.811173950756,
        -26.244859588686,
    ]
    poly_terms = [-0.00000001313, 0.0000022970661, -0.0001616507845,
                  0.0059040250737, -0.1191137716452, 1.2773114573221,
                  -6.4434445274026,12.3748419185181]"""
    poly_terms = [-0.0000000230741, 0.0000039445528, -0.0002567345084,
                    0.0078038466414, -0.1060447525635, 0.4382671046341,
                    0.1668527493497, 12.3641110645933]
    poly_terms = [-0.0000000149249, 0.0000026923433, -0.0001872770445,
                    0.0062135430706, -0.0965664456686, 0.540829135253,
                    0.0080238383292, 2.9932651820113]
    poly_terms = [0.0000000023502, -0.0000004566543, 0.0000356379974,
                  -0.0014044390015, 0.0280452773052, -0.2262094658096,
                  -0.00320038334, 0.0028148161666]


    x = df.index[:50] / 60
    y = polyval(poly_terms, x)
    # Populate y 10 times up to a 500 array
    y = pd.Series(y)
    y = pd.concat([y] * 10)
    y = y[:len(df)] / 30
    mod_df = df['XINT(11)'] + y.values
    plt.plot(mod_df.iloc[:n_plot], label='poly')

    # Load actual one
    filename = ('/home/eiraola/data/data_tritium/03.tep_short_pulse/train-dev/'
                'plant_short_idv0_0000.csv')
    df_real = pd.read_csv(filename, index_col=0)
    plt.plot(df_real['XINT(11)'].iloc[:n_plot], label='real')
    plt.legend()
    plt.show()


if __name__ == '__main__':
    main()
