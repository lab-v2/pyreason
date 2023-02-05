import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def main():
    sns.set()
    smooth = False
    # data_path_jit = f'/home/dyuman/Documents/Mancalog/profiling/profile_jit.csv'
    # data_path_old = f'/home/dyuman/Documents/Mancalog/profiling/profile_old.csv'
    # data_path_oldest = f'/home/dyuman/Documents/Mancalog/profiling/profile_oldest.csv'
    # data = f'/home/dyuman/Downloads/memory.csv'

    x_axis_title = 'Number of Nodes (density=0.000384)'
    y_axis_title = 'Runtime'
    title = 'Number of Nodes vs Runtime'

    # headers = ['Timesteps', 'Memory', 'Memory Old']
    # df_jit = pd.read_csv(data_path_jit, names=headers, header=None)
    # df_old = pd.read_csv(data_path_old, names=headers, header=None)
    # df_oldest = pd.read_csv(data_path_oldest, names=headers, header=None)
    # df = pd.read_csv(data, names=headers, header=None)
    # x_jit = df_jit['Timesteps']
    # y_jit = df_jit['Time']
    # x_old = df_old['Timesteps']
    # y_old = df_old['Time']
    # x_oldest = df_oldest['Timesteps']
    # y_oldest = df_oldest['Time']
    # x = df['Timesteps']
    # y1 = df['Memory']
    # y2 = df['Memory Old']

    x = [1000, 2000, 5000, 10000]
    y2 = [56.40, 56.50, 57.24, 59.44] 
    y5 = [56.46, 56.27, 57.78, 60.34] 
    y15 = [56.76, 56.90, 58.87, 64.88] 
    
    # if smooth:
    #     y_jit = pd.Series(y_jit).rolling(15, min_periods=1).mean()
    #     y_old = pd.Series(y_old).rolling(15, min_periods=1).mean()
    #     y_oldest = pd.Series(y_oldest).rolling(15, min_periods=1).mean()

    # sns.relplot(data=df, x =x_axis_title, y=y_axis_title, kind = 'line', hue = 'type', palette = ['red', 'blue'])
    # ax = sns.relplot(data=df,  kind = 'line', ci=0)
    # plt.plot(x_jit, y_jit, label='accelerated with numba for CPU')
    # plt.plot(x_old, y_old, label='first optimized version')
    # plt.plot(x_oldest, y_oldest, label='original version')
    plt.plot(x, y2, linestyle='dotted', marker='^', label='2 Timesteps')
    plt.plot(x, y5, linestyle='dotted', marker='s', label='5 Timesteps')
    plt.plot(x, y15, linestyle='dotted', marker='o', label='15 Timesteps')
    plt.legend()
    plt.title(title, fontsize=20)
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
        plt.savefig(f'timesteps_vs_memory.png')


if __name__ == '__main__':
    main()