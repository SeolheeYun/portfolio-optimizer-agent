"""
정량 데이터 MCP 서버
주식, 코인, 채권, 금 가격 데이터 제공
"""
import logging
import yaml
import yfinance as yf
import requests
from fastmcp import FastMCP

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("quantitative_server")

mcp = FastMCP("Quantitative Data Server")

# portfolio.yaml 로드
def load_portfolio():
    logger.debug("포트폴리오 파일 로드")
    with open("portfolio.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@mcp.tool()
def get_stock_prices() -> dict:
    """주식/ETF 가격과 수익률을 조회합니다."""
    portfolio = load_portfolio()
    results = []

    for stock in portfolio.get("stocks", []):
        symbol = stock["symbol"]
        try:
            logger.debug(f"주식 데이터 조회: {symbol}")
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")

            if hist.empty:
                logger.warning(f"주식 데이터 없음: {symbol}")
                results.append({"symbol": symbol, "error": "데이터 없음"})
                continue

            current = hist["Close"].iloc[-1]
            prev_day = hist["Close"].iloc[-2] if len(hist) > 1 else current
            week_ago = hist["Close"].iloc[-5] if len(hist) >= 5 else hist["Close"].iloc[0]
            month_ago = hist["Close"].iloc[0]

            results.append({
                "symbol": symbol,
                "name": stock["name"],
                "price": round(current, 2),
                "change_1d_pct": round((current - prev_day) / prev_day * 100, 2),
                "change_1w_pct": round((current - week_ago) / week_ago * 100, 2),
                "change_1m_pct": round((current - month_ago) / month_ago * 100, 2),
            })
        except Exception as e:
            logger.error(f"주식 데이터 조회 오류 ({symbol}): {e}")
            results.append({"symbol": symbol, "error": str(e)})

    logger.info(f"주식 데이터 조회 완료: {len(results)}개")
    return {"stocks": results}


@mcp.tool()
def get_crypto_prices() -> dict:
    """암호화폐 가격과 변동률을 조회합니다. (CoinGecko)"""
    portfolio = load_portfolio()
    crypto_ids = [c["symbol"] for c in portfolio.get("crypto", [])]

    if not crypto_ids:
        logger.warning("암호화폐 목록이 비어있음")
        return {"crypto": []}

    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": ",".join(crypto_ids),
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_7d_change": "true",
        }
        logger.debug(f"CoinGecko API 요청: {crypto_ids}")
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        results = []
        for crypto in portfolio.get("crypto", []):
            coin_id = crypto["symbol"]
            if coin_id in data:
                coin_data = data[coin_id]
                results.append({
                    "symbol": coin_id,
                    "name": crypto["name"],
                    "price": coin_data.get("usd", 0),
                    "change_24h_pct": round(coin_data.get("usd_24h_change", 0), 2),
                    "change_7d_pct": round(coin_data.get("usd_7d_change", 0), 2),
                })
            else:
                logger.warning(f"암호화폐 데이터 없음: {coin_id}")
                results.append({"symbol": coin_id, "error": "데이터 없음"})

        logger.info(f"암호화폐 데이터 조회 완료: {len(results)}개")
        return {"crypto": results}
    except Exception as e:
        logger.error(f"암호화폐 데이터 조회 오류: {e}", exc_info=True)
        return {"crypto": [], "error": str(e)}


@mcp.tool()
def get_bond_prices() -> dict:
    """채권 ETF 가격과 수익률을 조회합니다."""
    portfolio = load_portfolio()
    results = []

    for bond in portfolio.get("bonds", []):
        symbol = bond["symbol"]
        try:
            logger.debug(f"채권 데이터 조회: {symbol}")
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")

            if hist.empty:
                logger.warning(f"채권 데이터 없음: {symbol}")
                results.append({"symbol": symbol, "error": "데이터 없음"})
                continue

            current = hist["Close"].iloc[-1]
            prev_day = hist["Close"].iloc[-2] if len(hist) > 1 else current
            week_ago = hist["Close"].iloc[-5] if len(hist) >= 5 else hist["Close"].iloc[0]
            month_ago = hist["Close"].iloc[0]

            results.append({
                "symbol": symbol,
                "name": bond["name"],
                "price": round(current, 2),
                "change_1d_pct": round((current - prev_day) / prev_day * 100, 2),
                "change_1w_pct": round((current - week_ago) / week_ago * 100, 2),
                "change_1m_pct": round((current - month_ago) / month_ago * 100, 2),
            })
        except Exception as e:
            logger.error(f"채권 데이터 조회 오류 ({symbol}): {e}")
            results.append({"symbol": symbol, "error": str(e)})

    logger.info(f"채권 데이터 조회 완료: {len(results)}개")
    return {"bonds": results}


@mcp.tool()
def get_gold_prices() -> dict:
    """금 ETF 가격과 수익률을 조회합니다."""
    portfolio = load_portfolio()
    results = []

    for gold in portfolio.get("gold", []):
        symbol = gold["symbol"]
        try:
            logger.debug(f"금 데이터 조회: {symbol}")
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")

            if hist.empty:
                logger.warning(f"금 데이터 없음: {symbol}")
                results.append({"symbol": symbol, "error": "데이터 없음"})
                continue

            current = hist["Close"].iloc[-1]
            prev_day = hist["Close"].iloc[-2] if len(hist) > 1 else current
            week_ago = hist["Close"].iloc[-5] if len(hist) >= 5 else hist["Close"].iloc[0]
            month_ago = hist["Close"].iloc[0]

            results.append({
                "symbol": symbol,
                "name": gold["name"],
                "price": round(current, 2),
                "change_1d_pct": round((current - prev_day) / prev_day * 100, 2),
                "change_1w_pct": round((current - week_ago) / week_ago * 100, 2),
                "change_1m_pct": round((current - month_ago) / month_ago * 100, 2),
            })
        except Exception as e:
            logger.error(f"금 데이터 조회 오류 ({symbol}): {e}")
            results.append({"symbol": symbol, "error": str(e)})

    logger.info(f"금 데이터 조회 완료: {len(results)}개")
    return {"gold": results}


if __name__ == "__main__":
    mcp.run(transport="stdio")
