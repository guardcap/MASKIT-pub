---
language: 
  - multilingual
  - af
  - am
  - ar
  - as
  - az
  - be
  - bg
  - bn
  - br
  - bs
  - ca
  - cs
  - cy
  - da
  - de
  - el
  - en
  - eo
  - es
  - et
  - eu
  - fa
  - fi
  - fr
  - fy
  - ga
  - gd
  - gl
  - gu
  - ha
  - he
  - hi
  - hr
  - hu
  - hy
  - id
  - is
  - it
  - ja
  - jv
  - ka
  - kk
  - km
  - kn
  - ko
  - ku
  - ky
  - la
  - lo
  - lt
  - lv
  - mg
  - mk
  - ml
  - mn
  - mr
  - ms
  - my
  - ne
  - nl
  - 'no'
  - om
  - or
  - pa
  - pl
  - ps
  - pt
  - ro
  - ru
  - sa
  - sd
  - si
  - sk
  - sl
  - so
  - sq
  - sr
  - su
  - sv
  - sw
  - ta
  - te
  - th
  - tl
  - tr
  - ug
  - uk
  - ur
  - uz
  - vi
  - xh
  - yi
  - zh
license: mit
library_name: sentence-transformers
tags:
  - korean
  - sentence-transformers
  - transformers
  - multilingual
  - sentence-transformers
  - sentence-similarity
  - feature-extraction
base_model: intfloat/multilingual-e5-base
datasets: []
metrics:
- pearson_cosine
- spearman_cosine
- pearson_manhattan
- spearman_manhattan
- pearson_euclidean
- spearman_euclidean
- pearson_dot
- spearman_dot
- pearson_max
- spearman_max
widget:
- source_sentence: 이집트 군대가 형제애를 단속하다
  sentences:
  - 이집트의 군대가 무슬림 형제애를 단속하다
  - 아르헨티나의 기예르모 코리아와 네덜란드의 마틴 버커크의 또 다른 준결승전도 매력적이다.
  - 그것이 사실일 수도 있다고 생각하는 것은 재미있다.
- source_sentence: 오, 그리고 다시 결혼은 근본적인 인권이라고 주장한다.
  sentences:
  - 특히 결혼은 근본적인 인권이라고 말한 후에.
  - 해변에 있는 흑인과 그의 개...
  - 이란은 핵 프로그램이 평화적인 목적을 위한 것이라고 주장한다
- source_sentence: 담배 피우는 여자.
  sentences:
  - 이것은 내가 영국의 아서 안데르센 사업부의 파트너인 짐 와디아를 아서 안데르센 경영진이 선택한 것보다 래리 웨인바흐를 안데르센 월드와이드의
    경영 파트너로 승계하기 위해 안데르센 컨설팅 사업부(현재의 엑센츄어라고 알려져 있음)의 전 관리 파트너인 조지 샤힌에 대한 지지를 표명했을
    때 가장 명백했다.
  - 한 여자가 물 한 잔을 마시고 있다.
  - 한 여성이 담배를 피우면서 청구서를 지불하는 것을 압도했다.
- source_sentence: 루이 15세의 소수 민족인 프랑스의 리젠트인 필리프 도를레앙 시대에는 악명 높은 오르가즘의 현장이었다.
  sentences:
  - 필립 도린스는 루이 15세가 70대였을 때 섭정이었다.
  - 행복한 어린 소년이 커다란 엘모 인형이 있는 의자에 앉아 있다.
  - 필리프 도를레앙 시대에는 그곳에서 많은 유명한 오르가즘이 일어났다.
- source_sentence: 두 남자가 안에서 일하고 있다
  sentences:
  - 국립공원에서 가장 큰 마을인 케스윅의 인구는 매년 여름 등산객, 뱃사람, 관광객이 도착함에 따라 증가한다.
  - 두 남자가 축구 경기를 보고 간식을 먹는다.
  - 두 남자가 집에 타일을 깔았다.
pipeline_tag: sentence-similarity
model-index:
- name: upskyy/e5-base-korean
  results:
  - task:
      type: semantic-similarity
      name: Semantic Similarity
    dataset:
      name: sts dev
      type: sts-dev
    metrics:
    - type: pearson_cosine
      value: 0.8593935914692068
      name: Pearson Cosine
    - type: spearman_cosine
      value: 0.8572594228080116
      name: Spearman Cosine
    - type: pearson_manhattan
      value: 0.8217336375412545
      name: Pearson Manhattan
    - type: spearman_manhattan
      value: 0.8280050978871264
      name: Spearman Manhattan
    - type: pearson_euclidean
      value: 0.8208931119126335
      name: Pearson Euclidean
    - type: spearman_euclidean
      value: 0.8277058727421436
      name: Spearman Euclidean
    - type: pearson_dot
      value: 0.8187961699085111
      name: Pearson Dot
    - type: spearman_dot
      value: 0.8236175658758088
      name: Spearman Dot
    - type: pearson_max
      value: 0.8593935914692068
      name: Pearson Max
    - type: spearman_max
      value: 0.8572594228080116
      name: Spearman Max
---

# upskyy/e5-base-korean

This model is korsts and kornli finetuning model from [intfloat/multilingual-e5-base](https://huggingface.co/intfloat/multilingual-e5-base). It maps sentences & paragraphs to a 768-dimensional dense vector space and can be used for semantic textual similarity, semantic search, paraphrase mining, text classification, clustering, and more.

## Model Details

### Model Description
- **Model Type:** Sentence Transformer
- **Base model:** [intfloat/multilingual-e5-base](https://huggingface.co/intfloat/multilingual-e5-base) <!-- at revision d13f1b27baf31030b7fd040960d60d909913633f -->
- **Maximum Sequence Length:** 512 tokens
- **Output Dimensionality:** 768 tokens
- **Similarity Function:** Cosine Similarity
<!-- - **Training Dataset:** Unknown -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->


### Full Model Architecture

```
SentenceTransformer(
  (0): Transformer({'max_seq_length': 512, 'do_lower_case': False}) with Transformer model: XLMRobertaModel 
  (1): Pooling({'word_embedding_dimension': 768, 'pooling_mode_cls_token': False, 'pooling_mode_mean_tokens': True, 'pooling_mode_max_tokens': False, 'pooling_mode_mean_sqrt_len_tokens': False, 'pooling_mode_weightedmean_tokens': False, 'pooling_mode_lasttoken': False, 'include_prompt': True})
)
```


## Usage

### Usage (Sentence-Transformers)


First install the Sentence Transformers library:

```bash
pip install -U sentence-transformers
```

Then you can load this model and run inference.
```python
from sentence_transformers import SentenceTransformer

# Download from the 🤗 Hub
model = SentenceTransformer("upskyy/e5-base-korean")

# Run inference
sentences = [
    '아이를 가진 엄마가 해변을 걷는다.',
    '두 사람이 해변을 걷는다.',
    '한 남자가 해변에서 개를 산책시킨다.',
]
embeddings = model.encode(sentences)
print(embeddings.shape)
# [3, 768]

# Get the similarity scores for the embeddings
similarities = model.similarity(embeddings, embeddings)
print(similarities.shape)
# [3, 3]
```

### Usage (HuggingFace Transformers)

Without sentence-transformers, you can use the model like this: 
First, you pass your input through the transformer model, then you have to apply the right pooling-operation on-top of the contextualized word embeddings.

```python
from transformers import AutoTokenizer, AutoModel
import torch


# Mean Pooling - Take attention mask into account for correct averaging
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] # First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


# Sentences we want sentence embeddings for
sentences = ["안녕하세요?", "한국어 문장 임베딩을 위한 버트 모델입니다."]

# Load model from HuggingFace Hub
tokenizer = AutoTokenizer.from_pretrained("upskyy/e5-base-korean")
model = AutoModel.from_pretrained("upskyy/e5-base-korean")

# Tokenize sentences
encoded_input = tokenizer(sentences, padding=True, truncation=True, return_tensors="pt")

# Compute token embeddings
with torch.no_grad():
    model_output = model(**encoded_input)

# Perform pooling. In this case, mean pooling.
sentence_embeddings = mean_pooling(model_output, encoded_input["attention_mask"])

print("Sentence embeddings:")
print(sentence_embeddings)
```


## Evaluation

### Metrics

#### Semantic Similarity
* Dataset: `sts-dev`
* Evaluated with [<code>EmbeddingSimilarityEvaluator</code>](https://sbert.net/docs/package_reference/sentence_transformer/evaluation.html#sentence_transformers.evaluation.EmbeddingSimilarityEvaluator)

| Metric             | Value      |
| :----------------- | :--------- |
| pearson_cosine     | 0.8594     |
| spearman_cosine    | 0.8573     |
| pearson_manhattan  | 0.8217     |
| spearman_manhattan | 0.828      |
| pearson_euclidean  | 0.8209     |
| spearman_euclidean | 0.8277     |
| pearson_dot        | 0.8188     |
| spearman_dot       | 0.8236     |
| **pearson_max**    | **0.8594** |
| **spearman_max**   | **0.8573** |

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

### Framework Versions
- Python: 3.10.13
- Sentence Transformers: 3.0.1
- Transformers: 4.42.4
- PyTorch: 2.3.0+cu121
- Accelerate: 0.30.1
- Datasets: 2.16.1
- Tokenizers: 0.19.1

## Citation

### BibTeX


```bibtex
@article{wang2024multilingual,
  title={Multilingual E5 Text Embeddings: A Technical Report},
  author={Wang, Liang and Yang, Nan and Huang, Xiaolong and Yang, Linjun and Majumder, Rangan and Wei, Furu},
  journal={arXiv preprint arXiv:2402.05672},
  year={2024}
}
```

```bibtex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
```
