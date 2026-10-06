"""Test-only Qwen XML to OpenAI tool calls. Does not execute tools."""
import json
import re
import uuid

def parse_output(text, tools):
    reasoning = ""
    if "</think>" in text:
        reasoning, text = text.split("</think>", 1)
        reasoning = reasoning.removeprefix("<think>").strip()
    declared = {t["function"]["name"]: t["function"] for t in tools}
    calls = []
    blocks = re.findall(r"<tool_call>(.*?)</tool_call>", text, re.S)
    if "<tool_call>" in text and not blocks:
        raise ValueError("Incomplete tool call")
    for block in blocks:
        match = re.fullmatch(r"\s*<function=([^>]+)>(.*?)</function>\s*", block, re.S)
        if not match or match[1] not in declared:
            raise ValueError("Malformed or undeclared tool")
        function = declared[match[1]]
        schema = function.get("parameters", {})
        properties = schema.get("properties", {})
        arguments = {}
        for parameter in re.finditer(r"<parameter=([^>]+)>(.*?)</parameter>", match[2], re.S):
            name, value = parameter[1], parameter[2].strip()
            if name not in properties or name in arguments:
                raise ValueError("Unknown or duplicate parameter")
            kind = properties[name].get("type", "string")
            if kind != "string":
                value = json.loads(value)
                expected = {"integer": int, "number": (int, float), "boolean": bool, "array": list, "object": dict}.get(kind)
                if expected is None or not isinstance(value, expected) or (kind in ("integer", "number") and isinstance(value, bool)):
                    raise ValueError("Wrong parameter type")
            arguments[name] = value
        remainder = re.sub(r"<parameter=[^>]+>.*?</parameter>", "", match[2], flags=re.S)
        if remainder.strip() or any(k not in arguments for k in schema.get("required", [])):
            raise ValueError("Missing or malformed parameters")
        calls.append({"id": "call_" + uuid.uuid4().hex, "type": "function",
                      "function": {"name": match[1], "arguments": json.dumps(arguments)}})
    content = re.sub(r"<tool_call>.*?</tool_call>", "", text, flags=re.S).strip()
    if "<tool_call>" in content or "</tool_call>" in content:
        raise ValueError("Unmatched tool marker")
    return content, reasoning, calls

if __name__ == "__main__":
    tools = [{"type": "function", "function": {"name": "read", "parameters": {
        "type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}}]
    sample = "<think>check</think><tool_call><function=read><parameter=path>fakty.txt</parameter></function></tool_call>"
    content, reasoning, calls = parse_output(sample, tools)
    assert content == "" and reasoning == "check" and json.loads(calls[0]["function"]["arguments"]) == {"path": "fakty.txt"}
    assert parse_output("OK", tools) == ("OK", "", [])
    for bad in (sample.replace("function=read", "function=write"), sample.replace("parameter=path", "parameter=oops"), sample.replace("</tool_call>", "")):
        try:
            parse_output(bad, tools)
        except ValueError:
            pass
        else:
            raise AssertionError(bad)
    print("parser checks PASS")
