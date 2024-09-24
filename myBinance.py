'''

myUpbit.py 최종 버전은 클래스 챕터 8-2 (매수하고 난 뒤 5가지 선택지에 대하여!)의 수업자료 탭에서 다운로드 가능하니 참고하세요!


하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^

클래스 제작 완료 후 많은 시간이 흘렀고 그 사이 전략에 많은 발전이 있었습니다.
제가 직접 투자하고자 백테스팅으로 검증하여 더 안심하고 있는 자동매매 전략들을 블로그에 공개하고 있으니
완강 후 꼭 블로그&유튜브 심화 과정에 참여해 보세요! 기다릴께요!!

아래 빠른 자동매매 가이드 시간날 때 완독하시면 방향이 잡히실 거예요!
https://blog.naver.com/zacra/223086628069

  
'''
import ccxt
import time
import pandas as pd
import pprint
import numpy
import requests
from cryptography.fernet import Fernet


'''
여기에 바이낸스 봇에 사용될 함수들을 추가하세요!!
'''
# Discord Webhook URL 설정
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1284037857442529282/lsh6wD8HLmVZUCMZWtF0X2LmWsedAO5vBuxK4LQ77ltF22e0hQ17QJtumEFQQOvqCDfu'  # Webhook URL로 교체

def send_discord_message(content):
    """Discord에 메시지 전송"""
    data = {"content": content}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        response.raise_for_status()  # HTTP 에러 발생 시 예외를 발생시킵니다.
        print(f"Message sent to Discord: {content}")  # 성공적으로 전송된 경우 출력
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred while sending message to Discord: {http_err}")
    except Exception as err:
        print(f"Error occurred while sending message to Discord: {err}")


#암호화 복호화 클래스
class SimpleEnDecrypt:
    def __init__(self, key=None):
        if key is None: # 키가 없다면
            key = Fernet.generate_key() # 키를 생성한다
        self.key = key
        self.f   = Fernet(self.key)
    
    def encrypt(self, data, is_out_string=True):
        if isinstance(data, bytes):
            ou = self.f.encrypt(data) # 바이트형태이면 바로 암호화
        else:
            ou = self.f.encrypt(data.encode('utf-8')) # 인코딩 후 암호화
        if is_out_string is True:
            return ou.decode('utf-8') # 출력이 문자열이면 디코딩 후 반환
        else:
            return ou
        
    def decrypt(self, data, is_out_string=True):
        if isinstance(data, bytes):
            ou = self.f.decrypt(data) # 바이트형태이면 바로 복호화
        else:
            ou = self.f.decrypt(data.encode('utf-8')) # 인코딩 후 복호화
        if is_out_string is True:
            return ou.decode('utf-8') # 출력이 문자열이면 디코딩 후 반환
        else:
            return ou


#RSI지표 수치를 구해준다. 첫번째: 분봉/일봉 정보, 두번째: 기간, 세번째: 기준 날짜
def GetRSI(ohlcv,period,st):
    delta = ohlcv["close"].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    RS = _gain / _loss
    return float(pd.Series(100 - (100 / (1 + RS)), name="RSI").iloc[st])

#이동평균선 수치를 구해준다 첫번째: 분봉/일봉 정보, 두번째: 기간, 세번째: 기준 날짜
def GetMA(ohlcv,period,st):
    close = ohlcv["close"]
    ma = close.rolling(period).mean()
    return float(ma.iloc[st])

#볼린저 밴드를 구해준다 첫번째: 분봉/일봉 정보, 두번째: 기간, 세번째: 기준 날짜
#차트와 다소 오차가 있을 수 있습니다.
def GetBB(ohlcv,period,st):
    dic_bb = dict()

    ohlcv = ohlcv[::-1]
    ohlcv = ohlcv.shift(st + 1)
    close = ohlcv["close"].iloc[::-1]

    unit = 2.0
    bb_center=numpy.mean(close[len(close)-period:len(close)])
    band1=unit*numpy.std(close[len(close)-period:len(close)])

    dic_bb['ma'] = float(bb_center)
    dic_bb['upper'] = float(bb_center + band1)
    dic_bb['lower'] = float(bb_center - band1)

    return dic_bb

# 스토캐스틱 %K %D 값을 구해준다 첫번째: 분봉/일봉 정보, 두번째: 기간, 세번째: 기준 날짜
def GetStochastic(ohlcv, period, k_period, st):
    """스토캐스틱 %K, %D 값을 반환합니다."""
    dic_stoch = dict()

    ndays_high = ohlcv['high'].rolling(window=period, min_periods=1).max()
    ndays_low = ohlcv['low'].rolling(window=period, min_periods=1).min()
    fast_k = (ohlcv['close'] - ndays_low) / (ndays_high - ndays_low) * 100
    slow_d = fast_k.rolling(window=k_period, min_periods=1).mean()

    dic_stoch['k'] = fast_k.iloc[st]
    dic_stoch['d'] = slow_d.iloc[st]

    return dic_stoch



#일목 균형표의 각 데이타를 리턴한다 첫번째: 분봉/일봉 정보, 두번째: 기준 날짜
def GetIC(ohlcv,st):

    high_prices = ohlcv['high']
    close_prices = ohlcv['close']
    low_prices = ohlcv['low']


    nine_period_high =  ohlcv['high'].shift(-2-st).rolling(window=9).max()
    nine_period_low = ohlcv['low'].shift(-2-st).rolling(window=9).min()
    ohlcv['conversion'] = (nine_period_high + nine_period_low) /2
    
    period26_high = high_prices.shift(-2-st).rolling(window=26).max()
    period26_low = low_prices.shift(-2-st).rolling(window=26).min()
    ohlcv['base'] = (period26_high + period26_low) / 2
    
    ohlcv['sunhang_span_a'] = ((ohlcv['conversion'] + ohlcv['base']) / 2).shift(26)
    
    
    period52_high = high_prices.shift(-2-st).rolling(window=52).max()
    period52_low = low_prices.shift(-2-st).rolling(window=52).min()
    ohlcv['sunhang_span_b'] = ((period52_high + period52_low) / 2).shift(26)
    
    
    ohlcv['huhang_span'] = close_prices.shift(-26)


    nine_period_high_real =  ohlcv['high'].rolling(window=9).max()
    nine_period_low_real = ohlcv['low'].rolling(window=9).min()
    ohlcv['conversion'] = (nine_period_high_real + nine_period_low_real) /2
    
    period26_high_real = high_prices.rolling(window=26).max()
    period26_low_real = low_prices.rolling(window=26).min()
    ohlcv['base'] = (period26_high_real + period26_low_real) / 2
    


    
    dic_ic = dict()

    dic_ic['conversion'] = ohlcv['conversion'].iloc[st]
    dic_ic['base'] = ohlcv['base'].iloc[st]
    dic_ic['huhang_span'] = ohlcv['huhang_span'].iloc[-27]
    dic_ic['sunhang_span_a'] = ohlcv['sunhang_span_a'].iloc[-1]
    dic_ic['sunhang_span_b'] = ohlcv['sunhang_span_b'].iloc[-1]


  

    return dic_ic




#MACD의 12,26,9 각 데이타를 리턴한다 첫번째: 분봉/일봉 정보, 두번째: 기준 날짜
def GetMACD(ohlcv,st):
    macd_short, macd_long, macd_signal=12,26,9

    ohlcv["MACD_short"]=ohlcv["close"].ewm(span=macd_short).mean()
    ohlcv["MACD_long"]=ohlcv["close"].ewm(span=macd_long).mean()
    ohlcv["MACD"]=ohlcv["MACD_short"] - ohlcv["MACD_long"]
    ohlcv["MACD_signal"]=ohlcv["MACD"].ewm(span=macd_signal).mean() 

    dic_macd = dict()
    
    dic_macd['macd'] = ohlcv["MACD"].iloc[st]
    dic_macd['macd_siginal'] = ohlcv["MACD_signal"].iloc[st]
    dic_macd['ocl'] = dic_macd['macd'] - dic_macd['macd_siginal']

    return dic_macd



#스토캐스틱 %K %D 값을 구해준다 첫번째: 분봉/일봉 정보, 두번째: 기간, 세번째: 기준 날짜
def GetStoch(ohlcv,period,st):

    dic_stoch = dict()

    ndays_high = ohlcv['high'].rolling(window=period, min_periods=1).max()
    ndays_low = ohlcv['low'].rolling(window=period, min_periods=1).min()
    fast_k = (ohlcv['close'] - ndays_low)/(ndays_high - ndays_low)*100
    slow_d = fast_k.rolling(window=3, min_periods=1).mean()

    dic_stoch['fast_k'] = fast_k.iloc[st]
    dic_stoch['slow_d'] = slow_d.iloc[st]

    return dic_stoch



#분봉/일봉 캔들 정보를 가져온다 첫번째: 바이낸스 객체, 두번째: 코인 티커, 세번째: 기간 (1d,4h,1h,15m,10m,1m ...)
def GetOhlcv(binance, Ticker, period):
    btc_ohlcv = binance.fetch_ohlcv(Ticker, period)
    df = pd.DataFrame(btc_ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    return df

#스탑로스를 걸어놓는다. 해당 가격에 해당되면 바로 손절한다. 첫번째: 바이낸스 객체, 두번째: 코인 티커, 세번째: 손절 수익율 (1.0:마이너스100% 청산, 0.9:마이너스 90%, 0.5: 마이너스 50%)
#네번째 웹훅 알림에서 사용할때는 마지막 파라미터를 False로 넘겨서 사용한다. 트레이딩뷰 웹훅 강의 참조..

def SetStopLoss(binance, Ticker, cut_rate, Rest=True, retries=3):
    """
    스탑 로스를 설정하는 함수.
    
    binance: ccxt 객체
    Ticker: 거래할 코인 티커 (예: "ETH/USDT")
    cut_rate: 손절 비율
    Rest: 대기 시간을 줄지 여부 (기본값: True)
    retries: entryPrice가 0일 때 재시도 횟수 (기본값: 3)
    """
    
    if Rest:
        time.sleep(0.1)
        
    # 현재 열린 주문 정보를 읽어옵니다.
    orders = binance.fetch_orders(Ticker)
    StopLossOk = any(order['status'] == "open" and order['type'] == 'stop_market' for order in orders)

    # 스탑로스 주문이 이미 있는 경우 함수 종료
    if StopLossOk:
        print("Stop loss order already exists. No new stop loss order placed.")
        return

    if Rest:
        time.sleep(10.0)

    # 잔고 데이터를 가져옵니다.
    balance = binance.fetch_balance(params={"type": "future"})

    if Rest:
        time.sleep(0.1)

    amt = 0
    entryPrice = None  # None으로 초기화하여 유효성 검사
    leverage = 0

    # 평균 매입단가와 수량을 가져옵니다.
    for posi in balance['info']['positions']:
        if posi['symbol'] == Ticker.replace("/", "").replace(":USDT", ""):
            entryPrice = float(posi.get('entryPrice', 0))  # 안전한 접근
            amt = float(posi.get('positionAmt', 0))
            leverage = float(posi.get('leverage', 1))
            break

    # 포지션이 없거나 entryPrice가 0인 경우에 대한 처리
    if amt == 0:
        print(f"No position found for ticker {Ticker}. Stop loss will not be set.")
        return

    # entryPrice가 유효한지 확인
    attempts = 0
    while (entryPrice is None or entryPrice == 0) and attempts < retries:
        print(f"Attempt {attempts + 1}: 'entryPrice' is not available or is zero for ticker {Ticker}. Retrying...")
        time.sleep(2)  # 2초 대기 후 다시 시도
        balance = binance.fetch_balance(params={"type": "future"})
        for posi in balance['info']['positions']:
            if posi['symbol'] == Ticker.replace("/", "").replace(":USDT", ""):
                entryPrice = float(posi.get('entryPrice', 0))
                amt = float(posi.get('positionAmt', 0))
                leverage = float(posi.get('leverage', 1))
                break
        attempts += 1

    if entryPrice is None or entryPrice == 0:
        print(f"Error: 'entryPrice' is not available or is zero for ticker {Ticker}. Cannot set stop loss.")
        return

    # 포지션 방향에 따른 손절 주문 방향 설정
    side = "sell" if amt > 0 else "buy"

    # 손절 비율 계산
    danger_rate = ((100.0 / leverage) * cut_rate) * 1.0

    # 손절 가격 계산
    stopPrice = entryPrice * (1.0 - danger_rate * 0.01) if amt > 0 else entryPrice * (1.0 + danger_rate * 0.01)

    # 주문 매개변수 설정
    params = {
        'stopPrice': stopPrice,
        'closePosition': True
    }

    print("side:", side, "stopPrice:", stopPrice, "entryPrice:", entryPrice)

    try:
        # 스탑 로스 주문을 생성
        order = binance.create_order(Ticker, 'STOP_MARKET', side, abs(amt), None, params)
        print(order)
        print("#### STOPLOSS SETTING DONE ####")
    except Exception as e:
        print(f"Failed to set stop loss for {Ticker}: {e}")

 
#스탑로스를 걸어놓는다. 해당 가격에 해당되면 바로 손절한다. 첫번째: 바이낸스 객체, 두번째: 코인 티커, 세번째: 손절 가격
#네번째 웹훅 알림에서 사용할때는 마지막 파라미터를 False로 넘겨서 사용한다. 트레이딩뷰 웹훅 강의 참조..
def SetStopLossPrice(binance, Ticker, StopPrice, Rest = True):

    if Rest == True:
        time.sleep(0.1)
        
    #주문 정보를 읽어온다.
    orders = binance.fetch_orders(Ticker)

    StopLossOk = False
    for order in orders:

        if order['status'] == "open" and order['type'] == 'stop_market':
            #print(order)
            StopLossOk = True
            break

    #스탑로스 주문이 없다면 주문을 건다!
    if StopLossOk == False:

        if Rest == True:
            time.sleep(10.0)

        #잔고 데이타를 가지고 온다.
        balance = binance.fetch_balance(params={"type": "future"})

        if Rest == True:
            time.sleep(0.1)
                                
        amt = 0
        entryPrice = 0

        #평균 매입단가와 수량을 가지고 온다.
        for posi in balance['info']['positions']:
            if posi['symbol'] == Ticker.replace("/", "").replace(":USDT", ""):
                entryPrice = float(posi['entryPrice'])
                amt = float(posi['positionAmt'])
          

        #롱일땐 숏을 잡아야 되고
        side = "sell"
        #숏일땐 롱을 잡아야 한다.
        if amt < 0:
            side = "buy"

 
        params = {
            'stopPrice': StopPrice,
            'closePosition' : True
        }

        print("side:",side,"   stopPrice:",StopPrice, "   entryPrice:",entryPrice)
        #스탑 로스 주문을 걸어 놓는다.
        print(binance.create_order(Ticker,'STOP_MARKET',side,abs(amt),StopPrice,params))

        print("####STOPLOSS SETTING DONE ######################")

#
# 
################# Hedge Mode 에서 유효한 함수####################
# https://blog.naver.com/zacra/222662884649
#
#스탑로스를 걸어놓는다. 해당 가격에 해당되면 바로 손절한다. 첫번째: 바이낸스 객체, 두번째: 코인 티커, 세번째: 손절 수익율 (1.0:마이너스100% 청산, 0.9:마이너스 90%, 0.5: 마이너스 50%)
def SetStopLossLong(binance, Ticker, cut_rate, Rest = True):

    if Rest == True:
        time.sleep(0.1)
    #주문 정보를 읽어온다.
    orders = binance.fetch_orders(Ticker)

    for order in orders:

        if order['status'] == "open" and order['type'] == 'stop_market' and order['info']['positionSide'] == "LONG":
            binance.cancel_order(order['id'],Ticker)

            break

    if Rest == True:
        time.sleep(2.0)

    #잔고 데이타를 가지고 온다.
    balance = binance.fetch_balance(params={"type": "future"})
    if Rest == True:
        time.sleep(0.1)
                            


    amt_b = 0 
    entryPrice_b = 0 #평균 매입 단가. 따라서 물을 타면 변경 된다.
    leverage = 0

    #롱잔고
    for posi in balance['info']['positions']:
        if posi['symbol'] == Ticker.replace("/", "").replace(":USDT", "")  and posi['positionSide'] == 'LONG':

            amt_b = float(posi['positionAmt'])
            entryPrice_b = float(posi['entryPrice'])
            leverage = float(posi['leverage'])
            break


    #롱일땐 숏을 잡아야 되고
    side = "sell"


    danger_rate = ((100.0 / leverage) * cut_rate) * 1.0

    #롱일 경우의 손절 가격을 정한다.
    stopPrice = entryPrice_b * (1.0 - danger_rate*0.01)


    params = {
        'positionSide': 'LONG',
        'stopPrice': stopPrice,
        'closePosition' : True
    }

    print("side:",side,"   stopPrice:",stopPrice, "   entryPrice:",entryPrice_b)
    #스탑 로스 주문을 걸어 놓는다.
    print(binance.create_order(Ticker,'STOP_MARKET',side,abs(amt_b),stopPrice,params))

    print("####STOPLOSS SETTING DONE ######################")






#
# 
################# Hedge Mode 에서 유효한 함수####################
# https://blog.naver.com/zacra/222662884649
#
#스탑로스를 걸어놓는다. 해당 가격에 해당되면 바로 손절한다. 첫번째: 바이낸스 객체, 두번째: 코인 티커, 세번째: 손절 수익율 (1.0:마이너스100% 청산, 0.9:마이너스 90%, 0.5: 마이너스 50%)
def SetStopLossShort(binance, Ticker, cut_rate, Rest = True):

    if Rest == True:
        time.sleep(0.1)
    #주문 정보를 읽어온다.
    orders = binance.fetch_orders(Ticker)

    for order in orders:

        if order['status'] == "open" and order['type'] == 'stop_market' and order['info']['positionSide'] == "SHORT":
            binance.cancel_order(order['id'],Ticker)

    if Rest == True:
        time.sleep(2.0)

    #잔고 데이타를 가지고 온다.
    balance = binance.fetch_balance(params={"type": "future"})
    if Rest == True:
        time.sleep(0.1)
                            



    amt_s = 0 
    entryPrice_s = 0 #평균 매입 단가. 따라서 물을 타면 변경 된다.
    leverage = 0

    #숏잔고
    for posi in balance['info']['positions']:
        if posi['symbol'] == Ticker.replace("/", "").replace(":USDT", "") and posi['positionSide'] == 'SHORT':

            amt_s = float(posi['positionAmt'])
            entryPrice_s= float(posi['entryPrice'])
            leverage = float(posi['leverage'])

            break




    #롱일땐 숏을 잡아야 되고
    side = "buy"


    danger_rate = ((100.0 / leverage) * cut_rate) * 1.0


    stopPrice = entryPrice_s * (1.0 + danger_rate*0.01)

    params = {
        'positionSide': 'SHORT',
        'stopPrice': stopPrice,
        'closePosition' : True
    }

    print("side:",side,"   stopPrice:",stopPrice, "   entryPrice:",entryPrice_s)
    #스탑 로스 주문을 걸어 놓는다.
    print(binance.create_order(Ticker,'STOP_MARKET',side,abs(amt_s),stopPrice,params))

    print("####STOPLOSS SETTING DONE ######################")










#
# 
################# Hedge Mode 에서 유효한 함수####################
# https://blog.naver.com/zacra/222662884649
#
#스탑로스를 걸어놓는다. 해당 가격에 해당되면 바로 손절한다. 첫번째: 바이낸스 객체, 두번째: 코인 티커, 세번째: 손절 가격
def SetStopLossLongPrice(binance, Ticker, StopPrice, Rest = True):

    if Rest == True:
        time.sleep(0.1)
    #주문 정보를 읽어온다.
    orders = binance.fetch_orders(Ticker)

    for order in orders:

        if order['status'] == "open" and order['type'] == 'stop_market' and order['info']['positionSide'] == "LONG":
            binance.cancel_order(order['id'],Ticker)

            break

    if Rest == True:
        time.sleep(2.0)

    #잔고 데이타를 가지고 온다.
    balance = binance.fetch_balance(params={"type": "future"})
    if Rest == True:
        time.sleep(0.1)
                            


    amt_b = 0 
    entryPrice_b = 0 #평균 매입 단가. 따라서 물을 타면 변경 된다.

    #롱잔고
    for posi in balance['info']['positions']:
        if posi['symbol'] == Ticker.replace("/", "").replace(":USDT", "")  and posi['positionSide'] == 'LONG':

            amt_b = float(posi['positionAmt'])
            entryPrice_b = float(posi['entryPrice'])
            break


    #롱일땐 숏을 잡아야 되고
    side = "sell"


    params = {
        'positionSide': 'LONG',
        'stopPrice': StopPrice,
        'closePosition' : True
    }

    print("side:",side,"   stopPrice:",StopPrice, "   entryPrice:",entryPrice_b)
    #스탑 로스 주문을 걸어 놓는다.
    print(binance.create_order(Ticker,'STOP_MARKET',side,abs(amt_b),StopPrice,params))

    print("####STOPLOSS SETTING DONE ######################")






#
# 
################# Hedge Mode 에서 유효한 함수####################
# https://blog.naver.com/zacra/222662884649
#
#스탑로스를 걸어놓는다. 해당 가격에 해당되면 바로 손절한다. 첫번째: 바이낸스 객체, 두번째: 코인 티커, 세번째: 손절 가격
def SetStopLossShortPrice(binance, Ticker, StopPrice, Rest = True):

    if Rest == True:
        time.sleep(0.1)
    #주문 정보를 읽어온다.
    orders = binance.fetch_orders(Ticker)

    for order in orders:

        if order['status'] == "open" and order['type'] == 'stop_market' and order['info']['positionSide'] == "SHORT":
            binance.cancel_order(order['id'],Ticker)

    if Rest == True:
        time.sleep(2.0)

    #잔고 데이타를 가지고 온다.
    balance = binance.fetch_balance(params={"type": "future"})
    if Rest == True:
        time.sleep(0.1)
                            



    amt_s = 0 
    entryPrice_s = 0 #평균 매입 단가. 따라서 물을 타면 변경 된다.

    #숏잔고
    for posi in balance['info']['positions']:
        if posi['symbol'] == Ticker.replace("/", "").replace(":USDT", "") and posi['positionSide'] == 'SHORT':

            amt_s = float(posi['positionAmt'])
            entryPrice_s= float(posi['entryPrice'])

            break




    #롱일땐 숏을 잡아야 되고
    side = "buy"

    params = {
        'positionSide': 'SHORT',
        'stopPrice': StopPrice,
        'closePosition' : True
    }

    print("side:",side,"   stopPrice:",StopPrice, "   entryPrice:",entryPrice_s)
    #스탑 로스 주문을 걸어 놓는다.
    print(binance.create_order(Ticker,'STOP_MARKET',side,abs(amt_s),StopPrice,params))

    print("####STOPLOSS SETTING DONE ######################")









#구매할 수량을 구한다.  첫번째: 돈(USDT), 두번째:코인 가격, 세번째: 비율 1.0이면 100%, 0.5면 50%
def GetAmount(usd, coin_price, rate):

    target = usd * rate 

    amout = target/coin_price


    #print("amout", amout)
    return amout

#거래할 코인의 현재가를 가져온다. 첫번째: 바이낸스 객체, 두번째: 코인 티커
def GetCoinNowPrice(binance,Ticker):
    coin_info = binance.fetch_ticker(Ticker)
    coin_price = coin_info['last'] # coin_info['close'] == coin_info['last'] 

    return coin_price


def ExistOrderSide(binance,Ticker,Side):
    #주문 정보를 읽어온다.
    orders = binance.fetch_orders(Ticker)

    ExistFlag = False
    for order in orders:
        if order['status'] == "open" and order['side'] == Side:
            ExistFlag = True

    return ExistFlag


        
#거래대금 폭발 여부 첫번째: 캔들 정보, 두번째: 이전 5개의 평균 거래량보다 몇 배 이상 큰지
#이전 캔들이 그 이전 캔들 5개의 평균 거래금액보다 몇 배이상 크면 거래량 폭발로 인지하고 True를 리턴해줍니다
#현재 캔들[-1]은 막 시작했으므로 이전 캔들[-2]을 보는게 맞다!
def IsVolumePung(ohlcv,st):

    Result = False
    try:
        avg_volume = (float(ohlcv['volume'].iloc[-3]) + float(ohlcv['volume'].iloc[-4]) + float(ohlcv['volume'].iloc[-5]) + float(ohlcv['volume'].iloc[-6]) + float(ohlcv['volume'].iloc[-7])) / 5.0
        if avg_volume * st < float(ohlcv['volume'].iloc[-2]):
            Result = True
    except Exception as e:
        print("IsVolumePung ---:", e)

    
    return Result



#내가 포지션 잡은 (가지고 있는) 코인 개수를 리턴하는 함수
def GetHasCoinCnt(binance):

    #잔고 데이타 가져오기 
    balances = binance.fetch_balance(params={"type": "future"})
    time.sleep(0.1)

    #선물 마켓에서 거래중인 코인을 가져옵니다.
    Tickers = binance.fetch_tickers()

    
    CoinCnt = 0
    #모든 선물 거래가능한 코인을 가져온다.
    for ticker in Tickers:

        if "/USDT" in ticker:
            Target_Coin_Symbol = ticker.replace("/", "").replace(":USDT", "")

            amt = 0
            #실제로 잔고 데이타의 포지션 정보 부분에서 해당 코인에 해당되는 정보를 넣어준다.
            for posi in balances['info']['positions']:
                if posi['symbol'] == Target_Coin_Symbol:
                    amt = float(posi['positionAmt'])
                    break

            if amt != 0:
                CoinCnt += 1


    return CoinCnt


#바이낸스 선물 거래에서 거래량이 많은 코인 순위 (테더 선물 마켓)
def GetTopCoinList(binance, top):
    print("--------------GetTopCoinList Start-------------------")

    #선물 마켓에서 거래중인 코인을 가져옵니다.
    Tickers = binance.fetch_tickers()
    pprint.pprint(Tickers)

    dic_coin_money = dict()
    #모든 선물 거래가능한 코인을 가져온다.
    for ticker in Tickers:

        try: 

            if "/USDT" in ticker:
                print(ticker,"----- \n",Tickers[ticker]['baseVolume'] * Tickers[ticker]['close'])

                dic_coin_money[ticker] = Tickers[ticker]['baseVolume'] * Tickers[ticker]['close']

        except Exception as e:
            print("---:", e)


    dic_sorted_coin_money = sorted(dic_coin_money.items(), key = lambda x : x[1], reverse= True)


    coin_list = list()
    cnt = 0
    for coin_data in dic_sorted_coin_money:
        print("####-------------", coin_data[0], coin_data[1])
        cnt += 1
        if cnt <= top:
            coin_list.append(coin_data[0])
        else:
            break

    print("--------------GetTopCoinList End-------------------")

    return coin_list


#해당되는 리스트안에 해당 코인이 있는지 여부를 리턴하는 함수
def CheckCoinInList(CoinList,Ticker):
    InCoinOk = False
    for coinTicker in CoinList:
        if coinTicker.replace(":USDT", "") == Ticker.replace(":USDT", ""):
            InCoinOk = True
            break

    return InCoinOk



# 트레일링 스탑 함수!
# https://blog.naver.com/zhanggo2/222664158175 여기 참고!!
def create_trailing_sell_order(binance, Ticker, amount, activationPrice=None, rate=0.2):
    # rate range min 0.1, max 5 (%) from binance rule
    if rate < 0.1:
        rate = 0.1
    elif rate > 5:
        rate = 5

    if activationPrice == None:
        # activate from current price
        params = {
            'callbackRate': rate
        }
    else:
        # given activationprice
        params = {
            'activationPrice': activationPrice,
            'callbackRate': rate
        }

    print(binance.create_order(Ticker, 'TRAILING_STOP_MARKET', 'sell', amount ,None, params))


# 트레일링 스탑 함수!
# https://blog.naver.com/zhanggo2/222664158175 여기 참고!!
def create_trailing_buy_order(binance, Ticker, amount, activationPrice=None, rate=0.2):
    # rate range min 0.1, max 5 (%) from binance rule
    if rate < 0.1:
        rate = 0.1
    elif rate > 5:
        rate = 5

    if activationPrice == None:
        # activate from current price
        params = {
            'callbackRate': rate
        }
    else:
        # given activationprice
        params = {
            'activationPrice': activationPrice,
            'callbackRate': rate
        }

    print(binance.create_order(Ticker, 'TRAILING_STOP_MARKET', 'buy', amount ,None, params))



#
# 트레일링 스탑 함수!
################# Hedge Mode 에서 유효한 함수####################
# https://blog.naver.com/zacra/222662884649
#
def create_trailing_sell_order_Long(binance, Ticker, amount, activationPrice=None, rate=0.2):
    # rate range min 0.1, max 5 (%) from binance rule
    if rate < 0.1:
        rate = 0.1
    elif rate > 5:
        rate = 5

    if activationPrice == None:
        # activate from current price
        params = {
            'positionSide': 'LONG',
            'callbackRate': rate
        }
    else:
        # given activationprice
        params = {
            'positionSide': 'LONG',
            'activationPrice': activationPrice,
            'callbackRate': rate
        }

    print(binance.create_order(Ticker, 'TRAILING_STOP_MARKET', 'sell', amount ,None, params))


#
# 트레일링 스탑 함수!
################# Hedge Mode 에서 유효한 함수####################
# https://blog.naver.com/zacra/222662884649
#
def create_trailing_buy_order_Short(binance, Ticker, amount, activationPrice=None, rate=0.2):
    # rate range min 0.1, max 5 (%) from binance rule
    if rate < 0.1:
        rate = 0.1
    elif rate > 5:
        rate = 5

    if activationPrice == None:
        # activate from current price
        params = {
            'positionSide': 'SHORT',
            'callbackRate': rate
        }
    else:
        # given activationprice
        params = {
            'positionSide': 'SHORT',
            'activationPrice': activationPrice,
            'callbackRate': rate
        }

    print(binance.create_order(Ticker, 'TRAILING_STOP_MARKET', 'buy', amount ,None, params))





# 최소 주문 단위 금액 구하는 함수
# https://blog.naver.com/zhanggo2/222722244744 
# 이 함수는 이곳을 참고하세요 
def GetMinimumAmount(binance, ticker):
    limit_values = binance.markets[ticker]['limits']

    min_amount = limit_values['amount']['min']
    min_cost = limit_values['cost']['min']
    min_price = limit_values['price']['min']

    coin_info = binance.fetch_ticker(ticker)
    coin_price = coin_info['last']

    print("min_cost: ",min_cost)
    print("min_amount: ",min_amount)
    print("min_price: ",min_price)
    print("coin_price: ",coin_price)

    # get mininum unit price to be able to order
    if min_price < coin_price:
        min_price = coin_price

    # order cost = price * amount
    min_order_cost = min_price * min_amount

    num_min_amount = 1

    if min_cost is not None and min_order_cost < min_cost:
        # if order cost is smaller than min cost
        # increase the order cost bigger than min cost
        # by the multiple number of minimum amount
        while min_order_cost < min_cost:
            num_min_amount = num_min_amount + 1
            min_order_cost = min_price * (num_min_amount * min_amount)

    return num_min_amount * min_amount





#현재 평가금액을 구한다!
def GetTotalRealMoney(balance):
    return float(balance['info']['totalWalletBalance']) + float(balance['info']['totalUnrealizedProfit'])


#코인의 평가 금액을 구한다!
def GetCoinRealMoney(balance,ticker,posiSide):

    Money = 0

    for posi in balance['info']['positions']:
        if posi['symbol'] == ticker.replace("/", "").replace(":USDT", "") and posi['positionSide'] == posiSide:
            Money = float(posi['initialMargin']) + float(posi['unrealizedProfit'])
            break

    return Money

# 레버리지 설정 함수 정의
def SetLeverage(binance, symbol, leverage):
    try:
        # set_leverage 메서드로 레버리지 설정
        response = binance.set_leverage(leverage, symbol)
        print(f"Leverage set to {leverage} for {symbol}. Response: {response}")
    except Exception as e:
        print(f"Failed to set leverage for {symbol}: {str(e)}")

# 레버리지 확인 함수 정의
def GetLeverage(binance, symbol):
    try:
        # fetch_balance로 포지션 정보 가져오기
        balance = binance.fetch_balance({'type': 'future'})
        positions = balance['info']['positions']
        print("Positions fetched:", positions)  # 디버깅을 위해 추가
        for pos in positions:
            if pos['symbol'] == symbol.replace("/", ""):  # "BTC/USDT" -> "BTCUSDT"
                return float(pos['leverage'])
    except Exception as e:
        print(f"Failed to get leverage for {symbol}: {str(e)}")
    return None