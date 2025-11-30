from app.utils.recognizer_registry import RecognizerRegistry

if __name__ == "__main__":

    registry = RecognizerRegistry()
    registry.load_predefined_recognizers()
    test_text = """안녕하세요. 저는 김철수라고 합니다. 서울에 있는 삼성전자에서 일해요. 제 전화번호는 010-1234-5678이고, 이메일은 test@example.com입니다. 내일 오후 3시에 010-1234-5678로 전화 줘. 
    이곳의 위치 좌표는 37.5665, 126.9780 입니다.
    다른 예시로는 위도: 35.1796,경도: 129.0756 이 있습니다.
    이메일은 test@example.com이고
    참고로 28891058191007이고, 카드번호는 1234-5678-9012-3456이야.
    내 운전면허 번호는 11-23-456789-01이고, 여권번호는 M12345678이야. 
    주민등록번호는 900101-1234567이야. 
    그리고 집에 있는 컴퓨터 IP는 192.168.1.1이고, MAC 주소는 00-1B-63-84-45-E6이야."""
    
    analysis_results = registry.regex_analyze(test_text)
    
    print(analysis_results )
