CREATE TABLE articles (
  id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  article_id     VARCHAR(20) NOT NULL UNIQUE, -- 네이버 article_id
  office_id      VARCHAR(10),
  title          TEXT NOT NULL,
  url            TEXT NOT NULL,
  press          VARCHAR(100),
  published_date TIMESTAMP NOT NULL,
  content        TEXT NOT NULL
);

CREATE TABLE clusters (
  id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_date     DATE NOT NULL, -- 파이프라인 실행 날짜
  cluster_seq  INT NOT NULL,  -- 파이프라인 내 cluster_id (1, 2)
  size         INT NOT NULL,
  is_singleton BOOLEAN NOT NULL DEFAULT FALSE,
  created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(run_date, cluster_seq)
);

CREATE TABLE cluster_articles (
  cluster_id             BIGINT NOT NULL REFERENCES clusters(id) ON DELETE CASCADE,
  article_id             BIGINT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  similarity_to_centroid FLOAT,
  PRIMARY KEY (cluster_id, article_id)
);

CREATE TABLE entity_extraction (
  id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  cluster_id    BIGINT NOT NULL REFERENCES clusters(id) ON DELETE CASCADE,
  company_names TEXT[] NOT NULL DEFAULT '{}',  -- KRX 기준 정규화 법인명
  sectors       TEXT[] NOT NULL DEFAULT '{}',
  keywords      TEXT[] NOT NULL DEFAULT '{}',
  UNIQUE(cluster_id)  -- 클러스터당 1개 추출 결과
);

CREATE TABLE company_master (
  id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  krx_code   VARCHAR(6) UNIQUE NOT NULL,
  dart_code  VARCHAR(8) UNIQUE,
  krx_name   VARCHAR(100) NOT NULL,
  dart_name  VARCHAR(100),
  sector     VARCHAR(50),                     -- KRX 업종명 (전기·전자, 화학 등)
  market     VARCHAR(10) CHECK (market IN ('KOSPI', 'KOSDAQ')),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE dart_financial_statements (
  id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  company_id        BIGINT NOT NULL REFERENCES company_master(id) ON DELETE CASCADE,
  fiscal_year       SMALLINT NOT NULL,
  fs_div            VARCHAR(5) NOT NULL CHECK (fs_div IN ('CFS', 'OFS')),
  rcept_no          VARCHAR(20) NOT NULL,     -- DART 접수번호
  reprt_code        VARCHAR(10) NOT NULL,     -- 11011(사업) | 11012(반기) | 11013(1Q) | 11014(3Q)
  revenue           BIGINT,                  -- 매출액
  operating_income  BIGINT,                  -- 영업이익
  income_before_tax BIGINT,                  -- 법인세차감전순이익
  net_income        BIGINT,                  -- 당기순이익
  current_assets    BIGINT,                  -- 유동자산
  total_assets      BIGINT,                  -- 자산총계
  current_liabilities BIGINT,               -- 유동부채
  total_liabilities BIGINT,                 -- 부채총계
  capital_stock     BIGINT,                 -- 자본금
  retained_earnings BIGINT,                 -- 이익잉여금
  total_equity      BIGINT,                 -- 자본총계
  currency          VARCHAR(5) NOT NULL DEFAULT 'KRW',
  updated_at        TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(company_id, fiscal_year, fs_div, reprt_code)
);

CREATE TABLE dart_document (
  id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  company_id    BIGINT NOT NULL REFERENCES company_master(id) ON DELETE CASCADE,
  document_type VARCHAR(20) NOT NULL
                CHECK (document_type IN ('business_report', 'quarterly_report')),
  fiscal_year   SMALLINT NOT NULL,
  period_type   VARCHAR(10) NOT NULL
                CHECK (period_type IN ('annual', 'q1', 'q2', 'q3')),
  section       TEXT NOT NULL,               -- 사업의 내용, 연구개발활동 등
  subsection    TEXT NOT NULL DEFAULT '',
  content       TEXT NOT NULL,
  embedding     vector(768),                 -- pgvector RAG 검색용
  source        VARCHAR(20) NOT NULL DEFAULT 'DART',
  source_url    TEXT,
  created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(company_id, fiscal_year, section, subsection)
);

-- articles: 날짜 조회, 벡터 검색
CREATE INDEX ON articles(published_date DESC);
-- CREATE INDEX ON articles USING hnsw (embedding vector_cosine_ops);  -- pgvector

-- clusters: 날짜 조회
CREATE INDEX ON clusters(run_date DESC);

-- cluster_articles: 클러스터별 기사 조회
CREATE INDEX ON cluster_articles(cluster_id);

-- entity_extraction: 클러스터 조회
CREATE INDEX ON entity_extraction(cluster_id);

-- dart_financial_statements: 종목별 연도 조회
CREATE INDEX ON dart_financial_statements(company_id, fiscal_year DESC);

-- dart_document: 종목별 벡터 검색
CREATE INDEX ON dart_document(company_id);
CREATE INDEX ON dart_document USING hnsw (embedding vector_cosine_ops);  -- pgvector
