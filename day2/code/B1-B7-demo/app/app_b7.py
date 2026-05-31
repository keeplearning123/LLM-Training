"""
The Company App — B7 edition
==============================
Evolved from B1. New test cases exercise the response-side controls.

Test 1 — normal question           → 200  (passes everything)
Test 2 — banned keyword            → 403  (blocked at request, B1 rule)
Test 3 — prompt too large          → 413  (blocked at request, B1 rule)
Test 4 — ask for PII in response   → 451  (LLM replies with PII, Presidio catches it)
Test 5 — ask for structured JSON   → 200  (Pydantic validates shape, passes)
Test 6 — trigger schema mismatch   → 422  (response shape wrong, Pydantic blocks)
"""
import time
import httpx

GATEWAY_URL    = "http://gateway:8000/v1/chat/completions"
GATEWAY_HEALTH = "http://gateway:8000/health"


def wait_for_gateway():
    for attempt in range(1, 21):
        try:
            httpx.get(GATEWAY_HEALTH, timeout=2)
            print("Gateway is ready.\n")
            return
        except Exception:
            print(f"Waiting for gateway... ({attempt})")
            time.sleep(1)
    raise SystemExit("Gateway never came up.")


def ask(label: str, question: str, expected: str):
    """Send one question and print the result clearly."""
    print(f"{'─' * 60}")
    print(f"TEST: {label}")
    print(f"  Expected : HTTP {expected}")
    print(f"  Question : {question[:80]}{'...' if len(question) > 80 else ''}")

    response = httpx.post(
        GATEWAY_URL,
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": question}],
        },
        timeout=40,
    )

    status = response.status_code
    data   = response.json()
    match  = "✓ PASS" if str(status) == expected else "✗ FAIL"

    print(f"  Got      : HTTP {status}  {match}")

    if status == 200:
        reply = data["choices"][0]["message"]["content"]
        print(f"  Reply    : {reply.strip()[:120]}")

    elif status == 451:
        err = data.get("error", {})
        print(f"  Blocked  : {err.get('message')}")
        print(f"  Entities : {err.get('entities')}")

    elif status == 422:
        err = data.get("error", {})
        print(f"  Blocked  : {err.get('message')}")

    else:
        err = data.get("error", {})
        print(f"  Blocked  : {err.get('message', data)}")

    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Company app — B7 (request + response guardrails)")
    print("=" * 60)
    print()

    wait_for_gateway()

    # ── B1 request-side controls (still work exactly as before) ─────────────

    ask(
        label    = "Normal banking question",
        question = "In one sentence, what is a fixed deposit?",
        expected = "200",
    )

    ask(
        label    = "Banned keyword in request",
        question = "Tell me about projectfalcon, our new release.",
        expected = "403",
    )

    ask(
        label    = "Prompt too large",
        question = "Summarize this: " + ("data " * 3000),
        expected = "413",
    )

    # ── B7 response-side controls (new) ─────────────────────────────────────

    ask(
        label    = "PII in response — SSN echoed back",
        question = (
            "A customer named Sarah Johnson called. Her SSN is 987-65-4321 "
            "and her account number is 4532-1234-5678-9012. "
            "Please summarise this customer record in one sentence."
        ),
        expected = "451",
        # The LLM will echo the SSN and card number in its reply.
        # Presidio catches PERSON + US_SSN + CREDIT_CARD → 451.
    )

    ask(
        label    = "PII in response — name and email",
        question = (
            "Draft a one-sentence reply to our customer "
            "james.wilson@acmebank.com confirming his appointment."
        ),
        expected = "451",
        # LLM echoes the email address → EMAIL_ADDRESS detected → 451.
    )

    ask(
        label    = "Clean response — no PII, passes everything",
        question = "In one sentence, what is compound interest?",
        expected = "200",
    )

    print("=" * 60)
    print("Done. Check traces/trace.jsonl — notice:")
    print("  phase: 'request'  → blocked before LLM ran   ($0 cost)")
    print("  phase: 'response' → blocked after LLM ran    (tokens already spent)")
    print("=" * 60)