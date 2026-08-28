from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_fresh_clone_onboarding_contract():
    agents = (ROOT / "AGENTS.md").read_text()
    catalog = (ROOT / "skills/CATALOG.md").read_text()
    skill = (ROOT / "skills/onboard-observatory/SKILL.md").read_text()
    compatibility = (
        ROOT
        / "skills/onboard-observatory/references/instruction-compatibility.md"
    ).read_text()
    preservation = (
        ROOT / "skills/onboard-observatory/references/preservation-and-rollback.md"
    ).read_text()
    interview = (
        ROOT
        / "skills/onboard-observatory/references/operating-system-interview.md"
    ).read_text()

    assert "skills/onboard-observatory/SKILL.md" in agents
    assert "| Onboard Observatory |" in catalog
    assert "Ask for exactly one answer per conversational turn" in skill
    assert "Use at most one question mark" in skill
    assert "Explain the system before interviewing" in skill
    assert "The opening response must contain four explicit parts" in skill
    assert "Do not compress these into a generic promise to be careful" in skill
    assert "Do not ask for paths, exclusions, preferences" in skill
    assert "Would you like to begin the read-only onboarding interview?" in skill
    assert "Which single knowledge or repository root should I inventory first?" in skill
    assert "Do not claim zero compatibility risk" in skill
    assert "Preserving an imported rule does not make it authoritative" in skill
    assert "Default to preserving every existing instruction file byte-for-byte" in skill
    assert "compact onboarding blueprint" in skill
    assert "Silence, continued conversation, approval to inventory" in skill
    assert "Make a verified preservation snapshot" in skill
    assert "If any source cannot be copied or verified, do not modify it" in skill
    for filename in ("AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md"):
        assert f"`{filename}`" in compatibility
    assert "Do not execute commands" in compatibility
    assert "Approval to perform the read-only inventory is not approval" in compatibility
    assert "Hash every backup copy independently" in preservation
    assert "Rollback is a separate write operation" in preservation
    assert "never describe rollback as complete" in preservation
    assert "Start with a recent real workflow" in interview
    assert "Keep unused topics in an internal queue" in interview
    assert "Do not turn the topic lists below into a questionnaire" in interview
    assert "Translate answers into a reviewable blueprint" in interview


def test_obsidian_local_state_and_first_run_contract():
    ignored = (ROOT / ".gitignore").read_text().splitlines()
    readme = (ROOT / "README.md").read_text()
    start = (ROOT / "START-HERE.md").read_text()

    assert ".obsidian/" in ignored
    assert "open the repository root directly as an Obsidian vault" in readme
    assert "no community plugin is required" in readme
    assert "Open folder as vault" in start
    assert "CLI and Mission Control do not depend on Obsidian" in start


def test_observatory_policy_primary_and_legacy_mirror_match():
    for filename in (
        "destructive-change-approvals.yaml",
        "ontology.yaml",
        "policies.yaml",
        "schema.yaml",
        "validation.yaml",
    ):
        assert (ROOT / ".observatory" / filename).read_bytes() == (
            ROOT / ".brain" / filename
        ).read_bytes()


def test_narrated_progress_recording_contract():
    agents = (ROOT / "AGENTS.md").read_text()
    skill = (ROOT / "skills/narrated-progress-recording/SKILL.md").read_text()
    assert "skills/narrated-progress-recording/SKILL.md" in agents
    for status in ("produced", "deferred", "not applicable"):
        assert f"`{status}`" in skill
    assert "exact source revision" in skill
    assert "external service without exact user authorization" in skill
    assert "Never publish, message, email, or upload" in skill


def test_review_workflow_contract():
    review = (ROOT / "skills/observatory-review/SKILL.md").read_text()
    agents = (ROOT / "AGENTS.md").read_text()
    assert "skills/observatory-review/SKILL.md" in agents
    for mode in ("combined", "unverified", "staged", "stale", "disputed"):
        assert f"**{mode}**" in review
    assert "Return 7 cards by default" in review
    assert "Git-tracked candidate Markdown under `staging/`" in review
    for state in ("unverified", "machine-confirmed", "human-reviewed"):
        assert f"**{state}**" in review
    assert "Never interpret praise, liking, a thumbs-up" in review


def test_deep_research_alias_and_required_sections():
    research = (ROOT / "skills/research/SKILL.md").read_text()
    assert "Treat **Brief this** and **Research this** as aliases" in research
    for section in (
        "findings",
        "evidence",
        "disagreement",
        "uncertainty",
        "implications",
        "value",
        "investment",
        "pitfalls",
        "recommendations",
    ):
        assert section.lower() in research.lower()
    for action in ("Discard", "Stage this", "Brain this", "Verify this"):
        assert f"**{action}**" in research
    assert "non-persistent by default" in research
    assert "never counts as human verification" in research


def test_staging_and_session_capture_contracts():
    staging = ROOT / "staging/README.md"
    session = (ROOT / "skills/session-capture/SKILL.md").read_text()
    agents = (ROOT / "AGENTS.md").read_text()
    assert staging.is_file()
    assert "not canonical knowledge" in staging.read_text()
    assert "skills/session-capture/SKILL.md" in agents
    for trigger in ("Remember this session", "Brain this session", "Save project handoff"):
        assert f"**{trigger}**" in session
    assert "Never save a raw transcript by default" in session
    assert "Update the matching `projects/*.md` card" in session
    assert "repository-wide operating policy belongs in the root `AGENTS.md`" in session
    assert (
        "Never edit machine-wide or provider-global instruction files outside this repository"
        in session
    )
    for action in ("Discard", "Stage session", "Brain session", "Update project", "Edit preview"):
        assert f"**{action}**" in session
    assert "does not create a human verification event" in session


def test_paid_model_capacity_handoff_contract():
    agents = (ROOT / "AGENTS.md").read_text()
    handoff = (ROOT / "skills/session-handoff/SKILL.md").read_text()
    architecture = (ROOT / "docs/architecture.md").read_text()
    monitor = (ROOT / "docs/ai-provider-capacity-monitor.md").read_text()
    policies = (ROOT / ".observatory/policies.yaml").read_text()

    assert "paid AI model" in agents
    for limit_kind in ("usage", "context", "rate", "credit", "subscription"):
        assert limit_kind in agents
    assert "skills/session-handoff/SKILL.md" in agents
    assert "park/stop work before exhaustion" in agents
    assert "Non-negotiable cost/capacity rule" in agents
    assert "No agent, model, automation, or orchestration system may autonomously" in agents
    assert "Explicit user approval is required for every such increase" in agents
    assert "Never solve capacity exhaustion by increasing spend" in agents

    for required_state in (
        ".ops/PROJECT_STATUS.md",
        "Capacity / parking state",
        "pitfalls",
        "next actions",
        "park cleanly",
    ):
        assert required_state in handoff

    assert "Capacity monitor and failover coordinator" in architecture
    assert "automation plane" in architecture
    assert "not canonical knowledge" in architecture
    assert "ai-provider-capacity-monitor.md" in architecture

    for provider_state in ("available", "degraded", "parked", "exhausted"):
        assert f"`{provider_state}`" in monitor
    for behavior in (
        "Graceful degradation for missing telemetry",
        "Manual controls",
        "Audit log",
        "Cooldown, retry, and recovery",
        "already-authorized provider",
        "successor must acknowledge",
        "paused queue and user notification",
    ):
        assert behavior in monitor
    for prohibited_change in (
        "purchase credits",
        "raise limits or spend caps",
        "change plan tiers",
        "add paid capacity",
    ):
        assert prohibited_change in monitor

    assert "paid_ai_capacity:" in policies
    assert "autonomous_capacity_increase: false" in policies
    assert "increase_requires_explicit_user_approval: true" in policies
    assert (
        "No monitor, agent, model, automation, coordinator, or other system component"
        in architecture
    )
    assert "without explicit user approval for that specific increase" in architecture


def test_concurrency_and_observation_promotion_contracts():
    agents = (ROOT / "AGENTS.md").read_text()
    handoff = (ROOT / "skills/session-handoff/SKILL.md").read_text()
    observation = (ROOT / "skills/observation-promotion/SKILL.md").read_text()
    concurrency = (ROOT / "docs/concurrency-contract.md").read_text()
    template = (ROOT / "staging/observation-template.md").read_text()

    assert "skills/observation-promotion/SKILL.md" in agents
    assert "Working ownership / overlap" in handoff
    assert "observatory overlap" in handoff
    assert "same-path overlap" in concurrency
    assert 'unconditional "ours" or "theirs"' in concurrency
    assert "never automatically promoted" in observation.lower()
    for action in ("Discard", "Stage observation", "Brain this observation", "Edit proposal"):
        assert f"**{action}**" in observation
    for section in ("Scope and time", "Evidence", "Relationship to current knowledge"):
        assert f"## {section}" in template
