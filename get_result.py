import backtest_binance_auto_bot as backtest, csv, os
import matplotlib.pyplot as plt
from tkinter import filedialog, Tk

# 백테스트 초기 설정
commission_val = 0.04  # 0.04% taker fees binance usdt futures
portofolio = 10000.0  # starting amount of money
stake_val = 1
quantity = 0.10  # percentage to buy based on the current portofolio amount
start = '2022-01-01'
end = '2024-08-31'
strategies = ['SMA', 'RSI']
periodRange = range(10, 31)
plot = False

# 결과를 저장할 딕셔너리 초기화
results = {strategy: {'periods': [], 'final_values': [], 'profits': []} for strategy in strategies}

# result 디렉토리가 없으면 생성
result_dir = './result'
if not os.path.exists(result_dir):
    os.makedirs(result_dir)

# 사용자로부터 백테스팅할 파일 복수 선택
Tk().withdraw()  # Tkinter 창 숨기기
file_paths = filedialog.askopenfilenames(initialdir='./data', title='백테스팅할 CSV 파일을 선택하세요')

# 파일이 선택되지 않은 경우 처리
if not file_paths:
    print("파일이 선택되지 않았습니다. 프로그램을 종료합니다.")
    exit()

# 선택된 각 파일에 대해 백테스팅 실행
for file_path in file_paths:
    file_name = os.path.basename(file_path)
    print('\n ------------ ', file_path)
    print()

    # 파일명에서 필요한 정보를 추출
    sep = file_name.split('-')
    symbol = sep[0]
    timeframe = sep[-1].replace('.csv', '')

    for strategy in strategies:
        # 백테스트 결과를 저장할 CSV 파일 생성
        result_filename = f'{strategy}-{symbol}-{start.replace("-", "")}-{end.replace("-", "")}-{timeframe}.csv'
        result_filepath = os.path.join(result_dir, result_filename)
        with open(result_filepath, 'w', newline='') as csvfile:
            result_writer = csv.writer(csvfile, delimiter=',')
            result_writer.writerow(['Pair', 'Timeframe', 'Start', 'End', 'Strategy', 'Period', 'Final value', '%', 'Total win', 'Total loss', 'SQN'])

            for period in periodRange:
                # 백테스팅 실행
                end_val, totalwin, totalloss, pnl_net, sqn = backtest.run_custom_backtest(
                    file_path, start, end, period, strategy, commission_val, portofolio, stake_val, quantity, plot
                )
                profit = (pnl_net / portofolio) * 100

                # 결과 저장
                results[strategy]['periods'].append(period)
                results[strategy]['final_values'].append(end_val)
                results[strategy]['profits'].append(profit)

                # 콘솔에 결과 표시
                print(f'data processed: {file_name}, {strategy} (Period {period}) --- Ending Value: {end_val:.2f} --- Total win/loss {totalwin}/{totalloss}, SQN {sqn:.2f}')

                result_writer.writerow([symbol, timeframe, start, end, strategy, period, round(end_val, 3), round(profit, 3), totalwin, totalloss, sqn])

# 결과 시각화
for strategy in strategies:
    plt.figure(figsize=(12, 6))
    plt.plot(results[strategy]['periods'], results[strategy]['final_values'], marker='o', label='Final Value')
    plt.plot(results[strategy]['periods'], results[strategy]['profits'], marker='x', label='Profit (%)')
    plt.title(f'{strategy} Strategy Performance')
    plt.xlabel('Period')
    plt.ylabel('Value / Profit')
    plt.grid(True)
    plt.legend()
    plt.show()
