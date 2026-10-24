#!/usr/bin/env python3
"""Dependency-aware reasoning over Marble Skill Taxonomy JSON."""
from __future__ import annotations
import argparse, json, re, sys
from typing import Any

def records(payload: Any, keys: tuple[str, ...]) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in keys:
            if isinstance(payload.get(key), list):
                return [x for x in payload[key] if isinstance(x, dict)]
    raise ValueError(f"Expected a list or object containing one of {keys}")

def ident(topic: dict[str, Any]) -> str | None:
    return next((topic[k] for k in ("id", "topicId", "topic_id") if isinstance(topic.get(k), str)), None)

def label(topic: dict[str, Any]) -> str:
    return next((topic[k].strip() for k in ("title", "name", "label", "topic", "titleText")
                 if isinstance(topic.get(k), str) and topic[k].strip()), ident(topic) or "(unnamed topic)")

def select_target(topics: list[dict[str, Any]], query: str) -> dict[str, Any]:
    terms = [w for w in re.findall(r"[\w'-]+", query.lower()) if len(w) > 1]
    if not terms:
        raise ValueError("Query must contain meaningful words")
    scored = []
    for topic in topics:
        text = " ".join(str(v) for v in topic.values() if isinstance(v, (str, int, float))).lower()
        title = label(topic).lower()
        score = sum(3 if word in title else 1 if word in text else 0 for word in terms)
        if score:
            scored.append((score, topic))
    if not scored:
        raise LookupError(f"No topic matched {query!r}")
    scored.sort(key=lambda pair: (-pair[0], label(pair[1]).lower()))
    tied = [topic for score, topic in scored if score == scored[0][0]]
    if len(tied) > 1:
        raise LookupError("Ambiguous target; refine query. Top matches: " + ", ".join(label(t) for t in tied[:5]))
    return scored[0][1]

def prerequisite_map(edges: list[dict[str, Any]], include_soft: bool = False) -> dict[str, list[dict[str, Any]]]:
    graph: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        dependent = edge.get("topicId", edge.get("topic_id"))
        prerequisite = edge.get("prerequisiteId", edge.get("prerequisite_id"))
        if not isinstance(dependent, str) or not isinstance(prerequisite, str):
            continue
        if edge.get("strength", "hard") != "hard" and not include_soft:
            continue
        graph.setdefault(dependent, []).append(edge)
    return graph

def ordered_dependencies(target: str, graph: dict[str, list[dict[str, Any]]]) -> list[str]:
    result, done, active = [], set(), []
    def visit(node: str) -> None:
        if node in done: return
        if node in active:
            raise ValueError("Cycle detected: " + " -> ".join(active[active.index(node):] + [node]))
        active.append(node)
        for edge in graph.get(node, []):
            pre = edge.get("prerequisiteId", edge.get("prerequisite_id"))
            if isinstance(pre, str): visit(pre)
        active.pop(); done.add(node); result.append(node)
    visit(target)
    return result

def fixture():
    topics = [
        {"id":"t1","title":"Recognize numbers","description":"Identify numerals and quantities"},
        {"id":"t2","title":"Add single-digit numbers","description":"Combine small quantities"},
        {"id":"t3","title":"Add two-digit numbers","description":"Use place value to add two-digit numbers"},
    ]
    edges = [
        {"topicId":"t3","prerequisiteId":"t2","strength":"hard","reason":"Two-digit addition depends on basic addition"},
        {"topicId":"t2","prerequisiteId":"t1","strength":"hard","reason":"Addition depends on number recognition"},
    ]
    return topics, edges, "Add two-digit numbers"

def run(topics: list[dict[str, Any]], edges: list[dict[str, Any]], query: str, include_soft: bool = False):
    index = {ident(t): t for t in topics if ident(t)}
    target = select_target(topics, query)
    target_id = ident(target)
    if not target_id: raise ValueError("Matched topic has no recognized ID")
    graph = prerequisite_map(edges, include_soft)
    order = ordered_dependencies(target_id, graph)
    plan = []
    for node in order:
        topic = index.get(node)
        plan.append({"id":node,"title":label(topic) if topic else "[missing topic record]",
                     "status":"target" if node == target_id else ("prerequisite" if topic else "unresolved")})
    reasons = []
    for node in order:
        for edge in graph.get(node, []):
            pre = edge.get("prerequisiteId", edge.get("prerequisite_id"))
            if pre in order:
                reasons.append({"from":label(index[node]) if node in index else node,
                    "requires":label(index[pre]) if pre in index else pre,
                    "strength":edge.get("strength","hard"),"reason":edge.get("reason","")})
    return {"query":query,"matched_target":label(target),"target_id":target_id,
            "dependency_count":max(0,len(plan)-1),"ordered_plan":plan,"dependency_reasons":reasons,
            "limits":["A prerequisite edge does not prove mastery.",
                      "Lexical target matching must be reviewed when ambiguous."]}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--topics"); p.add_argument("--dependencies"); p.add_argument("--query")
    p.add_argument("--include-soft",action="store_true"); p.add_argument("--fixture",action="store_true")
    a=p.parse_args(argv)
    if a.fixture or not (a.topics and a.dependencies and a.query):
        topics, edges, query = fixture(); result=run(topics,edges,query,a.include_soft); result["mode"]="fixture"
    else:
        with open(a.topics,encoding="utf-8") as f: topics=records(json.load(f),("topics","items","data"))
        with open(a.dependencies,encoding="utf-8") as f: edges=records(json.load(f),("dependencies","edges","items","data"))
        result=run(topics,edges,a.query,a.include_soft); result["mode"]="local-os-taxonomy-data"
    print(json.dumps(result,indent=2,ensure_ascii=False)); return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except (ValueError, LookupError, OSError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}",file=sys.stderr); raise SystemExit(2)
