from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import SpacyNlpEngine, NlpEngine, NlpEngineProvider
import spacy
from presidio_analyzer import PatternRecognizer

# 예시: 한국어 모델 or 커스텀 모델
nlp_model = spacy.load("ko_core_news_sm")  # 또는 커스텀 경로

custom_nlp_engine = SpacyNlpEngine()
custom_nlp_engine.nlp = {"ko": nlp_model}  

analyzer = AnalyzerEngine(
    nlp_engine=custom_nlp_engine,
    supported_languages=["ko"]
)

recognizer = PatternRecognizer(
    supported_entity="KOREAN_PHONE_NUMBER",
    patterns=[
        {"name": "ko_phone", "regex": r"\b01[016789]-?\d{3,4}-?\d{4}\b", "score": 0.85}
    ],
    context=["전화", "휴대폰"]
)
analyzer.registry.add_recognizer(recognizer)

text = "홍길동의 전화번호는 010-1234-5678입니다."
results = analyzer.analyze(text=text, language="ko")

for res in results:
    print(f"{res.entity_type}: {text[res.start:res.end]} (score={res.score})")