import os
import subprocess

# 현재 실행 위치 (app/test)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join("data", "policy.md")  # 현재 위치 기준
chunk_script = "chunk_and_save.py"
eval_script = "evalute_chunking.py"

models = {
    "upskyy_e5": "upskyy/e5-base-korean",
    "kosimcse": "BM-K/KoSimCSE-roberta-multitask",
    "multilingual_e5": "intfloat/multilingual-e5-base",
}

def run_chunk_and_save(model_name: str, model_path: str):
    print(f"\n🟦 Running chunk_and_save.py with {model_name} ({model_path})")
    subprocess.run(
        ["python3", chunk_script,
         "--input", data_path,
         "--output", os.path.join("vectors", model_name),
         "--model", model_path]
    )

def run_evaluate(model_name: str):
    print(f"\n🟩 Evaluating with {model_name}")
    subprocess.run(
        ["python3", eval_script,
         "--vectorstore", os.path.join("vectors", model_name)]
    )

if __name__ == "__main__":
    for model_name, model_path in models.items():
        run_chunk_and_save(model_name, model_path)
        run_evaluate(model_name)
