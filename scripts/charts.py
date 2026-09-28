"""Build the two README charts from the checked-in response records."""

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHARTS = ROOT / "charts"
ROCM = ROOT / "data/raw/qwen-gsq-rocm-tuning-2026-09-27"
MTP = ROOT / "data/raw/qwen-gsq-mtp-nasone32-20260927"


def svg(title, description, width, height, content):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'role="img" aria-labelledby="title desc" font-family="Arial, sans-serif">\n'
            f'<title id="title">{title}</title><desc id="desc">{description}</desc>\n'
            f'<rect width="{width}" height="{height}" fill="#fff"/>\n'
            + "\n".join(content) + "\n</svg>\n")


def rocm_chart():
    names = ["base", "ub1024", "fit2560", "fit2048", "ub2048",
             "fit2048-65k", "ub2048-65k"]
    lines = [
        '<text x="30" y="34" font-size="20" font-weight="bold" fill="#17212b">Time to finish the same task</text>',
        '<text x="30" y="57" font-size="13" fill="#4b5563">GSQ-RCO IQ3_XXS, upstream ROCm, q8_0 KV, 894 output tokens. One run per bar.</text>',
        '<rect x="253" y="72" width="15" height="13" fill="#2875a8"/><text x="274" y="83" font-size="13">Prompt</text>',
        '<rect x="340" y="72" width="15" height="13" fill="#e59b39"/><text x="361" y="83" font-size="13">Generation</text>',
        '<text x="30" y="117" font-size="13" font-weight="bold">32k context (31,525 prompt tokens)</text>',
        '<text x="30" y="405" font-size="13" font-weight="bold">65k context (62,980 prompt tokens)</text>',
    ]
    for tick in range(0, 201, 50):
        x = 253 + tick * 2.7
        lines += [f'<line x1="{x:.1f}" y1="126" x2="{x:.1f}" y2="553" stroke="#e5e7eb"/>',
                  f'<text x="{x:.1f}" y="574" text-anchor="middle" font-size="12" fill="#4b5563">{tick}</text>']
    lines.append('<text x="523" y="599" text-anchor="middle" font-size="13">Elapsed seconds (less is better)</text>')
    for i, name in enumerate(names):
        d = json.loads((ROCM / f"{name}.json").read_text())
        t = d["response"]["timings"]
        prompt = t["prompt_ms"] / 1000
        generation = t["predicted_ms"] / 1000
        assert t["predicted_n"] == 894 and t["cache_n"] == 0
        assert abs(prompt + generation - d["wall_s"]) < 0.1
        used, limit = map(float, re.findall(r"([\d.]+)GB", d["memory_stats"]))
        free = limit - used
        y = 143 + i * 55 + (20 if i >= 5 else 0)
        x = 253
        label = f'ubatch {d["ubatch"]}, fit {d["fit_target_mib"]}'
        lines += [
            f'<text x="30" y="{y + 17}" font-size="13" fill="#17212b">{label}</text>',
            f'<rect x="{x}" y="{y}" width="{prompt * 2.7:.1f}" height="25" fill="#2875a8"/>',
            f'<rect x="{x + prompt * 2.7:.1f}" y="{y}" width="{generation * 2.7:.1f}" height="25" fill="#e59b39"/>',
            f'<text x="810" y="{y + 17}" font-size="13" fill="#{"a93632" if free < 1 else "17212b"}">{d["wall_s"]:.1f}s, {free:.2f} GB free</text>',
        ]
    lines.append('<text x="30" y="620" font-size="12" fill="#4b5563">32k rows also vary fit target. At 65k, both rows use fit 2048.</text>')
    return svg("ROCm task time by configuration", "Seven stacked bars show prompt and generation seconds, plus remaining container memory. At 65k, ubatch 1024 took 186.4 seconds with 2.55 GB free; ubatch 2048 took 167.4 seconds with 0.72 GB free.", 1050, 638, lines)


def mtp_chart():
    def timing(name):
        return json.loads((MTP / name).read_text())["timings"]

    no_prompt = timing("65k-nomtp-long.json")
    mtp_prompt = timing("65k-mtp1-long.json")
    no_follow = timing("65k-nomtp-followup.json")
    mtp_follow = timing("65k-mtp1-followup.json")
    assert no_prompt["prompt_n"] == mtp_prompt["prompt_n"] == 59734
    assert no_follow["cache_n"] == mtp_follow["cache_n"] == 59740
    pp = 100 * (mtp_prompt["prompt_per_second"] / no_prompt["prompt_per_second"] - 1)
    tg = 100 * (mtp_follow["predicted_per_second"] / no_follow["predicted_per_second"] - 1)
    lines = [
        '<text x="30" y="35" font-size="20" font-weight="bold" fill="#17212b">MTP n=1: mixed result, little memory headroom</text>',
        '<text x="30" y="59" font-size="13" fill="#4b5563">Change versus no MTP. Separate nasone32 fork, q4_0 KV, ubatch 256; one pair.</text>',
        '<line x1="394" y1="83" x2="394" y2="183" stroke="#6b7280"/>',
        '<text x="394" y="202" text-anchor="middle" font-size="12" fill="#4b5563">0%</text>',
        '<text x="30" y="111" font-size="14">Full prefill, 59,734 tokens</text>',
        f'<rect x="{394 + pp * 10:.1f}" y="90" width="{-pp * 10:.1f}" height="29" fill="#a93632"/>',
        f'<text x="{394 + pp * 10 - 8:.1f}" y="110" text-anchor="end" font-size="14" fill="#a93632">{pp:+.1f}%</text>',
        '<text x="30" y="165" font-size="14">Cached follow-up TG</text>',
        f'<rect x="394" y="144" width="{tg * 10:.1f}" height="29" fill="#2875a8"/>',
        f'<text x="{394 + tg * 10 + 8:.1f}" y="164" font-size="14" fill="#2875a8">{tg:+.1f}%</text>',
        '<text x="30" y="231" font-size="12" fill="#4b5563">Follow-up lengths differ: 169 vs 160 tokens. About 0.12 GB container memory remained with MTP.</text>',
    ]
    return svg("MTP effect at 65k context", "One matched setup: MTP reduced full prompt throughput by 12.4 percent and raised cached follow-up generation speed by 8.7 percent. The follow-up lengths differ and MTP left about 0.12 GB of container memory.", 900, 250, lines)


def main():
    charts = {"rocm-task-time.svg": rocm_chart(), "mtp-change.svg": mtp_chart()}
    if sys.argv[1:] == ["--check"]:
        assert all((CHARTS / name).read_text() == content for name, content in charts.items())
        print("Charts match raw data")
    else:
        CHARTS.mkdir(exist_ok=True)
        for name, content in charts.items():
            (CHARTS / name).write_text(content)


if __name__ == "__main__":
    main()
