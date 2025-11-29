"""
PII 엔티티별 마스킹 규칙 정의
- 각 엔티티 타입에 대해 완전 마스킹과 부분 마스킹 방법을 정의
- 일관성 있고 표준화된 마스킹 적용
"""

from typing import Dict, Callable
import re


class MaskingRules:
    """엔티티별 마스킹 규칙을 정의하고 적용하는 클래스"""

    @staticmethod
    def mask_name_full(value: str) -> str:
        """이름 완전 마스킹: 모든 글자를 O으로 대체"""
        return 'O' * len(value)

    @staticmethod
    def mask_name_partial(value: str) -> str:
        """이름 부분 마스킹: 가운데 글자만 O으로 대체
        - 2글자: 김O
        - 3글자: 김O지
        - 4글자 이상: 첫글자 + O*(n-2) + 마지막글자
        """
        if len(value) <= 1:
            return 'O'
        elif len(value) == 2:
            return value[0] + 'O'
        elif len(value) == 3:
            return value[0] + 'O' + value[2]
        else:
            return value[0] + 'O' * (len(value) - 2) + value[-1]

    @staticmethod
    def mask_email_full(value: str) -> str:
        """이메일 완전 마스킹: ***@***.***"""
        return '***@***.***'

    @staticmethod
    def mask_email_partial(value: str) -> str:
        """이메일 부분 마스킹: 아이디 앞 2-3글자만 표시
        - example@domain.com -> exa***@domain.com
        """
        if '@' not in value:
            return '***@***.***'

        local, domain = value.split('@', 1)
        if len(local) <= 3:
            masked_local = local[0] + '***'
        else:
            masked_local = local[:3] + '***'

        return f"{masked_local}@{domain}"

    @staticmethod
    def mask_phone_full(value: str) -> str:
        """전화번호 완전 마스킹: ***-****-****"""
        return '***-****-****'

    @staticmethod
    def mask_phone_partial(value: str) -> str:
        """전화번호 부분 마스킹: 뒷 4자리만 표시
        - 010-1234-5678 -> ***-****-5678
        - 01012345678 -> *******5678
        """
        # 숫자만 추출
        digits = re.sub(r'\D', '', value)

        if len(digits) >= 4:
            if '-' in value:
                return f"***-****-{digits[-4:]}"
            else:
                return '*' * (len(digits) - 4) + digits[-4:]
        else:
            return '***-****-****'

    @staticmethod
    def mask_jumin_full(value: str) -> str:
        """주민등록번호 완전 마스킹: ******-*******"""
        return '******-*******'

    @staticmethod
    def mask_jumin_partial(value: str) -> str:
        """주민등록번호 부분 마스킹: 생년월일만 표시, 뒷자리 완전 마스킹
        - 901234-1234567 -> 901234-*******
        """
        if '-' in value:
            front = value.split('-')[0]
            return f"{front}-*******"
        elif len(value) == 13:
            return f"{value[:6]}-*******"
        else:
            return '******-*******'

    @staticmethod
    def mask_account_full(value: str) -> str:
        """계좌번호 완전 마스킹: ***-***-******"""
        return '***-***-******'

    @staticmethod
    def mask_account_partial(value: str) -> str:
        """계좌번호 부분 마스킹: 뒷 4자리만 표시
        - 123-456-789012 -> ***-***-**9012
        - 123456789012 -> ********9012
        """
        # 숫자만 추출
        digits = re.sub(r'\D', '', value)

        if len(digits) >= 4:
            if '-' in value:
                return f"***-***-**{digits[-4:]}"
            else:
                return '*' * (len(digits) - 4) + digits[-4:]
        else:
            return '***-***-******'

    @staticmethod
    def mask_passport_full(value: str) -> str:
        """여권번호 완전 마스킹: *********"""
        return '*' * 9

    @staticmethod
    def mask_passport_partial(value: str) -> str:
        """여권번호 부분 마스킹: 앞 2자리와 뒤 2자리만 표시
        - M12345678 -> M1*****78
        """
        if len(value) <= 4:
            return '*' * len(value)
        else:
            return value[:2] + '*' * (len(value) - 4) + value[-2:]

    @staticmethod
    def mask_driver_license_full(value: str) -> str:
        """운전면허번호 완전 마스킹: **-**-******-**"""
        return '**-**-******-**'

    @staticmethod
    def mask_driver_license_partial(value: str) -> str:
        """운전면허번호 부분 마스킹: 앞 지역코드만 표시
        - 11-12-345678-90 -> 11-**-******-**
        """
        parts = value.split('-')
        if len(parts) == 4:
            return f"{parts[0]}-**-******-**"
        else:
            return '**-**-******-**'

    @staticmethod
    def mask_address_full(value: str) -> str:
        """주소 완전 마스킹: [주소 마스킹]"""
        return '[주소 마스킹]'

    @staticmethod
    def mask_address_partial(value: str) -> str:
        """주소 부분 마스킹: 시/도 + 구/군까지만 표시
        - 서울시 강남구 역삼동 123-45 -> 서울시 강남구 ***
        """
        # 시/도와 구/군 추출
        parts = value.split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[1]} ***"
        elif len(parts) == 1:
            return f"{parts[0]} ***"
        else:
            return '[주소 마스킹]'

    @staticmethod
    def mask_company_full(value: str) -> str:
        """회사명 완전 마스킹: [회사명]"""
        return '[회사명]'

    @staticmethod
    def mask_company_partial(value: str) -> str:
        """회사명 부분 마스킹: 앞 2-3글자만 표시
        - 주식회사 ABC -> 주식***
        - ABC Corporation -> ABC***
        """
        if len(value) <= 3:
            return value[0] + '***'
        else:
            return value[:3] + '***'

    @staticmethod
    def mask_card_number_full(value: str) -> str:
        """카드번호 완전 마스킹: ****-****-****-****"""
        return '****-****-****-****'

    @staticmethod
    def mask_card_number_partial(value: str) -> str:
        """카드번호 부분 마스킹: 뒷 4자리만 표시
        - 1234-5678-9012-3456 -> ****-****-****-3456
        """
        # 숫자만 추출
        digits = re.sub(r'\D', '', value)

        if len(digits) >= 4:
            if '-' in value:
                return f"****-****-****-{digits[-4:]}"
            else:
                return '*' * (len(digits) - 4) + digits[-4:]
        else:
            return '****-****-****-****'

    # 엔티티 타입별 마스킹 함수 매핑
    MASKING_FUNCTIONS: Dict[str, Dict[str, Callable[[str], str]]] = {
        'name': {
            'full': mask_name_full.__func__,
            'partial': mask_name_partial.__func__,
        },
        'email': {
            'full': mask_email_full.__func__,
            'partial': mask_email_partial.__func__,
        },
        'phone': {
            'full': mask_phone_full.__func__,
            'partial': mask_phone_partial.__func__,
        },
        'jumin': {
            'full': mask_jumin_full.__func__,
            'partial': mask_jumin_partial.__func__,
        },
        'account': {
            'full': mask_account_full.__func__,
            'partial': mask_account_partial.__func__,
        },
        'passport': {
            'full': mask_passport_full.__func__,
            'partial': mask_passport_partial.__func__,
        },
        'driver_license': {
            'full': mask_driver_license_full.__func__,
            'partial': mask_driver_license_partial.__func__,
        },
        'address': {
            'full': mask_address_full.__func__,
            'partial': mask_address_partial.__func__,
        },
        'company': {
            'full': mask_company_full.__func__,
            'partial': mask_company_partial.__func__,
        },
        'card_number': {
            'full': mask_card_number_full.__func__,
            'partial': mask_card_number_partial.__func__,
        },
        # 대문자 영어명 매핑 (PII 탐지 모듈 호환성)
        'person': {
            'full': mask_name_full.__func__,
            'partial': mask_name_partial.__func__,
        },
        'resident_id': {
            'full': mask_jumin_full.__func__,
            'partial': mask_jumin_partial.__func__,
        },
        'organization': {
            'full': mask_company_full.__func__,
            'partial': mask_company_partial.__func__,
        },
        'bank_account': {
            'full': mask_account_full.__func__,
            'partial': mask_account_partial.__func__,
        },
    }

    @classmethod
    def apply_masking(cls, value: str, entity_type: str, masking_level: str = 'full') -> str:
        """
        엔티티 타입과 마스킹 레벨에 따라 마스킹 적용

        Args:
            value: 원본 값
            entity_type: PII 엔티티 타입 (name, email, phone 등)
            masking_level: 마스킹 수준 ('full' 또는 'partial')

        Returns:
            마스킹된 값
        """
        # 소문자로 변환하여 대소문자 구분 없이 처리
        entity_type_lower = entity_type.lower()

        # 엔티티 타입이 없으면 기본 마스킹
        if entity_type_lower not in cls.MASKING_FUNCTIONS:
            print(f"⚠️ 알 수 없는 엔티티 타입: {entity_type}, 기본 마스킹 적용")
            return '***'

        # 마스킹 레벨 검증
        if masking_level not in ['full', 'partial']:
            print(f"⚠️ 알 수 없는 마스킹 레벨: {masking_level}, 완전 마스킹 적용")
            masking_level = 'full'

        # 해당 마스킹 함수 가져오기
        masking_func = cls.MASKING_FUNCTIONS[entity_type_lower][masking_level]

        try:
            masked_value = masking_func(value)
            print(f"✅ 마스킹 적용: {entity_type} ({masking_level}) - {value} -> {masked_value}")
            return masked_value
        except Exception as e:
            print(f"❌ 마스킹 적용 실패: {entity_type} - {value}, 오류: {e}")
            return '***'

    @classmethod
    def get_available_entity_types(cls) -> list:
        """사용 가능한 엔티티 타입 목록 반환"""
        return list(cls.MASKING_FUNCTIONS.keys())


# 사용 예시 및 테스트
if __name__ == "__main__":
    print("=== 마스킹 규칙 테스트 ===\n")

    test_cases = [
        ('김민지', 'name', 'full'),
        ('김민지', 'name', 'partial'),
        ('example@gmail.com', 'email', 'full'),
        ('example@gmail.com', 'email', 'partial'),
        ('010-1234-5678', 'phone', 'full'),
        ('010-1234-5678', 'phone', 'partial'),
        ('901234-1234567', 'jumin', 'full'),
        ('901234-1234567', 'jumin', 'partial'),
        ('123-456-789012', 'account', 'full'),
        ('123-456-789012', 'account', 'partial'),
        ('서울시 강남구 역삼동 123-45', 'address', 'full'),
        ('서울시 강남구 역삼동 123-45', 'address', 'partial'),
    ]

    for value, entity_type, level in test_cases:
        masked = MaskingRules.apply_masking(value, entity_type, level)
        print(f"{entity_type:15s} ({level:7s}): {value:30s} -> {masked}")

    print(f"\n사용 가능한 엔티티 타입: {MaskingRules.get_available_entity_types()}")
