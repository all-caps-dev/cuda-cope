#!/usr/bin/env python3
"""probe: a graded quality pass for a local model, in one file.

Speed benchmarks tell you a quant loaded and ran fast. They do not tell you it
was still thinking. This runs graded prompt sets with known answers against an
OpenAI-compatible endpoint and reports what fraction it got right, plus two
checks that catch the specific way low-bit quants fail on the wrong runtime:
prose coherence and structured-output validity.

    probe.py --endpoint http://localhost:8080
    probe.py --endpoint http://localhost:8080 --set counting --set arithmetic
    probe.py --endpoint http://localhost:8080 --json > benches/run.json

Why the two sets are graded differently
---------------------------------------
Letter counting fails on every model at every quant, because a model sees
tokens rather than characters. A low score there is not evidence of a broken
quant, and treating it as such sends you chasing a phantom.

Arithmetic is the opposite. A model that reads fluently but cannot multiply two
two-digit numbers is showing real damage, and it is the dangerous case because
the output still looks confident.

So: read the sets together. Counting low and arithmetic perfect is a healthy
model. Both low, with prose still fine, is a runtime or quant problem worth
chasing.

Python 3 standard library only.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PROMPTS = os.path.join(os.path.dirname(HERE), "prompts")


def chat(endpoint, model, messages, max_tokens, temperature, timeout=300):
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
        # Thinking off: a reasoning trace eats a small token budget and returns
        # an empty answer, which grades as a failure that never happened.
        "chat_template_kwargs": {"enable_thinking": False, "thinking": False},
    }
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "cuda-cope-probe/1.0"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.load(r)
    m = d["choices"][0]["message"]
    text = ((m.get("content") or "") or (m.get("reasoning_content") or "")).strip()
    return text, time.time() - t0, (d.get("usage") or {})


def discover_model(endpoint, timeout=10):
    """Ask the server what it is serving, so the bench file records the truth."""
    for path, pick in (("/v1/models", "list"), ("/props", "props")):
        try:
            req = urllib.request.Request(endpoint.rstrip("/") + path,
                                         headers={"User-Agent": "cuda-cope-probe/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.load(r)
            if pick == "list":
                items = d.get("models") or d.get("data") or []
                if items:
                    return items[0].get("name") or items[0].get("id")
            elif d.get("model_path"):
                return d["model_path"]
        except Exception:
            continue
    return None


def first_number(s):
    m = re.search(r"-?\d+(?:\.\d+)?", s.replace(",", ""))
    return m.group(0) if m else None


def run_set(endpoint, model, name, spec, runs):
    """Run one graded set. runs > 1 also reports determinism at temperature 0."""
    results = []
    for case in spec["cases"]:
        answers, times = [], []
        for _ in range(runs):
            try:
                txt, dt, _ = chat(endpoint, model, [{"role": "user", "content": case["q"]}],
                                  spec.get("max_tokens", 32), spec.get("temperature", 0))
            except Exception as e:
                answers.append("ERROR: %s" % str(e)[:60])
                times.append(0.0)
                continue
            answers.append(txt)
            times.append(dt)
        got = [first_number(a) for a in answers]
        correct = all(g == case["a"] for g in got)
        deterministic = len(set(got)) == 1
        results.append({
            "q": case["q"], "expected": case["a"], "got": got,
            "correct": correct, "deterministic": deterministic,
            "mean_s": round(sum(times) / len(times), 3) if times else None,
        })
    passed = sum(1 for r in results if r["correct"])
    return {"set": name, "passed": passed, "total": len(results),
            "note": spec.get("note", ""), "cases": results}


def coherence(endpoint, model):
    """The gibberish check. A broken low-bit quant on the wrong runtime does not
    fail cleanly; it produces text that parses as words but drifts, or sprays
    non-ASCII. Both are visible here without a judge model."""
    txt, dt, _ = chat(endpoint, model,
                      [{"role": "user", "content":
                        "Write exactly three sentences explaining why the sky is blue."}],
                      200, 0)
    non_ascii = sum(1 for c in txt if ord(c) > 127)
    words = txt.split()
    return {"seconds": round(dt, 2), "words": len(words), "non_ascii": non_ascii,
            "text": txt,
            "verdict": "clean" if words and non_ascii == 0 and len(words) > 15 else "suspect"}


def structured(endpoint, model):
    """Structured output. A model that cannot round-trip a trivial JSON object is
    useless for tool calling regardless of how it scores elsewhere."""
    txt, dt, _ = chat(endpoint, model,
                      [{"role": "user", "content":
                        'Return ONLY this JSON, no prose: {"city":"Lisbon","country":"Portugal"}'}],
                      80, 0)
    ok = False
    try:
        m = re.search(r"\{.*\}", txt, re.S)
        ok = json.loads(m.group(0)) == {"city": "Lisbon", "country": "Portugal"}
    except Exception:
        ok = False
    return {"seconds": round(dt, 2), "valid": ok, "text": txt}


def main():
    ap = argparse.ArgumentParser(description="Graded quality probe for a local model.")
    ap.add_argument("--endpoint", default=os.environ.get("PROBE_ENDPOINT", "http://localhost:8080"),
                    help="OpenAI-compatible base URL (default $PROBE_ENDPOINT or localhost:8080)")
    ap.add_argument("--model", default=os.environ.get("PROBE_MODEL"),
                    help="model id; default is whatever the server reports")
    ap.add_argument("--set", dest="sets", action="append",
                    help="prompt set name, repeatable; default is every set in prompts/")
    ap.add_argument("--runs", type=int, default=3,
                    help="repetitions per case, for determinism at temperature 0 (default 3)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = ap.parse_args()

    model = args.model or discover_model(args.endpoint)
    if not model:
        sys.exit("probe: could not reach %s or it served no models" % args.endpoint)

    names = args.sets or sorted(
        f[:-5] for f in os.listdir(PROMPTS)
        if f.endswith(".json") and not f.endswith(".local.json"))

    out = {"endpoint": args.endpoint, "model": model, "runs": args.runs,
           "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "sets": []}
    for n in names:
        path = os.path.join(PROMPTS, n + ".json")
        if not os.path.exists(path):
            sys.exit("probe: no prompt set %r in %s" % (n, PROMPTS))
        spec = json.load(open(path))
        if not all("a" in c for c in spec.get("cases", [])):
            print("probe: %r has cases without an 'a' answer key, skipping (is it a refusal set?)" % n, file=sys.stderr)
            continue
        out["sets"].append(run_set(args.endpoint, model, n, spec, args.runs))
    out["coherence"] = coherence(args.endpoint, model)
    out["structured"] = structured(args.endpoint, model)

    if args.json:
        print(json.dumps(out, indent=2))
        return

    print("model     : %s" % os.path.basename(str(model)))
    print("endpoint  : %s" % args.endpoint)
    print("runs/case : %d at temperature 0\n" % args.runs)
    for s in out["sets"]:
        print("== %s: %d/%d ==" % (s["set"], s["passed"], s["total"]))
        for c in s["cases"]:
            flag = "PASS" if c["correct"] else "FAIL"
            nd = "" if c["deterministic"] else "  NON-DETERMINISTIC"
            print("   %-4s expected %-5s got %-18s %.2fs%s"
                  % (flag, c["expected"], ",".join(str(g) for g in c["got"]), c["mean_s"] or 0, nd))
        print()
    co, st = out["coherence"], out["structured"]
    print("coherence : %s (%d words, %d non-ascii, %.2fs)"
          % (co["verdict"], co["words"], co["non_ascii"], co["seconds"]))
    print("structured: %s (%.2fs)" % ("valid JSON" if st["valid"] else "INVALID", st["seconds"]))
    print("\nReading it: counting low with arithmetic perfect is a healthy model.")
    print("Both low with prose still clean is a runtime or quant problem.")


if __name__ == "__main__":
    main()
