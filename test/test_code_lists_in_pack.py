"""Every Master Data list and code the Agents Registry uses is in every country pack.

The forms' dropdowns and the training checks read the AGENT_* lists live from
Master Data, and the sample trainings use fixed codes of them. A list or code
missing from a pack would show as an empty dropdown or a rejected activity on a
live install; here it fails the build. Codes are the same in every pack (a
country changes labels, not codes), so the check covers each pack.
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import agents_definitions as d  # noqa: E402
from master_data_pack import PACKS, codes, load_lists, pack_dir  # noqa: E402

SAMPLES = (REPO / "agents-extension/src/openg2p_registry_agents_extension/register_domain/services"
           / "agent_training_samples.py")


def _samples():
    """agent_training_samples.py, read as source: CI runs these checks without the platform installed."""
    import ast

    tree = ast.parse(SAMPLES.read_text())
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                values[node.targets[0].id] = ast.literal_eval(node.value)
            except ValueError:
                pass

    class Samples:
        COURSES = values["COURSES"]
        DEFAULT_COURSE = values["DEFAULT_COURSE"]

    return Samples


def _lists_in_forms() -> set[str]:
    found = set()

    def walk(node):
        if isinstance(node, dict):
            source = node.get("widget-data-source") or {}
            if source.get("service") == "attributes":
                found.add(source["params"]["attribute_id"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    for section in d.SECTIONS:
        walk(section["section_ui_schema"])
    return found


def _lists_in_activities() -> set[str]:
    return {rule["attribute"] for t in d.ACTIVITY_TYPES for rule in t["reference_rules"].values()
            if rule["kind"] == "ATTRIBUTE"}


@pytest.fixture(params=PACKS)
def pack(request):
    found = pack_dir(request.param)
    if found is None:
        pytest.skip("openg2p-data is not checked out beside this repo (set OPENG2P_DATA_DIR)")
    return load_lists(found)


def test_every_list_is_in_the_pack(pack):
    used = _lists_in_forms() | _lists_in_activities() | set(d.RECORD_LISTS.values()) | set(d.ACTIVITY_LISTS.values())
    assert used, "no lists found in the definitions"
    assert sorted(used - set(pack)) == []


def test_every_form_list_is_declared():
    # RECORD_LISTS is the documented list of the record's coded fields: keep it complete.
    assert _lists_in_forms() <= set(d.RECORD_LISTS.values())


def test_sample_training_codes_are_in_the_pack(pack):
    s = _samples()

    topics = {topic for topic, _, _ in s.COURSES.values()} | {s.DEFAULT_COURSE[0], "AGTOP_DIGITAL_TOOLS"}
    assert topics <= codes(pack["AGENT_TRAINING_TOPIC"])
    assert {"AGTDM_IN_PERSON", "AGTDM_ONLINE"} <= codes(pack["AGENT_TRAINING_DELIVERY_MODE"])
    assert {"AGTRS_PASSED", "AGTRS_COMPLETED"} <= codes(pack["AGENT_TRAINING_RESULT"])
    assert set(s.COURSES) <= codes(pack["AGENT_SPECIALIZATION"])


def test_lists_have_the_same_codes_in_every_pack():
    packs = {country: pack_dir(country) for country in PACKS}
    if not all(packs.values()):
        pytest.skip("openg2p-data is not checked out beside this repo (set OPENG2P_DATA_DIR)")
    loaded = {country: load_lists(path) for country, path in packs.items()}
    for code in sorted(set(d.RECORD_LISTS.values()) | set(d.ACTIVITY_LISTS.values())):
        if code == "GENDER":
            continue
        assert len({frozenset(codes(lists[code])) for lists in loaded.values()}) == 1, code


def test_eth_sample_agents_use_the_packs_codes():
    found = pack_dir("ETH")
    if found is None:
        pytest.skip("openg2p-data is not checked out beside this repo (set OPENG2P_DATA_DIR)")
    lists = load_lists(found)
    agents = json.loads((found / "samples" / "agents.json").read_text())
    assert len(agents) >= 20
    for agent in agents:
        for field, code in d.RECORD_LISTS.items():
            if agent.get(field) is not None and field in agent:
                assert agent[field] in codes(lists[code]), (agent["agent_id"], field)
        assert len(agent["agent_id"]) == 8 and agent["agent_id"].isdigit()
        assert sum(1 for s in agent["specializations"] if s["is_primary"]) == 1
