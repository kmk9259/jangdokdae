## 환경 설정

```bash
# 저장소 루트에서
cp .env.example .env
```

`.env` 파일에 아래 키를 채워 넣습니다.

| 변수 | 필수 | 설명 |
|---|---|---|
| `GEMINI_API_KEY` | ✅ | 엔티티 추출(LLM) |
| `LLM_MODEL` | ✅ | 사용할 Gemini 모델명 (예: `gemini-2.0-flash-lite`) |
| `EMBED_MODEL` | ✅ | Sentence-Transformer 모델명 (예: `jhgan/ko-sroberta-multitask`) |
| `OPENDART_API_KEY` | ✅ | DART 공시·재무제표 조회 |
| `KRX_ID` | ⬜ | KRX 로그인 ID (투자자별 거래량 조회 시 필요) |
| `KRX_PASSWORD` | ⬜ | KRX 로그인 비밀번호 |
| `OPENAI_API_KEY` | ⬜ | 현재 미사용 |

## 패키지 설치

```bash
pip install \
  requests beautifulsoup4 lxml \
  pykrx OpenDartReader yfinance \
  sentence-transformers torch \
  umap-learn hdbscan \
  langchain-core langchain-google-genai \
  pydantic pandas numpy \
  matplotlib scikit-learn
```

> Mac(Apple Silicon)에서는 `torch` 설치 후 MPS 가속이 자동으로 활성화됩니다.

## 실행

### 파이프라인 실행

```bash
# 오늘 날짜 기준, 기사 최대 50개
python -m apps.scripts.collector_pipeline

# 특정 날짜 지정
python -m apps.scripts.collector_pipeline --date 20260511

# 수집 기사 수 조정
python -m apps.scripts.collector_pipeline --limit 100
```

### 클러스터 품질 평가

```bash
python -m apps.scripts.evaluate_clusters

# 특정 결과 파일 지정
python -m apps.scripts.evaluate_clusters --file apps/data/20260511_153000/news_clusters.json
```

### 클러스터 시각화

```bash
python -m apps.scripts.visualize_clusters

# 특정 결과 파일 지정
python -m apps.scripts.visualize_clusters --file apps/data/20260511_153000/news_clusters.json
```

PNG 3종이 같은 디렉토리에 생성됩니다: `scatter.png`, `sizes.png`, `cohesion.png`

## 파이프라인 구조

각 단계는 순차 실행되며, `apps/data/{YYYYMMDD_HHMMSS}/` 폴더에 중간 결과를 저장합니다.

| 단계 | 출력 파일 | 실패 시 |
|---|---|---|
| 1. 뉴스 수집 | `news_crawled.json` | 중단 |
| 2. 뉴스 전처리 | — | 중단 |
| 3. 임베딩 | — | 중단 |
| 4. 클러스터링 | `news_clusters.json` | 중단 |
| 5. 엔티티 추출 (LLM) | `clusters_extracted.json` | 계속 |
| 6. 기업 데이터 수집 | — | 계속 |
| 7. 기업 데이터 전처리 | — | 계속 |
| 8. 거시지표 수집 | `clusters_final.json` | 계속 |

## 프로젝트 구조

```
apps/
├── scripts/
│   ├── collector_pipeline.py   # 파이프라인 진입점
│   ├── evaluate_clusters.py    # 클러스터 품질 평가
│   └── visualize_clusters.py   # 클러스터 시각화
└── src/
    ├── config/                 # 전역 상수 (섹터 목록, 경로, ticker 등)
    ├── utils/                  # 공통 유틸 (날짜, JSON, HTTP 재시도)
    ├── models/                 # DTO
    ├── prompts/                # LLM 프롬프트 템플릿
    └── services/
        ├── collector/          # 뉴스·KRX·DART·거시지표 수집
        ├── embedder/           # 임베딩 + UMAP/HDBSCAN 클러스터링
        ├── extractor/          # Gemini 기반 엔티티 추출
        └── preprocessor/       # 뉴스·기업·DART 데이터 전처리
```
