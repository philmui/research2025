# MemAgent Project

This project aims to study various short term and long term memory strategies for agents.

## Evaluation with LongMemEval

For evaluation, we will start with using the [LongMemEval](https://github.com/xiaowu0162/LongMemEval) dataset to test five core long-term memory abilities:

- Information Extraction
- Multi-Session Reasoning
- Knowledge Updates
- Temporal Reasoning
- Abstention

Here are some examples from this dataset:

![Example Questions in LongMemEval](eval/LongMemEval/assets/longmemeval_examples.png)

This [dataset](https://drive.usercontent.google.com/download?id=1zJgtYRFhOh5zDQzzatiddfjYhFSnyQ80&export=download&authuser=0) was released in March, 2025 from: D. Wu, et al.  LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory. arXiv:2410.10813. [link](https://arxiv.org/abs/2410.10813)

### 📜 Dataset Format
Three files are included in the data package:

- `longmemeval_s.json`: The LongMemEval_S introduced in the paper. Concatenating all the chat history roughly consumes 115k tokens (~40 history sessions) for Llama 3.
- `longmemeval_m.json`: The LongMemEval_M introduced in the paper. Each chat history contains roughly 500 sessions.
- `longmemeval_oracle.json`: LongMemEval with oracle retrieval. Only the evidence sessions are included in the history.

Within each file, there are 500 evaluation instances.