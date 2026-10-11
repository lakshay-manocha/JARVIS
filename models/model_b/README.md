# JARVIS-StateMismatch-v1.0: Stored-State vs Current-State Mismatch Classifier

## Research Objective
Independent binary classifier predicting whether a stored workflow environment state and a current environment state contain a material mismatch ($P(\text{mismatch} \mid \text{stored\_state}, \text{current\_state})$).
Trained strictly with ZERO synthetic data using real observed states from the OSWorld and Mind2Web benchmarks.

## Architecture
- Pretrained Encoder: `sentence-transformers/all-MiniLM-L6-v2` (genuinely fine-tuned end-to-end)
- Pair Representation: $[u, v, |u - v|, u \odot v] \in \mathbb{R}^{1536}$
- Classification Head: Linear(1536, 256) -> ReLU -> Dropout(0.2) -> Linear(256, 64) -> ReLU -> Dropout(0.2) -> Linear(64, 1)
- Validation Selected Threshold: 0.30

## Test Set Evaluation
- Accuracy: 0.9848
- Precision: 1.0000
- Recall: 0.9697
- F1 Score: 0.9846
- ROC-AUC: 0.9949

## Exact Python API
```python
from predictor import predict_state_mismatch

result = predict_state_mismatch(stored_state, current_state)
print(result)
```
