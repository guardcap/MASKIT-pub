from app.utils.analyzer_engine import AnalyzerEngine

if __name__ == "__main__":

    text = "홍길동의 이메일은 gildong@example.com 이고, IP는 192.168.0.1 입니다. 계좌번호는 123-456-789012 입니다."
    engine = AnalyzerEngine()
    group = engine.analyze(text)

    # 마스킹 등에서 바로 사용 가능
    for ent in group.entities:
        print(ent)
