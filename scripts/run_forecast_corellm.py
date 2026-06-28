"""Run the SAME forecast question as the glm-5 Agent-SDK demo, but through the core/llm path
(CoreLLMBackend -> GPTSub2APIClient -> haoxiang gpt_sub2api gpt-5.5). No Agent SDK, no router.

This answers "can the previous core/llm run gpt-5.5?" and produces a trajectory we can compare
against the glm-5 Agent-SDK rollout. The trajectory is written to log/corellm/<ts>.jsonl in a
record-per-message form (the core/llm loop is our own, so it is not a claude-CLI transcript;
that difference is exactly the point of the comparison).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# The gateways are reachable directly; drop any inherited SOCKS/HTTP proxy so httpx (inside the
# openai SDK) does not route LLM calls through a proxy that may be absent in this environment.
for _k in ("ALL_PROXY", "all_proxy", "HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
    os.environ.pop(_k, None)

import anyio

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from futurecast.model.coremllm_backend import CoreLLMBackend  # noqa: E402

PLAYBOOK = (ROOT / "futurecast/playbook/playbook_A_numeric.md").read_text(encoding="utf-8")
AS_OF = "2026-06-14"
QUESTION = (
    "You are forecasting a recurring numeric series.\n"
    f"AS-OF CUTOFF: {AS_OF}. Use only information available up to this date; do not use any "
    "knowledge of the realized value.\n\n"
    "On 2026-06-15 (UTC+8), what will Local Hybrid Hog (土杂猪) hog price (生猪价格) be, in CNY "
    "per kilogram (元/公斤)?\n\n"
    "End with: \\boxed{<plain number>} then a one-line JSON "
    '{"point":n,"low":n,"high":n,"anchor":"...","confidence":"low|med|high"}.\n\n'
    "Do not use any tools; answer from your own reasoning."
)


async def main(model: str) -> None:
    backend = CoreLLMBackend("gpt_sub2api", model=model)
    messages = [
        {"role": "system", "content": PLAYBOOK},
        {"role": "user", "content": QUESTION},
    ]
    t0 = time.time()
    turn = await backend.chat(messages, tools=None)
    dt = time.time() - t0
    text = turn["content"]
    print(text)
    print(f"\n=== {backend.name} | {dt:.1f}s ===")

    # write trajectory (record per message + meta), relocated under log/corellm/
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = ROOT / "log/corellm" / f"gpt55_{stamp}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = turn.get("raw")
    usage = getattr(raw, "usage", None) if raw is not None else None
    with out.open("w", encoding="utf-8") as fh:
        for m in messages:
            fh.write(json.dumps({"type": m["role"], "content": m["content"]}, ensure_ascii=False) + "\n")
        fh.write(json.dumps({"type": "assistant", "content": text,
                             "tool_calls": turn.get("tool_calls")}, ensure_ascii=False) + "\n")
        fh.write(json.dumps({"type": "result", "model": backend.name, "elapsed_s": round(dt, 1),
                             "usage": usage}, ensure_ascii=False) + "\n")
    print("ROLLOUT TRANSCRIPT:", out)
    await backend.aclose()


if __name__ == "__main__":
    anyio.run(main, sys.argv[1] if len(sys.argv) > 1 else "gpt-5.5")
