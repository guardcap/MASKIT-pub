"""
LLM Provider Factory
Ollama와 OpenAI를 자동으로 전환하는 팩토리 함수
"""
import os
from typing import Optional


def get_llm(model: str = "llama3", temperature: float = 0.0):
    """
    LLM 인스턴스를 반환하는 팩토리 함수

    모델명 형식:
    - Ollama: "llama3", "ollama:llama3", "ollama:mistral"
    - OpenAI: "gpt-4", "gpt-3.5-turbo", "openai:gpt-4"

    Args:
        model: 모델명 (provider:model 형식 또는 단순 모델명)
        temperature: 생성 온도 (0.0 = 결정적, 1.0 = 창의적)

    Returns:
        ChatOllama 또는 ChatOpenAI 인스턴스

    Examples:
        >>> llm = get_llm("llama3")  # Ollama
        >>> llm = get_llm("gpt-4")   # OpenAI
        >>> llm = get_llm("openai:gpt-4o")  # 명시적 provider
    """

    # Provider와 모델명 분리
    if ":" in model:
        provider, model_name = model.split(":", 1)
    else:
        # Provider가 명시되지 않은 경우 자동 감지
        if model.startswith("gpt-") or model.startswith("o1-"):
            provider = "openai"
            model_name = model
        else:
            provider = "ollama"
            model_name = model

    provider = provider.lower()

    if provider == "openai":
        return _get_openai_llm(model_name, temperature)
    elif provider == "ollama":
        return _get_ollama_llm(model_name, temperature)
    else:
        raise ValueError(
            f"지원하지 않는 LLM provider: {provider}\n"
            f"지원 provider: 'openai', 'ollama'"
        )


def _get_openai_llm(model: str, temperature: float):
    """OpenAI ChatGPT 모델 인스턴스 생성"""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "OpenAI를 사용하려면 langchain-openai 패키지가 필요합니다.\n"
            "설치: pip install langchain-openai"
        )

    # API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.\n"
            "export OPENAI_API_KEY=sk-..."
        )

    print(f"   - OpenAI 모델 사용: {model}")

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_key=api_key
    )


def _get_ollama_llm(model: str, temperature: float):
    """Ollama 로컬 모델 인스턴스 생성"""
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        raise ImportError(
            "Ollama를 사용하려면 langchain-ollama 패키지가 필요합니다.\n"
            "설치: pip install langchain-ollama"
        )

    print(f"   - Ollama 모델 사용: {model}")

    # Ollama 서버 URL (기본값: localhost:11434)
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    return ChatOllama(
        model=model,
        temperature=temperature,
        base_url=base_url
    )


# 지원 모델 목록 (참고용)
SUPPORTED_MODELS = {
    "ollama": [
        "llama3",
        "llama3:70b",
        "mistral",
        "mixtral",
        "codellama",
        "phi",
    ],
    "openai": [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-3.5-turbo",
        "o1-preview",
        "o1-mini",
    ]
}


def list_supported_models():
    """지원하는 모델 목록 출력"""
    print("\n📋 지원하는 LLM 모델:")
    print("\n🔷 Ollama (로컬):")
    for model in SUPPORTED_MODELS["ollama"]:
        print(f"   - {model}")
    print("\n🔷 OpenAI (API):")
    for model in SUPPORTED_MODELS["openai"]:
        print(f"   - {model}")
    print()


if __name__ == "__main__":
    # 테스트
    list_supported_models()

    # 사용 예시
    print("사용 예시:")
    print('  llm = get_llm("llama3")       # Ollama')
    print('  llm = get_llm("gpt-4")        # OpenAI')
    print('  llm = get_llm("openai:gpt-4") # 명시적')
