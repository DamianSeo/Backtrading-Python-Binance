import config, csv, os
from binance.client import Client

# Binance Client 설정
client = Client(config.API_KEY, config.API_SECRET)

# 데이터 저장 경로 설정
data_dir = './data'
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# 데이터 수집 함수 정의
def collect_data(symbol, interval, start_date, end_date, filename):
    """
    특정 코인의 히스토리 데이터를 수집하여 CSV 파일로 저장하는 함수

    :param symbol: 수집할 코인 심볼 (예: 'BTCUSDT')
    :param interval: 캔들스틱 데이터의 시간 간격 (예: '5m' or '1d')
    :param start_date: 데이터 수집 시작일 (예: '2022-01-01')
    :param end_date: 데이터 수집 종료일 (예: '2024-08-31')
    :param filename: 저장할 CSV 파일 이름
    """
    # CSV 파일을 열고 데이터를 저장할 준비
    filepath = os.path.join(data_dir, filename)
    with open(filepath, 'w', newline='') as csvfile:
        candlestick_writer = csv.writer(csvfile, delimiter=',')

        # Binance에서 히스토리 캔들스틱 데이터 수집
        if interval == '5m':
            binance_interval = Client.KLINE_INTERVAL_5MINUTE
        elif interval == '1d':
            binance_interval = Client.KLINE_INTERVAL_1DAY
        else:
            print("지원하지 않는 시간 간격입니다. '5m' 또는 '1d'만 지원됩니다.")
            return

        candlesticks = client.get_historical_klines(symbol, binance_interval, start_date, end_date)

        # 수집된 데이터를 CSV 파일에 저장
        for candlestick in candlesticks:
            candlestick[0] = candlestick[0] / 1000  # 타임스탬프를 초 단위로 변경
            candlestick_writer.writerow(candlestick)  # CSV 파일에 쓰기

    print(f"Data collected and saved to {filepath}.")

# 사용자 입력 받기
symbol = input("다운로드할 코인 심볼을 입력하세요 (예: BTCUSDT): ")
start_date = input("데이터 수집 시작일을 입력하세요 (예: 2022-01-01): ")
end_date = input("데이터 수집 종료일을 입력하세요 (예: 2024-08-31): ")
interval = input("수집할 데이터의 간격을 선택하세요 ('5m' 또는 '1d'): ")

# 날짜 형식을 파일 이름 형식으로 변환
start_date_fmt = start_date.replace('-', '')
end_date_fmt = end_date.replace('-', '')

# 파일명 생성 규칙에 따른 설정
interval_suffix = '5m' if interval == '5m' else 'd'
filename = f"{symbol}-{start_date_fmt}-{end_date_fmt}-{interval_suffix}.csv"

# 데이터 수집 실행
collect_data(
    symbol=symbol,
    interval=interval,
    start_date=start_date,
    end_date=end_date,
    filename=filename
)
