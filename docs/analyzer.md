# Analyzer

수집/가공 파트가 넘겨주는 기사 JSON을 받아 핵심 이슈와 요약 재료를 구조화하는 분석 단계입니다.

## 입력

- `article_id`
- `title`
- `summary_hint`
- `content`
- `metadata.company_names`
- `metadata.sectors`
- `metadata.keywords`

## 출력

- `news_type`
- `primary_issue_id`
- `summary`
- `issue_candidates`
- `summary_points`
- `coverage_check`

## 흐름

1. 기사 유형 분류
2. `issue_candidates` 생성
3. `primary_issue` 선정
4. `summary_points` 생성
5. `summary` 종합

## 연결 의미

- 앞단 수집/가공 → analyzer
- analyzer → content 생성

즉 analyzer는 단순 요약기보다, 콘텐츠 생성 전 단계의 분석 레이어로 설명하는 것이 적절합니다.
