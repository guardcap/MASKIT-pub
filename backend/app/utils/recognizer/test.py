from app.utils.recognizer.MACaddress import MACRecognizer
if __name__ == "__main__":
    recognizer = MACRecognizer()
    
    text = """
    장치의 MAC 주소는 01:23:45:67:89:AB 입니다.
    다른 장치 맥주소 01-23-45-67-89-AB도 등록되어 있습니다.
    추가로 mac 12:34:56:78:9A:BC가 있습니다.
    """

    result = recognizer.analyze(text)

    print("인식된 MAC 엔티티:")
    for e in result.entities:
        print(f"Entity(entity='{e.entity}', score={e.score:.2f}, word='{e.word}', start={e.start}, end={e.end})")
