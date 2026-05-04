# Cluster Processing Flow

`cluster input`
→ `LangGraph workflow`
→ `representative 기사 선택`
→ `AnalysisRequest 정규화`
→ `LangChain structured output`
→ `Gemini on Vertex AI or Gemini API`
→ `AnalysisResponse`
→ `rules fallback if needed`
→ `downstream content generation`
