# Aggregated backtest tables

### Threshold signal | full 2013-2025 | no_cost | avg over 7 real pairs

                 mean_sharpe  median_sharpe  mean_ann_ret  mean_maxdd  mean_trades  mean_turnover
method                                                                                           
kalman_basic           0.374          0.324         0.023      -0.131       64.429          0.044
kalman_momentum        0.015          0.092        -0.001      -0.217      109.286          0.072
rolling_ols            0.382          0.386         0.024      -0.139       56.571          0.039

### Threshold signal | full 2013-2025 | tc_5bps | avg over 7 real pairs

                 mean_sharpe  median_sharpe  mean_ann_ret  mean_maxdd  mean_trades  mean_turnover
method                                                                                           
kalman_basic           0.291          0.268         0.017      -0.137       64.429          0.044
kalman_momentum       -0.126         -0.057        -0.010      -0.258      109.286          0.072
rolling_ols            0.307          0.308         0.019      -0.144       56.571          0.039

### Threshold signal | full 2013-2025 | tc_10bps | avg over 7 real pairs

                 mean_sharpe  median_sharpe  mean_ann_ret  mean_maxdd  mean_trades  mean_turnover
method                                                                                           
kalman_basic           0.209          0.194         0.011      -0.145       64.429          0.044
kalman_momentum       -0.267         -0.206        -0.019      -0.309      109.286          0.072
rolling_ols            0.231          0.245         0.014      -0.152       56.571          0.039

### Threshold signal | OOS 2023-2025 | tc_5bps | avg over 7 real pairs

                 mean_sharpe  median_sharpe  mean_ann_ret  mean_maxdd
method                                                               
kalman_basic           0.108          0.167         0.004      -0.085
kalman_momentum       -0.354         -0.394        -0.019      -0.103
rolling_ols            0.105          0.017         0.005      -0.105

### Proportional sizing | full 2013-2025 | no_cost | avg over 7 real pairs

                 mean_sharpe  mean_ann_ret  mean_total_ret  mean_maxdd
method                                                                
kalman_basic           0.424         0.019           0.270      -0.102
kalman_momentum        0.040         0.001           0.016      -0.159
rolling_ols            0.312         0.014           0.194      -0.111

### Proportional sizing | full 2013-2025 | tc_5bps | avg over 7 real pairs

                 mean_sharpe  mean_ann_ret  mean_total_ret  mean_maxdd
method                                                                
kalman_basic           0.142         0.005           0.070      -0.127
kalman_momentum       -0.367        -0.018          -0.191      -0.259
rolling_ols            0.049         0.002           0.025      -0.137

### Per-pair Sharpe | threshold | full 2013-2025 | tc_5bps

method   kalman_basic  kalman_momentum  rolling_ols
pair                                               
EWA-EWC         0.300           -0.180        0.420
GLD-GDX         0.130            0.030        0.300
GS-MS           0.140           -0.060        0.050
HD-LOW          0.570           -0.330        0.310
KO-PEP          0.270            0.130        0.410
V-MA            0.700            0.080        0.270
XOM-CVX        -0.070           -0.550        0.390

### JUNK pair AAPL-XOM | threshold | full | tc_5bps

              method  sharpe  ann_return  max_drawdown  n_trades
511      rolling_ols  -0.342      -0.079        -0.779        35
529     kalman_basic  -0.374      -0.080        -0.720        51
556  kalman_momentum  -0.465      -0.075        -0.743       106