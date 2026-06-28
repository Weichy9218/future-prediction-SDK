"""futurecast — a thin forecasting agent.

A provider-agnostic loop (loop/agent.py) + 4 forecasting-specific pieces:
  playbook (cognition in prompt) · as-of guard · scorable output · experience library.
Models come from a pluggable backend: CoreLLMBackend (cheap, default) or ClaudeBackend (optional).
"""
