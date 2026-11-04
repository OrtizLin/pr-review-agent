# Retrieval comparison

Guideline lines: 5
TF-IDF top-1 correct: 4/4
Old keyword method: returned the whole file every time, so top-1 precision was 1/5 by construction.

- Query `bare except handling`: top-1 correct = True; top 3 = [('- Do not use a bare `except:`; catch a specific exception and log it.', 0.4064), ('- Do not leave `print(` in production code; use logging.', 0.0), ('- Do not leave an unresolved `TODO` in new code without a tracked issue.', 0.0)]
- Query `hardcoded password secret`: top-1 correct = True; top 3 = [('- Do not hardcode secrets such as `password =`; use env / secret manager.', 0.4447), ('- Do not use a bare `except:`; catch a specific exception and log it.', 0.0), ('- Do not leave `print(` in production code; use logging.', 0.0)]
- Query `print logging production`: top-1 correct = True; top 3 = [('- Do not leave `print(` in production code; use logging.', 0.7171), ('- Do not use a bare `except:`; catch a specific exception and log it.', 0.0), ('- Do not leave an unresolved `TODO` in new code without a tracked issue.', 0.0)]
- Query `TODO tracked issue`: top-1 correct = True; top 3 = [('- Do not leave an unresolved `TODO` in new code without a tracked issue.', 0.5523), ('- Do not use a bare `except:`; catch a specific exception and log it.', 0.0), ('- Do not leave `print(` in production code; use logging.', 0.0)]
