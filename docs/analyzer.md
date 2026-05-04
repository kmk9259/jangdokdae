# Analyzer

수집/가공 파트가 넘겨주는 기사 또는 클러스터 JSON을 받아 핵심 이슈와 요약 재료를 구조화하는 분석 단계입니다.

## 입력

### 단일 기사 입력

- `article_id`
- `title`
- `summary_hint`
- `content`
- `metadata.company_names`
- `metadata.sectors`
- `metadata.keywords`

### 클러스터 입력

- `clusters[].cluster.representative_news_id`
- `clusters[].news[]`
- `clusters[].company[]`
- `clusters[].cluster.sector`
- `clusters[].cluster.keyword`

## LangChain / LangGraph 적용 위치

### LangChain

- 적용 위치: analyzer 내부 LLM 호출부
- 역할: Gemini 응답을 `AnalysisResponse` 구조로 안정적으로 받기

### LangGraph

- 적용 위치: 클러스터 배치 처리부
- 역할: 대표 기사 선택, 입력 정규화, 분석 실행, 결과 반환을 단계별로 관리

## 전체 흐름

1. 수집/가공 파트가 기사 또는 클러스터 입력 전달
2. 클러스터인 경우 representative 기사 선택
3. analyzer 입력 형태로 정규화
4. LangChain 기반 Gemini 호출
5. 실패 시 기존 rules fallback
6. 구조화 결과를 downstream content 생성 파트로 전달

## GCP Vertex 실행

1. `pip install -r requirements.txt`
2. `.env.example` 값을 기준으로 환경변수 설정
3. Vertex 인증 준비
4. `uvicorn main:app --reload`
5. `python apps/scripts/gcp_cluster_smoke.py`

실제 cluster 입력을 받아 analyzer를 돌리는 운영 경로에는 `sample_data.py`가 필요하지 않습니다.
