# Team Guidelines (retrieved by the agent)

- Do not use a bare `except:`; catch a specific exception and log it.
- Do not leave `print(` in production code; use logging.
- Do not leave an unresolved `TODO` in new code without a tracked issue.
- Do not hardcode secrets such as `password =`; use env / secret manager.
- Every finding in a review must cite a diff line, a tool result, or a guideline.
