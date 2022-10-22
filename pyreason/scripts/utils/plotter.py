import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def main():
    sns.set()
    smooth = False
    data_path_jit = f'/home/dyuman/Documents/Mancalog/profiling/profile_jit.csv'
    data_path_old = f'/home/dyuman/Documents/Mancalog/profiling/profile_old.csv'
    data_path_oldest = f'/home/dyuman/Documents/Mancalog/profiling/profile_oldest.csv'

    x_axis_title = 'Timesteps'
    y_axis_title = 'Run time (seconds)'
    title = 'Run time vs Timesteps'

    headers = ['Timesteps', 'Time']
    df_jit = pd.read_csv(data_path_jit, names=headers, header=None)
    df_old = pd.read_csv(data_path_old, names=headers, header=None)
    df_oldest = pd.read_csv(data_path_oldest, names=headers, header=None)
    x_jit = df_jit['Timesteps']
    y_jit = df_jit['Time']
    x_old = df_old['Timesteps']
    y_old = df_old['Time']
    x_oldest = df_oldest['Timesteps']
    y_oldest = df_oldest['Time']
    
    if smooth:
        y_jit = pd.Series(y_jit).rolling(15, min_periods=1).mean()
        y_old = pd.Series(y_old).rolling(15, min_periods=1).mean()
        y_oldest = pd.Series(y_oldest).rolling(15, min_periods=1).mean()

    # sns.relplot(data=df, x =x_axis_title, y=y_axis_title, kind = 'line', hue = 'type', palette = ['red', 'blue'])
    # ax = sns.relplot(data=df,  kind = 'line', ci=0)
    plt.plot(x_jit, y_jit, label='accelerated with numba for CPU')
    plt.plot(x_old, y_old, label='first optimized version')
    plt.plot(x_oldest, y_oldest, label='original version')
    plt.legend()
    plt.title('Run time vs Timesteps', fontsize=20)
    plt.xlabel(x_axis_title, fontsize=13)
    plt.ylabel(y_axis_title, fontsize=13)

    # ax = sns.lineplot(x=x, y=y, ci=95)
    # ax = sns.lineplot(x=x_jit, y=y_jit, label='')
    # ax = sns.lineplot(x=x, y=y, label='')
    # ax = sns.lineplot(x=x, y=y, label='')


    # ax.axes.set_title(title, fontsize=18)
    # ax.set_xlabel(x_axis_title, fontsize=13)
    # ax.set_ylabel(y_axis_title, fontsize=13)
    # plt.show()
    if smooth:
        plt.savefig(f'timesteps_vs_time_smooth.png')
    else:
        plt.savefig(f'timesteps_vs_time.png')


if __name__ == '__main__':
    main()