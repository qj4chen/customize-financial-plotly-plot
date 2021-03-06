import os
import pandas as pd
import plotly.graph_objects as go
import tushare as ts
from plotly.subplots import make_subplots

token = '6a721053ea3e70bb52605d6c0972caeda9ff080d3671f69bd8b6b434'
pro = ts.pro_api(token)
df = pro.daily(ts_code='600519.SH', start_date='20000101', end_date='20211027')

print(df.columns)
df.index = df['trade_date']
df.index = pd.to_datetime(df.index)
df.sort_index(inplace=True)

df['color'] = 'red'
df.loc[df['close'] < df['open'], 'color'] = 'green'


def resample_k_lines(data, resample_config=None):
    """
    resample the k-lines by the given freq
    :param data:
    :param resample_config:
    :return:
    """
    if resample_config is None:
        resample_config = {
            'rule': '1W',
        }
    resampled_data = pd.DataFrame()
    resampled_data['open'] = data['open'].resample(**resample_config).first()
    resampled_data['close'] = data['close'].resample(**resample_config).last()
    resampled_data['low'] = data['low'].resample(**resample_config).min()
    resampled_data['high'] = data['high'].resample(**resample_config).max()
    resampled_data['vol'] = data['vol'].resample(**resample_config).sum()
    resampled_data['color'] = 'red'
    resampled_data.loc[resampled_data['close'] < resampled_data['open'], 'color'] = 'green'
    resampled_data = resampled_data[resampled_data['vol'] > 0.0]
    return resampled_data


def find_range_breaks(dataframe, freq=None):
    index = dataframe.index
    start = index[0]
    end = index[-1]
    filled_index = pd.date_range(start=start, end=end, freq=freq)
    return filled_index.difference(index)


data_list = [df] + [resample_k_lines(df, dict(rule=freq)) for freq in ['1W', '1M', '3M', '6M', '1Y']]
text_list = ['日线', '周线', '月线', '3月线', '半年线', '年线']
freq_list = ['1D', '1W', '1M', '3M', '6M', '1Y']

n_cols = 2
fig = make_subplots(rows=2, cols=1,
                    shared_xaxes=True,
                    row_heights=[n_cols, 1],
                    vertical_spacing=0.05,
                    subplot_titles=['K线图', '成交量']
                    )

for text, data in zip(text_list, data_list):
    fig.add_candlestick(
        x=data.index,
        open=data.open,
        high=data.high,
        low=data.low,
        close=data.close,
        increasing=dict(line_color='red'),
        decreasing=dict(line_color='green'),
        visible=False,
        name='k-lines_' + text,
        row=1, col=1)

for text, data in zip(text_list, data_list):
    fig.add_trace(
        go.Bar(x=data.index, y=data.vol, visible=False, marker_color=data['color'], name='Volume_' + text),
        row=2, col=1
    )

fig.update_layout(
    updatemenus=[
        dict(
            type="buttons",
            direction="left",
            active=0,
            x=1.0,
            y=1.1,
            buttons=[
                        dict(label='None',
                             method='update',
                             args=[{"visible": [False for _ in range(len(data_list))]}] * 2
                             )
                    ] +
                    [
                        dict(label=text,
                             method="update",
                             args=[{"visible": [True if _ == idx else False for _ in range(len(data_list))] * 2, },
                                   {'xaxis.rangebreaks': [
                                       dict(values=find_range_breaks(dataframe=data_list[idx],
                                                                     freq=freq_list[idx]))]}
                                   ])
                        for idx, text in enumerate(text_list)
                    ],
        )
    ]
)

fig.update_layout(autosize=True,
                  title=dict(text='贵州茅台K线图', x=0.5),
                  )
# modify the subplot title by fig.layout['annotations']
k = 1
while k < n_cols:
    fig.update_xaxes(rangeslider={'visible': False}, row=k, col=1)
    k += 1
fig.update_xaxes(rangeslider={'visible': True, 'thickness': 0.05}, row=n_cols, col=1)

if not os.path.exists('./docs'):
    os.makedirs('./docs')
fig.write_html('./docs/index.html')
