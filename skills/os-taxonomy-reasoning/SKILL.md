---
name: os-taxonomy-reasoning
description: Use a prerequisite graph to break a question into concepts, resolve dependencies, and produce a verified order of work. Use with a local checkout of lattmamb/os-taxonomy; its current dataset is education-focused, not a universal agent ontology.
---

# OS Taxonomy Reasoning

Use this skill when the task benefits from explicit prerequisites, concept sequencing, or identifying missing foundations.

## Procedure

1. **Define the target.** State the requested outcome as one specific concept, skill, decision, or deliverable.
2. **Resolve the data domain.** Use Marble Skill Taxonomy only for concepts actually represented in its educational dataset. Do not pretend its K–12 topic graph describes software, finance, or general agent work.
3. **Find the target node.** Search topic titles and descriptions. If multiple candidates are equally plausible, stop and request a more precise target rather than silently choosing.
4. **Traverse prerequisite edges.** In `data/dependencies.json`, `topicId` depends on `prerequisiteId`. Include hard dependencies by default; include soft edges only when useful and label them.
5. **Order prerequisites before the target.** Detect cycles, missing topic records, and unresolved dependencies. Never hide graph errors.
6. **Check evidence.** A prerequisite edge is a sequencing recommendation, not proof that a learner has mastered the prerequisite. Use available assessment evidence; otherwise mark mastery as unknown.
7. **Act and verify.** Produce the ordered plan, execute the next appropriate step, and check the result against an explicit success criterion.
8. **Report provenance.** Distinguish facts read from the taxonomy from reasoning added by the agent. Do not claim the taxonomy supports a concept it does not contain.

## Run the executable demonstration

From a checkout of this repository:

```bash
python examples/os-taxonomy-reasoning/os_taxonomy_reasoning.py --fixture
python -m unittest discover -s examples/os-taxonomy-reasoning -p 'test_*.py' -v
```

To query the actual taxonomy checkout:

```bash
python examples/os-taxonomy-reasoning/os_taxonomy_reasoning.py \
  --topics /path/to/os-taxonomy/data/topics.json \
  --dependencies /path/to/os-taxonomy/data/dependencies.json \
  --query "your specific topic"
```

This is a graph-navigation helper, not an LLM, not a mastery detector, and not a universal knowledge graph.