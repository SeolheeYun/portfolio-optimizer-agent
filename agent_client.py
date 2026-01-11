"""
포트폴리오 투자 비율 결정 Agent
MCP 서버를 통해 데이터를 수집하고 투자 비율을 제안
"""
import os
import asyncio
import yaml
import logging
from dotenv import load_dotenv

from langchain_mcp_adapters.client import MultiServerMCPClient

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("agent_client")
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()


def load_portfolio():
    """portfolio.yaml 로드"""
    logger.info("포트폴리오 파일 로드 중...")
    with open("portfolio.yaml", "r", encoding="utf-8") as f:
        portfolio = yaml.safe_load(f)
    logger.info("포트폴리오 파일 로드 완료")
    return portfolio


def build_system_prompt(portfolio: dict) -> str:
    """포트폴리오 기반 시스템 프롬프트 생성"""
    stocks = [f"{s['symbol']} ({s['name']})" for s in portfolio.get("stocks", [])]
    crypto = [f"{c['symbol']} ({c['name']})" for c in portfolio.get("crypto", [])]
    bonds = [f"{b['symbol']} ({b['name']})" for b in portfolio.get("bonds", [])]
    gold = [f"{g['symbol']} ({g['name']})" for g in portfolio.get("gold", [])]

    return f"""당신은 데이터 기반 포트폴리오 투자 비율을 결정하는 투자 어드바이저입니다.

## 투자 유니버스
- 주식 (위험자산): {', '.join(stocks)}
- 암호화폐 (고위험자산): {', '.join(crypto)}
- 채권 (안전자산): {', '.join(bonds)}
- 금 (안전자산/인플레이션 헷지): {', '.join(gold)}

## 분석 프로세스
사용자가 투자 비율을 요청하면 반드시 다음 순서로 진행하세요:

### 1단계: 데이터 수집
- `get_all_prices`: 모든 자산의 가격/수익률 조회
- `get_market_summary`: 환율, 공포탐욕지수 조회

### 2단계: 시장 상황 판단
수집된 데이터를 기반으로 현재 시장 국면을 판단하세요:
- **Risk-On (위험선호)**: 공포탐욕지수 50 이상, 주식 상승세 → 주식/암호화폐 비중 확대
- **Risk-Off (위험회피)**: 공포탐욕지수 50 미만, 변동성 확대 → 채권/금 비중 확대
- **인플레이션 우려**: 금 가격 상승세 → 금 비중 확대
- **달러 강세**: 환율 상승 → 해외자산 신중, 원화자산 고려

### 3단계: 비율 결정 가이드라인
| 시장 국면 | 주식 | 암호화폐 | 채권 | 금 |
|-----------|------|----------|------|-----|
| 강한 Risk-On | 50-60% | 15-20% | 15-20% | 5-10% |
| 약한 Risk-On | 40-50% | 10-15% | 25-30% | 10-15% |
| 중립 | 35-40% | 5-10% | 35-40% | 15-20% |
| 약한 Risk-Off | 25-35% | 0-5% | 40-50% | 20-25% |
| 강한 Risk-Off | 15-25% | 0% | 45-55% | 25-30% |

## 응답 형식
```
## 시장 현황 요약
(수집된 데이터 요약)

## 시장 국면 판단
(현재 시장 국면과 근거)

## 추천 투자 비율
| 자산군 | 비율 | 사유 |
|--------|------|------|
| 주식 | X% | ... |
| 암호화폐 | Y% | ... |
| 채권 | Z% | ... |
| 금 | W% | ... |
| **합계** | **100%** | |

## 주의사항
(현재 시장의 주요 리스크 요인)
```

## 중요 규칙
1. 반드시 도구를 호출하여 실시간 데이터를 수집한 후 분석하세요.
2. 비율의 합은 반드시 100%여야 합니다.
3. 한국어로 응답하세요.
4. 이 조언은 참고용이며, 실제 투자 결정은 사용자의 판단과 책임입니다.
"""


async def main():
    print("=" * 50)
    print("포트폴리오 투자 비율 결정 Agent")
    print("=" * 50)

    # 포트폴리오 로드
    portfolio = load_portfolio()
    print(f"\n[포트폴리오 로드 완료]")
    print(f"  - 주식: {len(portfolio.get('stocks', []))}개")
    print(f"  - 암호화폐: {len(portfolio.get('crypto', []))}개")
    print(f"  - 채권: {len(portfolio.get('bonds', []))}개")
    print(f"  - 금: {len(portfolio.get('gold', []))}개")

    # MCP 서버 연결
    server_connections = {
        "quantitative": {
            "transport": "stdio",
            "command": "python",
            "args": ["quantitative_server.py"]
        },
        "qualitative": {
            "transport": "stdio",
            "command": "python",
            "args": ["qualitative_server.py"]
        },
    }

    print("\n[MCP 서버 연결 중...]")
    logger.info("MCP 서버 연결 시작")
    logger.debug(f"서버 설정: {server_connections}")

    # langchain-mcp-adapters 0.1.0+: get_tools()가 내부적으로 세션 관리
    client = MultiServerMCPClient(server_connections)
    tools = await client.get_tools()
    tool_names = [t.name for t in tools]
    logger.info(f"MCP 도구 로드 완료: {tool_names}")
    print(f"[도구 로드 완료] {tool_names}")

    # Agent 생성
    logger.info("LLM 및 Agent 초기화 중...")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = create_react_agent(llm, tools)
    system_prompt = build_system_prompt(portfolio)
    logger.info("Agent 초기화 완료")

    print("\n" + "=" * 50)
    print("대화를 시작합니다. (종료: quit)")
    print("예시: '현재 시장 상황을 분석하고 투자 비율을 추천해줘'")
    print("=" * 50 + "\n")

    while True:
        user_input = input("[질문]: ").strip()

        if not user_input or user_input.lower() in ["quit", "exit", "종료"]:
            logger.info("사용자가 종료 요청")
            print("종료합니다.")
            break

        try:
            logger.info(f"사용자 질문 수신: {user_input[:50]}...")
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input)
            ]
            logger.debug("Agent 호출 시작")
            response = await agent.ainvoke({"messages": messages})
            final_response = response["messages"][-1].content
            logger.info("Agent 응답 생성 완료")
            logger.debug(f"응답 길이: {len(final_response)} 문자")
            print(f"\n[답변]:\n{final_response}\n")

        except Exception as e:
            logger.error(f"Agent 처리 중 오류 발생: {e}", exc_info=True)
            print(f"[오류]: {e}\n")


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("[오류] OPENAI_API_KEY가 설정되지 않았습니다.")
        print("  .env 파일에 OPENAI_API_KEY를 추가하세요.")
        exit(1)

    asyncio.run(main())
