"""futurecast — the prediction CONTROL LAYER for a rented general agent.

We do NOT rebuild the agent loop. The loop/harness (context, plan, memory) is rented (Claude
Agent SDK); only the model-routing layer is ours (agent_sdk/llm_adapter.py, an Anthropic endpoint
backed by futurecast/llm — see agent_sdk/). This package owns only the four
forecasting-specific pieces that a general agent lacks:

  playbook/    — forecasting cognition, in the prompt (no Python state machine)
  guard/       — the as-of fetch guard (the one trust not given to the prompt)
  io/          — scorable output + scoring (Brier / numeric error / calibration)
  experience/  — the skills / experience library, disclosed on demand

plus data/ (the generic question contract) and llm/ (a reasoning-capable direct client,
Responses API summary:auto — the one path that can capture a hidden reasoning summary, which
the rented chat/completions loop cannot).
"""
