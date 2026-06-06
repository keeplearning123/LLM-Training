from openai import OpenAI
import argparse
import itertools
import json
import textwrap


def make_client(base_url: str, api_key: str):
	return OpenAI(base_url=base_url, api_key=api_key)


def run_and_print(client, model, messages, temperature, top_p, top_k, run_idx=None):
	response = client.chat.completions.create(
		model=model,
		messages=messages,
		temperature=temperature,
		top_p=top_p,
		extra_body={"top_k": top_k},
	)

	header = f"Run {run_idx}: temp={temperature} top_p={top_p} top_k={top_k}" if run_idx is not None else f"temp={temperature} top_p={top_p} top_k={top_k}"
	print("=" * 80)
	print(header)
	print("-" * 80)
	# pretty print the assistant text and a short JSON summary
	text = response.choices[0].message.content
	print(textwrap.fill(text, width=80))
	print("-" * 80)
	meta = {
		"model": response.model if hasattr(response, "model") else model,
		"usage": _make_json_safe(getattr(response, "usage", None)),
	}
	print(json.dumps(meta, indent=2))


def parse_list(s: str):
	# comma separated floats/ints
	parts = [p.strip() for p in s.split(",") if p.strip()]
	vals = []
	for p in parts:
		try:
			if "." in p:
				vals.append(float(p))
			else:
				vals.append(int(p))
		except Exception:
			vals.append(p)
	return vals


def _make_json_safe(obj):
	"""Attempt to convert common SDK objects into JSON-serializable forms.

	- dict/list/primitive -> left as-is
	- objects with .to_dict() -> use that
	- pydantic/BaseModel -> .dict()
	- objects with __dict__ -> shallow copy
	- otherwise -> str(obj)
	"""
	if obj is None:
		return None
	# primitives
	if isinstance(obj, (str, int, float, bool)):
		return obj
	if isinstance(obj, (list, tuple)):
		return [_make_json_safe(x) for x in obj]
	if isinstance(obj, dict):
		return {k: _make_json_safe(v) for k, v in obj.items()}

	# try common SDK helpers
	try:
		if hasattr(obj, "to_dict") and callable(obj.to_dict):
			return _make_json_safe(obj.to_dict())
	except Exception:
		pass
	try:
		# pydantic BaseModel
		from pydantic import BaseModel

		if isinstance(obj, BaseModel):
			return _make_json_safe(obj.dict())
	except Exception:
		pass

	# fallback to __dict__ if available
	if hasattr(obj, "__dict__"):
		try:
			return {k: _make_json_safe(v) for k, v in vars(obj).items()}
		except Exception:
			pass

	# last resort: string representation
	try:
		return str(obj)
	except Exception:
		return None


def main():
	parser = argparse.ArgumentParser(description="Compare sampling parameters for local LLM")
	parser.add_argument("--base-url", default="http://localhost:11434/v1", help="Local LLM base URL")
	parser.add_argument("--api-key", default="ollama", help="API key for local LLM client")
	parser.add_argument("--model", default="llama3.2:1b", help="Model to call")
	parser.add_argument("--prompt", default="Which of the undergrad schools have open house this weekend", help="User prompt")
	parser.add_argument("--temperatures", default="0.0,0.2,0.8", help="Comma-separated temperatures to try (e.g. 0.0,0.2,0.8)")
	parser.add_argument("--top-p", dest="top_ps", default="1.0", help="Comma-separated top_p values to try (e.g. 0.7,0.9,1.0)")
	parser.add_argument("--top-k", dest="top_ks", default="5", help="Comma-separated top_k (top_k -> extra_body.top_k) values to try (e.g. 1,5,40)")
	args = parser.parse_args()

	temps = parse_list(args.temperatures)
	top_ps = parse_list(args.top_ps)
	top_ks = parse_list(args.top_ks)

	client = make_client(args.base_url, args.api_key)

	messages = [{"role": "user", "content": args.prompt}]

	combos = list(itertools.product(temps, top_ps, top_ks))
	print(f"Running {len(combos)} combinations against model {args.model}\n")
	for idx, (t, tp, k) in enumerate(combos, start=1):
		try:
			run_and_print(client, args.model, messages, t, tp, k, run_idx=idx)
		except Exception as e:
			print(f"Error on run {idx} (temp={t} top_p={tp} top_k={k}): {e}")


if __name__ == "__main__":
	main()
