import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import tushare as ts

token = '6a721053ea3e70bb52605d6c0972caeda9ff080d3671f69bd8b6b434'
pro = ts.pro_api(token)
df = pro.daily(ts_code='600519.SH', start_date='20000101', end_date='20211027')

print(df.columns)
df.index = df['trade_date']
df.index = pd.to_datetime(df.index)
df.sort_index(inplace=True)

# calculate k lines using 'open', 'high', 'low', 'close', 'vol'
pio.templates.default = 'plotly_dark'


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
    return resampled_data


data_list = [df] + [resample_k_lines(df, dict(rule=freq)) for freq in ['1W', '1M', '3M', '6M', '1Y']]
text_list = ['原始', '周线', '月线', '3月线', '半年线', '年线']


fig = go.Figure(data=[
    go.Candlestick(x=data.index.strftime("%Y/%m/%d"),
                   open=data.open,
                   high=data.high,
                   low=data.low,
                   close=data.close,
                   increasing=dict(line_color='red'),
                   decreasing=dict(line_color='green'),
                   visible=False
                   ) for data in data_list
])

fig.update_layout(
    updatemenus=[
        dict(
            type="buttons",
            direction="right",
            active=0,
            x=0.57,
            y=1.2,
            buttons=[
                        dict(label='None',
                             method='update',
                             args=[{"visible": [False for _ in range(len(data_list))]}]
                             )
                    ] +
                    [
                        dict(label=text,
                             method="update",
                             args=[{"visible": [True if _ == idx else False for _ in range(len(data_list))]},
                                   {"title": "K线图",
                                    "annotations": []}]) for idx, text in enumerate(text_list)
                    ],
        )
    ]
)

# todo: add subplots

fig.write_html('sample_plot.html')
