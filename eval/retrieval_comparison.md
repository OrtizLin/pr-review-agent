# Retrieval comparison

Guideline lines: 5
TF-IDF original top-1: 4/4
TF-IDF paraphrase top-1: 2/5
Old keyword method: returned the whole file every time, so top-1 precision was 1/5 by construction.

- Original query `bare except handling`: TF-IDF top-1 correct = True; top 3 = [('- Do not use a bare `except:`; catch a specific exception and log it.', 0.4064), ('- Do not leave `print(` in production code; use logging.', 0.0), ('- Do not leave an unresolved `TODO` in new code without a tracked issue.', 0.0)]
- Original query `hardcoded password secret`: TF-IDF top-1 correct = True; top 3 = [('- Do not hardcode secrets such as `password =`; use env / secret manager.', 0.4447), ('- Do not use a bare `except:`; catch a specific exception and log it.', 0.0), ('- Do not leave `print(` in production code; use logging.', 0.0)]
- Original query `print logging production`: TF-IDF top-1 correct = True; top 3 = [('- Do not leave `print(` in production code; use logging.', 0.7171), ('- Do not use a bare `except:`; catch a specific exception and log it.', 0.0), ('- Do not leave an unresolved `TODO` in new code without a tracked issue.', 0.0)]
- Original query `TODO tracked issue`: TF-IDF top-1 correct = True; top 3 = [('- Do not leave an unresolved `TODO` in new code without a tracked issue.', 0.5523), ('- Do not use a bare `except:`; catch a specific exception and log it.', 0.0), ('- Do not leave `print(` in production code; use logging.', 0.0)]
- Paraphrase query `catching every error without naming the type and without recording it`: TF-IDF top-1 correct = False; top 3 = [('- Do not leave an unresolved `TODO` in new code without a tracked issue.', 0.2206), ('- Do not use a bare `except:`; catch a specific exception and log it.', 0.2097), ('- Every finding in a review must cite a diff line, a tool result, or a guideline.', 0.0801)]
- Paraphrase query `storing a credential directly in source code instead of a vault`: TF-IDF top-1 correct = False; top 3 = [('- Every finding in a review must cite a diff line, a tool result, or a guideline.', 0.4418), ('- Do not leave an unresolved `TODO` in new code without a tracked issue.', 0.3007), ('- Do not use a bare `except:`; catch a specific exception and log it.', 0.2569)]
- Paraphrase query `leaving debug output in shipped code instead of proper logging`: TF-IDF top-1 correct = True; top 3 = [('- Do not leave `print(` in production code; use logging.', 0.4526), ('- Do not leave an unresolved `TODO` in new code without a tracked issue.', 0.1825), ('- Every finding in a review must cite a diff line, a tool result, or a guideline.', 0.0541)]
- Paraphrase query `marking unfinished work in code with no ticket to track it`: TF-IDF top-1 correct = False; top 3 = [('- Do not leave `print(` in production code; use logging.', 0.23), ('- Do not leave an unresolved `TODO` in new code without a tracked issue.', 0.1772), ('- Do not use a bare `except:`; catch a specific exception and log it.', 0.1532)]
- Paraphrase query `a review comment with no evidence from the change, a tool, or a rule`: TF-IDF top-1 correct = True; top 3 = [('- Every finding in a review must cite a diff line, a tool result, or a guideline.', 0.6528), ('- Do not use a bare `except:`; catch a specific exception and log it.', 0.2742), ('- Do not leave an unresolved `TODO` in new code without a tracked issue.', 0.1442)]

Embedding original top-1: 4/4
Embedding paraphrase top-1: 5/5
Verdict: embedding BEATS TF-IDF on paraphrases without losing on originals -> switch default to embedding.
