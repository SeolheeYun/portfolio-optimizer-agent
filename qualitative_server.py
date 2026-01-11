"""
정성 데이터 MCP 서버
환율, 공포탐욕지수, 시장 요약 제공
"""
import logging
import yfinance as yf
import requests
from fastmcp import FastMCP

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("qualitative_server")

mcp = FastMCP("Qualitative Data Server")

@mcp.tool()
def get_exchange_rate() -> dict:
    """USD/KRW 환율을 조회합니다."""
    try:
        ticker = yf.Ticker("USDKRW=X")
        hist = ticker.history(period="1mo")

        if hist.empty:
            logger.warning("환율 데이터 없음")
            return {"error": "환율 데이터 없음"}

        current = hist["Close"].iloc[-1]
        prev_day = hist["Close"].iloc[-2] if len(hist) > 1 else current
        week_ago = hist["Close"].iloc[-5] if len(hist) >= 5 else hist["Close"].iloc[0]
        month_ago = hist["Close"].iloc[0]

        result = {
            "pair": "USD/KRW",
            "rate": round(current, 2),
            "change_1d_pct": round((current - prev_day) / prev_day * 100, 2),
            "change_1w_pct": round((current - week_ago) / week_ago * 100, 2),
            "change_1m_pct": round((current - month_ago) / month_ago * 100, 2),
        }
        logger.info(f"환율 조회 완료: {result['rate']} KRW")
        return result
    except Exception as e:
        logger.error(f"환율 조회 오류: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def get_fear_greed_index() -> dict:
    """암호화폐 Fear & Greed Index를 조회합니다. (0=극단적 공포, 100=극단적 탐욕)"""
    try:
        # Alternative.me Crypto Fear & Greed Index (무료)
        url = "https://api.alternative.me/fng/?limit=7"
        logger.debug(f"API 요청: {url}")
        resp = requests.get(url, timeout=10)
        data = resp.json()

        fng_data = data.get("data", [])
        if not fng_data:
            logger.warning("Fear & Greed 데이터 없음")
            return {"error": "데이터 없음"}

        current = fng_data[0]
        score = int(current.get("value", 0))
        rating = current.get("value_classification", "unknown")

        # 이전 데이터 (있으면)
        yesterday = int(fng_data[1]["value"]) if len(fng_data) > 1 else score
        week_ago = int(fng_data[6]["value"]) if len(fng_data) > 6 else score

        result = {
            "score": score,
            "rating": rating,
            "yesterday": yesterday,
            "one_week_ago": week_ago,
            "interpretation": _interpret_fear_greed(score),
        }
        logger.info(f"Fear & Greed Index 조회 완료: {score} ({rating})")
        return result
    except Exception as e:
        logger.error(f"Fear & Greed Index 조회 오류: {e}", exc_info=True)
        return {"error": str(e)}


def _interpret_fear_greed(score: float) -> str:
    """Fear & Greed 점수 해석"""
    if score <= 25:
        return "극단적 공포 - 매수 기회일 수 있음"
    elif score <= 45:
        return "공포 - 시장 불안정"
    elif score <= 55:
        return "중립 - 균형 잡힌 상태"
    elif score <= 75:
        return "탐욕 - 주의 필요"
    else:
        return "극단적 탐욕 - 과열 상태, 조정 가능성"


if __name__ == "__main__":
    mcp.run(transport="stdio")
