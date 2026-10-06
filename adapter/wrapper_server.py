"""Local adapter around the fork's server.py: XML tool calls -> OpenAI tool_calls.

Paths come from env (defaults match launch-wrapper.sh container mounts):
  WRAPPER_FORK_DIR  fork checkout with normalize_messages applied (default /fork)
  WRAPPER_OUT_DIR   writable dir for pid/request/timing logs (default /out)
Errors use the fork's shape ({"detail": ...}): 400 bad client input, 502 unparseable model output.
"""
import faulthandler
import functools
import inspect
import json
import os
import runpy
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from xml_tools import parse_output

FORK = Path(os.environ.get('WRAPPER_FORK_DIR', '/fork'))
OUT = Path(os.environ.get('WRAPPER_OUT_DIR', '/out'))
faulthandler.enable(all_threads=True)
(OUT / 'wrapper-server.pid').write_text(str(os.getpid()))
sys.path.insert(0, str(FORK / 'rocm_tools/exl3_server'))
# The fork's server.py ends with os._exit(0), which would MASK an exit crash; log it instead so the interpreter exits naturally.
os._exit = lambda code: print('NATURAL_EXIT', code, flush=True)
original_post = FastAPI.post

def check_tools(tools):
    if not all(isinstance(t, dict) and isinstance(t.get('function'), dict) and isinstance(t['function'].get('name'), str)
               and isinstance(t['function'].get('parameters', {}), dict) for t in tools):
        raise HTTPException(400, "Each tool must be {'type': 'function', 'function': {'name': ..., 'parameters': {...}}}")

def post(self, path, *args, **kwargs):
    register = original_post(self, path, *args, **kwargs)
    if path != '/v1/chat/completions':
        return register
    def decorate(fn):
        original_log = fn.__globals__["log_request"]
        def capture_log(kind, final):
            original_log(kind, final)
            fields = ("prompt_tokens", "cached_tokens", "new_tokens", "time_prefill", "time_generate", "eos_reason")
            with open(OUT / "wrapper-timings.jsonl", "a") as f:f.write(json.dumps({k:final.get(k) for k in fields})+"\n")
        fn.__globals__["log_request"] = capture_log
        @functools.wraps(fn)
        async def adapted(request, body):
            with open(OUT / 'wrapper-requests.jsonl', 'a') as f:
                f.write(json.dumps(dict(max_tokens=body.max_tokens, max_completion_tokens=body.max_completion_tokens,
                                        stream=body.stream, tools=[t.get('function', {}).get('name') if isinstance(t, dict) else None for t in body.tools or []],
                                        kwargs=body.chat_template_kwargs)) + '\n')
            if not body.tools:
                return await fn(request, body)
            check_tools(body.tools)
            response = await fn(request, body.model_copy(update={'stream': False}))
            payload = json.loads(response.body)
            for choice in payload['choices']:
                try:
                    content, reasoning, calls = parse_output(choice['message']['content'], body.tools)
                except ValueError as e:  # whole response is rejected, nothing is executed from it
                    raise HTTPException(502, f"Unparseable tool call in model output: {e}") from e
                message = choice['message']
                message['content'] = content or None
                if reasoning:
                    message['reasoning_content'] = reasoning
                if calls:
                    message['tool_calls'] = calls
                    choice['finish_reason'] = 'tool_calls'
            if not body.stream:
                return JSONResponse(payload)
            # ponytail: buffers one bounded response; incremental XML parsing only if latency matters.
            async def stream():
                for choice in payload['choices']:
                    delta = dict(choice['message'])
                    if 'tool_calls' in delta:
                        delta['tool_calls'] = [dict(call, index=i) for i, call in enumerate(delta['tool_calls'])]
                    base = {k: payload[k] for k in ('id', 'created', 'model')}
                    base['object'] = 'chat.completion.chunk'
                    yield {'data': json.dumps(dict(base, choices=[{'index': choice['index'], 'delta': delta, 'finish_reason': None}]))}
                    yield {'data': json.dumps(dict(base, usage=payload['usage'], choices=[{'index': choice['index'], 'delta': {}, 'finish_reason': choice['finish_reason']}]))}
                yield {'data': '[DONE]'}
            return EventSourceResponse(stream())
        adapted.__signature__ = inspect.signature(fn, eval_str=True)
        return register(adapted)
    return decorate

FastAPI.post = post
runpy.run_path(str(FORK / 'rocm_tools/exl3_server/server.py'), run_name='__main__')
