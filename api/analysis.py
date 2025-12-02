import json
import yfinance as yf
import pandas as pd
import numpy as np

# --- CONFIGURAÇÃO ---
# Lista simulada de tickers do IBOV. ***AJUSTADO: Reduzido para apenas 1 ticker para máxima estabilidade***
IBOV_TICKERS = ["PETR4.SA"] 
DAYS_TO_FETCH = 40 # Período necessário para calcular a MMA20
PERIOD_LOOKBACK = "1mo" # Reduzido para 1 mês de dados para maior velocidade
MMA_SHORT = 9
MMA_LONG = 20
THRESHOLD_PROXIMITY = 0.015 # 1.5% de proximidade da MMA20

def calculate_setup_conditions(df: pd.DataFrame, ticker: str):
    """
    Calcula as Médias Móveis (MMA9 e MMA20) e verifica as condições
    para a estratégia Power Breakout.
    
    A condição principal (simplificada) é:
    1. O preço de fechamento está próximo da MMA20 (correção).
    2. A MMS9 está cruzando ou está prestes a cruzar a MMA20 na direção da tendência.
    
    Retorna um dicionário com os resultados da análise.
    """
    if df.empty or len(df) < MMA_LONG:
        return None, "Dados insuficientes ou insuficientes para MMA20"

    # 1. Cálculo das Médias Móveis
    df['MMA9'] = df['Close'].rolling(window=MMA_SHORT).mean()
    df['MMA20'] = df['Close'].rolling(window=MMA_LONG).mean()

    # Pega o último dia (mais recente)
    latest = df.iloc[-1]
    
    current_price = latest['Close']
    mms9 = latest['MMA9']
    mms20 = latest['MMA20']

    # 2. Definição da Tendência (Simplificada: MMA20 ascendente ou descendente)
    # Compara a MMA20 de 5 dias atrás com a atual
    if len(df) >= MMA_LONG + 5:
        mms20_past = df.iloc[-5]['MMA20']
        if mms20 > mms20_past * 1.002: # MMA20 subindo > 0.2% em 5 dias
            trend = "Alta"
        elif mms20 < mms20_past * 0.998: # MMA20 caindo > 0.2% em 5 dias
            trend = "Baixa"
        else:
            trend = "Lateral"
    else:
        trend = "Indefinida"

    # 3. Verificação da Proximidade à MMA20 (Correção)
    price_proximity_to_mms20 = abs(current_price - mms20) / mms20
    is_close_to_mms20 = price_proximity_to_mms20 <= THRESHOLD_PROXIMITY
    
    # 4. Simulação de Gatilho e Níveis (Muito Simplificada para o propósito do App)
    is_setup_candidate = is_close_to_mms20 and trend != "Lateral"

    entry_price = None
    target_price = None
    stop_loss_price = None
    
    if is_setup_candidate:
        # Se for Alta: Entrada = Fechamento acima da MMA9 (Simulado: 1% acima da MMA9)
        if trend == "Alta":
            entry_price = mms9 * 1.01
            # Alvo (Topo Anterior Simulado) / Stop (Distância igual)
            distance = entry_price * 0.05 # Risco de 5%
            target_price = entry_price + distance
            stop_loss_price = entry_price - distance
        
        # Se for Baixa: Entrada = Fechamento abaixo da MMA9 (Simulado: 1% abaixo da MMA9)
        elif trend == "Baixa":
            entry_price = mms9 * 0.99
            # Alvo (Fundo Anterior Simulado) / Stop (Distância igual)
            distance = entry_price * 0.05 # Risco de 5%
            target_price = entry_price - distance
            stop_loss_price = entry_price + distance
            
        # Arredondar os preços
        if entry_price:
            entry_price = round(entry_price, 2)
            target_price = round(target_price, 2)
            stop_loss_price = round(stop_loss_price, 2)


    return {
        "ticker": ticker.replace(".SA", ""),
        "current_price": round(current_price, 2),
        "mms9": round(mms9, 2),
        "mms20": round(mms20, 2),
        "trend": trend,
        "is_setup_candidate": is_setup_candidate, 
        "analysis_time": pd.to_datetime('now').isoformat(),
        "entry_price": entry_price,
        "target_price": target_price,
        "stop_loss_price": stop_loss_price,
    }, None

def analyze_ibov_stocks():
    """
    Busca os dados de mercado e aplica a análise em todas as ações do IBOV.
    """
    analysis_results = []
    
    for ticker in IBOV_TICKERS:
        try:
            # 1. Busca os dados históricos
            stock = yf.Ticker(ticker)
            # Usa "Close" para evitar o erro de 'adj close' ser nulo em alguns casos
            df = stock.history(period=PERIOD_LOOKBACK, interval="1d")[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

            # ***VERIFICAÇÃO ADICIONAL DE DADOS***
            if df.empty:
                raise ValueError(f"Dados vazios retornados pelo yfinance para {ticker}.")
            
            # 2. Executa a análise
            result, error = calculate_setup_conditions(df, ticker)
            
            if result:
                analysis_results.append(result)
            elif error:
                # Logar o erro na Vercel (será visível nos logs)
                print(f"Erro na análise de {ticker}: {error}")
            
        except Exception as e:
            # Logar erro de rede/yfinance
            print(f"Erro ao buscar dados para {ticker}: {e}")
            # Em caso de erro, adiciona um placeholder
            analysis_results.append({
                "ticker": ticker.replace(".SA", ""),
                "current_price": 0.0, "mms9": 0.0, "mms20": 0.0,
                "trend": "Erro", "is_setup_candidate": False, 
                "analysis_time": pd.to_datetime('now').isoformat(),
                "entry_price": None, "target_price": None, "stop_loss_price": None
            })
            continue

    return analysis_results

def handler(event, context):
    """
    Função principal que a Vercel chamará (Serverless Function).
    """
    try:
        data = analyze_ibov_stocks()
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                # Necessário para CORS
                "Access-Control-Allow-Origin": "*" 
            },
            "body": json.dumps(data)
        }
    except Exception as e:
        print(f"Erro no handler: {e}")
        # Retorna um erro 500 mais detalhado
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": f"Erro interno do servidor: {str(e)}. Verifique os logs da Vercel para detalhes."})
        }

if __name__ == '__main__':
    # Teste de execução local
    results = analyze_ibov_stocks()
    print(json.dumps(results, indent=2))
