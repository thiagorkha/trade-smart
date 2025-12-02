import json
import random

# Este backend simula o acesso a dados de mercado e a lógica de análise.
# Em um ambiente real, você usaria bibliotecas como yfinance, pandas, e talib
# para obter dados reais, calcular médias móveis (MMA9 e MMA20) e
# analisar a tendência.

def get_simulated_stock_data():
    """
    Simula o processo de obter a lista de ações do IBOV e seus dados recentes.
    Retorna uma lista de ações com análises simuladas.
    """
    # Ações simuladas do IBOV
    tickers = ["PETR4", "VALE3", "ITUB4", "BBDC4", "MGLU3", "WEGE3", "PRIO3", "RENT3"]
    
    analysis_results = []

    for ticker in tickers:
        # Simula o preço atual, MMS9, e MMS20
        # Os valores são gerados para simular algumas ações em tendência e próximas da média.
        base_price = round(random.uniform(15.0, 50.0), 2)
        
        # Simula se a ação está em ponto de interesse (próxima da MMS20)
        is_close_to_mms20 = random.random() < 0.6  # 60% de chance de estar perto
        
        if is_close_to_mms20:
            # Perto da MMS20, em tendência de alta simulada
            mms20 = base_price * random.uniform(0.99, 1.01) # +- 1% da MMS20
            # Simula gatilho de entrada (MMS9 cruzando para cima da MMS20)
            mms9 = mms20 * random.uniform(1.005, 1.02)
            trend = "Alta"
        else:
            # Em tendência mais definida, longe da MMS20
            trend_multiplier = random.choice([1.15, 0.85]) # 15% acima (alta) ou abaixo (baixa)
            mms20 = base_price * trend_multiplier
            mms9 = mms20 * random.uniform(0.98, 1.01) # MMS9 perto da MMS20
            trend = "Baixa" if trend_multiplier < 1 else "Alta"

        # Simula o ponto de entrada, alvo e stop loss (para o frontend traçar)
        # Se for um ponto de interesse, simula o gatilho de entrada e os níveis.
        entry_price = round(base_price, 2)
        target_price = round(entry_price * 1.05, 2)
        stop_loss_price = round(entry_price * 0.95, 2)

        action_data = {
            "ticker": ticker,
            "current_price": base_price,
            "mms9": round(mms9, 2),
            "mms20": round(mms20, 2),
            "trend": trend,
            "is_setup_candidate": is_close_to_mms20, # Próximo da média de 20 (Setup inicial)
            "analysis_time": "2025-09-20T10:00:00Z",
            # Níveis calculados se o gatilho fosse acionado agora
            "entry_price": entry_price,
            "target_price": target_price,
            "stop_loss_price": stop_loss_price
        }
        analysis_results.append(action_data)
        
    return analysis_results

def handler(event, context):
    """
    Função principal que a Vercel chamará.
    O `event` (vindo do fetch no frontend) não é usado neste caso simples.
    """
    try:
        data = get_simulated_stock_data()
        
        # O backend da Vercel retornaria o JSON desta forma.
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                # Necessário para CORS no ambiente de desenvolvimento/teste
                "Access-Control-Allow-Origin": "*" 
            },
            "body": json.dumps(data)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)})
        }

# Para testes locais ou para a Vercel reconhecer
if __name__ == '__main__':
    print(json.dumps(get_simulated_stock_data(), indent=2))
elif 'vercel' in json.dumps(getattr(handler, '__globals__', {})):
    # Simula a exportação para o ambiente Vercel
    pass # A Vercel usará o `handler`
