# -*- coding: utf-8 -*-
"""L6 事實查核。第二次呼叫 gpt-5.6-sol-high，並用正規表達式核對數字。

未通過的格子回到 generate_messages.generate_cell，最多 3 次（含第一次）。
仍不過的格子保留最後一版，並在查核欄標明。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import generate_messages as gen

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "knowledge" / "generated_examples.md"
MAX_ATTEMPTS = 3


def fact_prompt(text: str, cited_rows: list[dict]) -> str:
    blocks = []
    for row in cited_rows:
        blocks.append(f"[id={row['id']}] {row['topic']}\n{row['text']}")
    packed = "\n\n".join(blocks) if blocks else "（沒有引用條目）"
    return f"""你是 Lexus 售後知識庫的事實查核員。不要讀檔，不要使用工具。
對照訊息與被引用條目原文，列出訊息裡的每一個具體主張。

只列這些：金額、年限、里程、次數、百分比、具名服務或保證方案（例如尊榮安檢、延長保證、定保套餐、零件保證、預約保留時間）、以及保證除外條件。
寒暄、邀請、渠道用語不要列。
一句話如果把兩個條件併在一起（例如自備油品和消耗性零件），拆成兩條主張分別判定，不要漏。

status 只能是 supported、unsupported、not_in_kb。
- supported：數字與意思都出現在某一條被引用原文。
- unsupported：與原文矛盾，或數字被改寫、換算。
- not_in_kb：講了具體事實，但提供的原文沒有。

只輸出一個 JSON 物件，第一個字元是 {{ 。
格式：{{"claims":[{{"claim":"...","kind":"年限","status":"supported","evidence_id":"1"}}]}}
kind 用：年限、里程、次數、金額、百分比、服務名稱。
supported 的 evidence_id 必須是上面某條的 id。沒有具體主張時 claims 為空陣列。

訊息：
{text}

被引用條目：
{packed}
"""


def normalize_claims(obj: dict, cited_ids: list[str]) -> list[dict]:
    raw = obj.get("claims") or []
    claims = []
    allowed = {"supported", "unsupported", "not_in_kb"}
    for item in raw:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "").strip()
        if status not in allowed:
            status = "unsupported"
        evidence = gen.norm_id(item.get("evidence_id") or "")
        if status == "supported" and evidence not in cited_ids:
            status = "not_in_kb"
        claims.append({
            "claim": re_space(str(item.get("claim") or "")),
            "kind": str(item.get("kind") or ""),
            "status": status,
            "evidence_id": evidence,
        })
    return claims


def re_space(text: str) -> str:
    return " ".join(text.split())


def check_once(rec: dict, kb_by_id: dict) -> dict:
    cited_ids = rec.get("cited_ids") or []
    cited_rows = [kb_by_id[i] for i in cited_ids if i in kb_by_id]
    corpus = "\n".join(row["text"] for row in cited_rows)
    missing = gen.numbers_missing(rec.get("text") or "", corpus)
    claims = []
    fc_error = ""
    try:
        obj = gen.call_llm(
            fact_prompt(rec["text"], cited_rows),
            f"{rec['persona']}-{rec['touchpoint']}-fc{rec.get('attempt', 1)}",
        )
        claims = normalize_claims(obj, cited_ids)
    except Exception as exc:
        fc_error = str(exc)
    supported = sum(1 for c in claims if c["status"] == "supported")
    total = len(claims)
    ratio = (supported / total) if total else 0.0
    reasons = list(rec.get("local_errors") or [])
    if fc_error:
        reasons.append(f"查核模型沒有回傳：{fc_error}")
    if total == 0:
        reasons.append("查核模型沒有列出任何具體主張")
    elif ratio < 1:
        bad = [c for c in claims if c["status"] != "supported"]
        for c in bad:
            reasons.append(f"{c['status']}：{c['claim']}")
    if missing:
        reasons.append("數字不在引用條目：" + "、".join(missing))
    # local_errors 可能已經含數字問題，去重
    dedup = list(dict.fromkeys(reasons))
    passed = not dedup and ratio == 1.0 and not missing and total > 0
    return {
        "claims": claims,
        "supported": supported,
        "total": total,
        "supported_ratio": ratio,
        "numbers": gen.extract_numbers(rec.get("text") or ""),
        "numbers_missing": missing,
        "number_ok": not missing,
        "passed": passed,
        "reasons": dedup,
    }


def run_cell(cell: dict, kb_index, kb_by_id: dict) -> dict:
    feedback = None
    rec = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            rec = gen.generate_cell(cell, kb_index, feedback=feedback, attempt=attempt)
        except Exception as exc:
            rec = {
                "persona": cell["persona"],
                "touchpoint": cell["touchpoint"],
                "touchpoint_label": cell["touchpoint_label"],
                "channel": cell["channel"],
                "text": "",
                "cited_ids": [],
                "design_note": "",
                "kpi": cell["kpi"],
                "attempt": attempt,
                "retrieved_ids": [],
                "retrieval": [],
                "local_errors": [f"生成失敗：{exc}"],
                "model": gen.MODEL,
            }
        fc = check_once(rec, kb_by_id)
        rec["factcheck"] = fc
        rec["regen_count"] = attempt - 1
        print(
            f"{cell['persona']} {cell['touchpoint']} attempt={attempt} "
            f"pass={fc['passed']} ratio={fc['supported_ratio']:.2f} "
            f"missing={fc['numbers_missing']} reasons={fc['reasons'][:3]}",
            flush=True,
        )
        if fc["passed"]:
            return rec
        feedback = "\n".join(f"- {r}" for r in fc["reasons"])
    return rec


def write_examples(rows: list[dict]) -> None:
    labels = {tp["id"]: tp["label"] for tp in gen.TOUCHPOINTS}
    header = [
        "# L6 溝通內容範例：Persona × 接觸點",
        "",
        "12 則由 gpt-5.6-sol-high 生成，數字只來自 `knowledge/lexus_aftersales_kb.jsonl` 被引用的條目。",
        "簡報 P12 只放每則前 40 字與渠道；完整文字、引用、設計說明與查核結果在本檔。",
        "12 則皆須人工審核後才投遞。代表句取自 `reports/T10_risk_persona_report.md` §6 去識別版，訊息裡沒有論壇帳號。",
        "",
        "## 12 格",
        "",
        "| Persona | 保固到期前 60 天 | 回廠間隔拉長 | 刪項後首次回廠 |",
        "| --- | --- | --- | --- |",
    ]
    by_key = {(r["persona"], r["touchpoint"]): r for r in rows}

    def cell_html(rec: dict) -> str:
        fc = rec.get("factcheck") or {}
        ratio = fc.get("supported_ratio")
        ratio_s = "—" if ratio is None else f"{ratio:.0%}"
        passed = "通過" if fc.get("passed") else "未通過"
        missing = fc.get("numbers_missing") or []
        num = "數字對得上" if fc.get("number_ok") else ("數字未對上：" + "、".join(missing))
        cites = "、".join(rec.get("cited_ids") or []) or "—"
        text = (rec.get("text") or "（無）").replace("|", "／")
        note = (rec.get("design_note") or "—").replace("|", "／")
        reasons = fc.get("reasons") or []
        reason = ""
        if reasons and not fc.get("passed"):
            reason = "<br>例外：" + "；".join(reasons).replace("|", "／")
        return (
            f"**{rec.get('channel', '')}**<br>"
            f"訊息：{text}<br>"
            f"引用條目：{cites}<br>"
            f"設計說明：{note}<br>"
            f"KPI：{rec.get('kpi', '')}<br>"
            f"查核：{passed}，主張 supported {ratio_s}"
            f"（{fc.get('supported', 0)}/{fc.get('total', 0)}），{num}，"
            f"重生成 {rec.get('regen_count', 0)} 次{reason}"
        )

    for persona in gen.PERSONAS:
        cols = []
        for tp in ("T1", "T2", "T3"):
            rec = by_key.get((persona["name"], tp))
            cols.append(cell_html(rec) if rec else "—")
        header.append(f"| {persona['name']} | " + " | ".join(cols) + " |")

    header += ["", "## 逐則", ""]
    for persona in gen.PERSONAS:
        for tp in gen.TOUCHPOINTS:
            if tp["id"] == "T4":
                continue
            rec = by_key.get((persona["name"], tp["id"]))
            if not rec:
                continue
            fc = rec.get("factcheck") or {}
            claims = fc.get("claims") or []
            claim_lines = []
            for c in claims:
                claim_lines.append(
                    f"  - {c.get('kind', '')}／{c.get('status', '')}：{c.get('claim', '')}（條目 {c.get('evidence_id') or '—'}）"
                )
            if not claim_lines:
                claim_lines.append("  - （無）")
            header += [
                f"### {persona['name']} × {tp['id']} {labels[tp['id']]}",
                "",
                f"- 渠道：{rec.get('channel')}",
                f"- KPI：{rec.get('kpi')}",
                f"- 引用條目：{'、'.join(rec.get('cited_ids') or []) or '—'}",
                f"- 檢索前 5：{'、'.join(rec.get('retrieved_ids') or []) or '—'}",
                f"- 設計說明：{rec.get('design_note') or '—'}",
                f"- 查核：{'通過' if fc.get('passed') else '未通過'}；"
                f"supported {fc.get('supported', 0)}/{fc.get('total', 0)}；"
                f"重生成 {rec.get('regen_count', 0)} 次；生成次數 {rec.get('attempt', 1)}",
                "- 主張：",
                *claim_lines,
                "- 訊息全文：",
                "",
                rec.get("text") or "（無）",
                "",
            ]
    t4 = [r for r in rows if r.get("touchpoint") == "T4"]
    if t4:
        header += [
            "## 待料通知（R5，T18 新增）",
            "",
            "觸發是零件待料超過 7 天，或同一台車待料至少 2 次。7 天和 2 次是內部規則，正文不寫。數字只來自被引用條目。沒有到貨日，也沒有價格。",
            "",
        ]
        for rec in t4:
            fc = rec.get("factcheck") or {}
            claims = fc.get("claims") or []
            claim_lines = []
            for c in claims:
                claim_lines.append(
                    f"  - {c.get('kind', '')}／{c.get('status', '')}：{c.get('claim', '')}（條目 {c.get('evidence_id') or '—'}）"
                )
            if not claim_lines:
                claim_lines.append("  - （無）")
            header += [
                f"### {rec.get('persona')} × 待料通知",
                "",
                f"- 渠道：{rec.get('channel')}",
                f"- KPI：{rec.get('kpi')}",
                f"- 引用條目：{'、'.join(rec.get('cited_ids') or []) or '—'}",
                f"- 檢索前 5：{'、'.join(rec.get('retrieved_ids') or []) or '—'}",
                f"- 設計說明：{rec.get('design_note') or '—'}",
                f"- 查核：{'通過' if fc.get('passed') else '未通過'}；"
                f"supported {fc.get('supported', 0)}/{fc.get('total', 0)}；"
                f"重生成 {rec.get('regen_count', 0)} 次；生成次數 {rec.get('attempt', 1)}",
                "- 主張：",
                *claim_lines,
                "- 訊息全文：",
                "",
                rec.get("text") or "（無）",
                "",
            ]
    EXAMPLES.write_text("\n".join(header), encoding="utf-8")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--recheck", action="store_true", help="對既有 jsonl 用目前的查核提示重查，未過者重生成")
    ap.add_argument("--notes", default="", help="轉傳給 generate_messages，逐則額外指示")
    ap.add_argument("--style", default="", choices=["", "colloquial"], help="轉傳給 generate_messages")
    args = ap.parse_args()
    gen.configure(args.notes, args.style)
    if args.recheck:
        kb = gen.load_kb()
        kb_by_id = {row["id"]: row for row in kb}
        kb_index = gen.index_kb(kb)
        cell_by = {(c["persona"], c["touchpoint"]): c for c in gen.cells()}
        rows = [json.loads(line) for line in gen.OUT.read_text(encoding="utf-8").splitlines() if line.strip()]
        updated = []
        for i, rec in enumerate(rows):
            fc = check_once(rec, kb_by_id)
            rec["factcheck"] = fc
            print(
                f"recheck {rec['persona']} {rec['touchpoint']} pass={fc['passed']} "
                f"{fc['supported']}/{fc['total']} reasons={fc['reasons'][:4]}",
                flush=True,
            )
            attempt = int(rec.get("attempt") or 1)
            while not fc["passed"] and attempt < MAX_ATTEMPTS:
                cell = cell_by[(rec["persona"], rec["touchpoint"])]
                feedback = "\n".join(f"- {r}" for r in fc["reasons"])
                attempt += 1
                rec = gen.generate_cell(cell, kb_index, feedback=feedback, attempt=attempt)
                fc = check_once(rec, kb_by_id)
                rec["factcheck"] = fc
                rec["regen_count"] = attempt - 1
                print(
                    f"regen {rec['persona']} {rec['touchpoint']} attempt={attempt} "
                    f"pass={fc['passed']} reasons={fc['reasons'][:4]}",
                    flush=True,
                )
            updated.append(rec)
            gen.write_jsonl(updated + rows[i + 1:])
        write_examples(updated)
        passed = sum(1 for r in updated if r.get("factcheck", {}).get("passed"))
        regens = sum(r.get("regen_count", 0) for r in updated)
        print(f"passed {passed}/{len(updated)} regenerations {regens}", flush=True)
        return
    kb = gen.load_kb()
    kb_by_id = {row["id"]: row for row in kb}
    kb_index = gen.index_kb(kb)
    chosen = gen.cells()
    if args.only:
        name, tp = args.only.split(":")
        chosen = [c for c in chosen if c["persona"] == name and c["touchpoint"] == tp]
    results = []
    for cell in chosen:
        results.append(run_cell(cell, kb_index, kb_by_id))
        if not args.only:
            gen.write_jsonl(results)
    if not args.only:
        gen.write_jsonl(results)
        write_examples(results)
        passed = sum(1 for r in results if r.get("factcheck", {}).get("passed"))
        regens = sum(r.get("regen_count", 0) for r in results)
        print(f"passed {passed}/{len(results)} regenerations {regens}", flush=True)
        print(f"wrote {EXAMPLES}", flush=True)
    else:
        print(json.dumps(results[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
