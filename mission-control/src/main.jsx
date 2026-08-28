import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const BASE = import.meta.env.BASE_URL || './';

const icons = {
  grid: <><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></>,
  radar: <><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><path d="M12 12l6-4"/><circle cx="17.8" cy="8.1" r="1.3"/></>,
  x: <><path d="M5 4l14 16M19 4L5 20"/></>,
  refresh: <><path d="M20 11a8 8 0 10-2.3 5.7"/><path d="M20 4v7h-7"/></>,
  arrow: <><path d="M5 12h14M14 7l5 5-5 5"/></>,
  git: <><circle cx="6" cy="5" r="2"/><circle cx="18" cy="7" r="2"/><circle cx="6" cy="19" r="2"/><path d="M6 7v10M8 6c5 0 3 1 8 1"/></>,
  atlas: <><circle cx="12" cy="12" r="2.5"/><circle cx="5" cy="7" r="1.5"/><circle cx="19" cy="6" r="1.5"/><circle cx="18" cy="18" r="1.5"/><circle cx="6" cy="18" r="1.5"/><path d="M7 8l3 2.5M14 10l3.5-3M14 14l3 3M10 14l-3 3"/></>,
};

function Icon({ name, size = 18 }) { return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{icons[name]}</svg>; }
function formatDate(value) { if (!value) return 'Awaiting first run'; const date = new Date(value); return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(date); }
function timeAgo(value) { if (!value) return 'not available'; const delta = Date.now() - new Date(value).getTime(); if (delta < 60000) return 'just now'; if (delta < 3600000) return `${Math.floor(delta / 60000)}m ago`; if (delta < 86400000) return `${Math.floor(delta / 3600000)}h ago`; return `${Math.floor(delta / 86400000)}d ago`; }
function StateDot({ state = 'unknown' }) { return <span className={`state-dot ${state}`} aria-hidden="true" />; }
function Badge({ children, tone = 'neutral' }) { return <span className={`badge ${tone}`}>{children}</span>; }

function Header({ tab, setTab, snapshot, refreshing, onRefresh }) {
  return <>
    <header className="topbar">
      <button className="brand" onClick={() => setTab('mission')} aria-label="Observatory Mission Control home"><span className="brand-symbol"><i /></span><span><strong>Observatory</strong><small>Mission Control</small></span></button>
      <nav className="desktop-nav" aria-label="Primary navigation">
        <NavButton id="mission" label="Overview" icon="grid" tab={tab} setTab={setTab}/>
        <NavButton id="atlas" label="Atlas" icon="atlas" tab={tab} setTab={setTab}/>
        <NavButton id="airadar" label="AIRadar" icon="radar" tab={tab} setTab={setTab}/>
        <NavButton id="x" label="X Posts" icon="x" tab={tab} setTab={setTab}/>
      </nav>
      <div className="header-actions"><span className="privacy"><span className="pulse"/>{snapshot.readOnly ? 'Authenticated share · read-only' : 'Local only'}</span><button className="icon-button" onClick={onRefresh} disabled={refreshing} title="Refresh local project status"><Icon name="refresh"/></button></div>
    </header>
    <nav className="mobile-nav" aria-label="Primary navigation">
      <NavButton id="mission" label="Home" icon="grid" tab={tab} setTab={setTab}/>
      <NavButton id="atlas" label="Atlas" icon="atlas" tab={tab} setTab={setTab}/>
      <NavButton id="airadar" label="AIRadar" icon="radar" tab={tab} setTab={setTab}/>
      <NavButton id="x" label="X Posts" icon="x" tab={tab} setTab={setTab}/>
    </nav>
  </>;
}
function NavButton({ id, label, icon, tab, setTab }) { return <button className={tab === id ? 'active' : ''} onClick={() => setTab(id)}><Icon name={icon}/><span>{label}</span></button>; }

function Stat({ label, value, detail, tone = '' }) { return <article className={`stat ${tone}`}><span>{label}</span><strong>{value}</strong><small>{detail}</small></article>; }

function ProjectCard({ project, onArchive, onKeepArchived, readOnly }) {
  const healthLabel = project.health === 'healthy' ? 'Healthy' : project.health === 'setup' ? 'Setup needed' : 'Watch';
  return <article className={`project-card ${project.accent}${project.archived ? ' archived' : ''}`}>
    <div className="project-top"><div><span className="project-kind">{project.kind}</span><h2>{project.name}</h2></div><Badge tone={project.health}><StateDot state={project.health}/>{healthLabel}</Badge></div>
    <p className="project-description">{project.objective || project.description}</p>
    <div className="project-strip">
      <div><span>CI</span><strong className={project.ci}>{project.ci || 'unknown'}</strong></div>
      <div><span>Open PRs</span><strong>{project.openPrs ?? '—'}</strong></div>
      <div><span>Issues</span><strong>{project.openIssues ?? '—'}</strong></div>
    </div>
    {project.archiveAttention ? <div className="archive-alert"><div><Badge tone="setup">New activity</Badge><strong>Is this still archived?</strong><p>The repository changed after it was archived.</p></div>{readOnly ? null : <div><button onClick={() => onKeepArchived(project)}>Keep archived</button><button className="restore" onClick={() => onArchive(project, false)}>Restore project</button></div>}</div> : null}
    <div className="project-footer"><span><Icon name="git" size={15}/>{project.git ? `${project.git.branch} · ${project.git.head}${project.git.dirty ? ' · changes' : ''}` : project.phase || 'Not checked out'}</span>{readOnly ? null : <button className="project-action" onClick={() => onArchive(project, !project.archived)}>{project.archived ? 'Restore' : 'Archive'}</button>}</div>
  </article>;
}

function MissionView({ snapshot, onArchive, onKeepArchived }) {
  const projects = snapshot.projects || [];
  const activeProjects = projects.filter((project) => !project.archived);
  const archivedProjects = projects.filter((project) => project.archived);
  const healthy = activeProjects.filter((p) => p.health === 'healthy').length;
  const blockers = activeProjects.flatMap((p) => (p.blockers || []).map((item) => ({ project: p.name, item })));
  const prs = activeProjects.reduce((sum, p) => sum + (Number(p.openPrs) || 0), 0);
  return <main className="page mission-page">
    <section className="hero"><div><span className="eyebrow">Everything worth keeping is connected</span><h1>Observatory command center.</h1><p>Your projects, signals, knowledge, and loose ends—one calm place to see what needs attention.</p></div><div className="freshness"><span>Last refresh</span><strong>{timeAgo(snapshot.generatedAt)}</strong><small>{snapshot.mode === 'local-live' ? 'Reading local checkouts' : 'Using generic starter data'}</small></div></section>
    <section className="stats-grid"><Stat label="Projects online" value={`${healthy}/${activeProjects.length}`} detail="healthy active projects" tone="green"/><Stat label="Open pull requests" value={prs} detail={snapshot.githubEnabled ? 'live GitHub data' : 'saved snapshot'} tone="blue"/><Stat label="Needs attention" value={blockers.length} detail="setup items + blockers" tone="amber"/><Stat label="AIRadar signals" value={(snapshot.airadar?.daily?.trends || []).length} detail="latest daily report" tone="violet"/></section>
    <div className="section-heading"><div><span className="eyebrow">Portfolio</span><h2>Active projects</h2></div><span>{activeProjects.length} active</span></div>
    <section className="projects-grid">{activeProjects.map((project) => <ProjectCard key={project.id} project={project} onArchive={onArchive} onKeepArchived={onKeepArchived} readOnly={snapshot.readOnly}/>)}</section>
    {archivedProjects.length ? <details className={`archived-section${archivedProjects.some((project) => project.archiveAttention) ? ' needs-review' : ''}`}><summary><span><span className="eyebrow">Archive</span><strong>Archived projects</strong></span><Badge tone={archivedProjects.some((project) => project.archiveAttention) ? 'setup' : 'neutral'}>{archivedProjects.some((project) => project.archiveAttention) ? 'Activity detected' : archivedProjects.length}</Badge></summary><section className="projects-grid">{archivedProjects.map((project) => <ProjectCard key={project.id} project={project} onArchive={onArchive} onKeepArchived={onKeepArchived} readOnly={snapshot.readOnly}/>)}</section></details> : null}
    <section className="bottom-grid">
      <article className="attention-panel"><div className="panel-title"><div><span className="eyebrow">Attention queue</span><h2>What to unblock next</h2></div><Badge tone={blockers.length ? 'setup' : 'healthy'}>{blockers.length || 'Clear'}</Badge></div>{blockers.length ? <div className="attention-list">{blockers.map((blocker, index) => <div className="attention-row" key={`${blocker.project}-${index}`}><span className="attention-number">{String(index + 1).padStart(2, '0')}</span><div><strong>{blocker.project}</strong><p>{blocker.item}</p></div></div>)}</div> : <p className="empty-copy">Nothing is blocked right now.</p>}</article>
      <article className="system-panel"><span className="eyebrow">Data boundary</span><h2>Private by design</h2><p>Mission Control reads known local project folders and generated report JSON. It does not store credentials or local filesystem paths in the browser snapshot.</p><div className="system-row"><span>Dashboard binding</span><strong>127.0.0.1</strong></div><div className="system-row"><span>Access mode</span><strong>{snapshot.readOnly ? 'Shared read-only' : 'Local owner'}</strong></div><div className="system-row"><span>GitHub live refresh</span><strong>{snapshot.githubEnabled ? 'Enabled' : 'Opt-in'}</strong></div><div className="system-row"><span>Local checkouts found</span><strong>{projects.filter((p) => p.local).length}</strong></div></article>
    </section>
  </main>;
}

const atlasTone = { Project: 'project', Concept: 'concept', ResearchDossier: 'research', Idea: 'idea', Question: 'question' };

function atlasPositions(nodes) {
  const positions = {};
  const projects = nodes.filter((node) => node.type === 'Project');
  const knowledge = nodes.filter((node) => node.type !== 'Project');
  function placeRing(ring, radius, phase = -Math.PI / 2) {
    ring.forEach((node, index) => {
      const angle = phase + (index / Math.max(ring.length, 1)) * Math.PI * 2;
      positions[node.id] = { x: 500 + Math.cos(angle) * radius, y: 350 + Math.sin(angle) * radius };
    });
  }
  if (projects.length === 1) positions[projects[0].id] = { x: 500, y: 350 };
  else placeRing(projects, projects.length <= 4 ? 120 : 165);
  if (knowledge.length <= 18) placeRing(knowledge, 285, -Math.PI / 2 + Math.PI / Math.max(knowledge.length, 1));
  else if (knowledge.length <= 36) {
    const split = Math.ceil(knowledge.length / 2);
    placeRing(knowledge.slice(0, split), 235);
    placeRing(knowledge.slice(split), 310, -Math.PI / 2 + Math.PI / Math.max(knowledge.length - split, 1));
  } else {
    placeRing(knowledge.slice(0, 12), 205);
    placeRing(knowledge.slice(12, 30), 265, -Math.PI / 2 + Math.PI / 18);
    placeRing(knowledge.slice(30), 320, -Math.PI / 2 + Math.PI / Math.max(knowledge.length - 30, 1));
  }
  return positions;
}

function AtlasView({ snapshot }) {
  const atlas = snapshot.atlas || { nodes: [], edges: [] };
  const [filter, setFilter] = useState('all');
  const [selectedId, setSelectedId] = useState(atlas.nodes.find((node) => node.type === 'Project')?.id || atlas.nodes[0]?.id || '');
  const nodes = useMemo(() => atlas.nodes.filter((node) => filter === 'all' || node.type === filter).slice(0, 60), [atlas.nodes, filter]);
  const visibleIds = useMemo(() => new Set(nodes.map((node) => node.id)), [nodes]);
  const edges = useMemo(() => atlas.edges.filter((edge) => visibleIds.has(edge.source) && visibleIds.has(edge.target)), [atlas.edges, visibleIds]);
  const positions = useMemo(() => atlasPositions(nodes), [nodes]);
  const selected = atlas.nodes.find((node) => node.id === selectedId) || nodes[0];
  const connectedIds = useMemo(() => new Set(atlas.edges.flatMap((edge) => edge.source === selectedId ? [edge.target] : edge.target === selectedId ? [edge.source] : [])), [atlas.edges, selectedId]);
  const connected = atlas.nodes.filter((node) => connectedIds.has(node.id));
  const types = ['all', 'Project', 'Concept', 'ResearchDossier', 'Idea', 'Question'];
  return <main className="page atlas-page">
    <section className="hero compact"><div><span className="eyebrow">Connected knowledge, on demand</span><h1>The Atlas</h1><p>A simple projection of the ordinary Markdown links already in Observatory. Open it when relationships help; ignore it when a list is clearer.</p></div><div className="freshness"><span>Map source</span><strong>{atlas.source || 'Canonical links'}</strong><small>{atlas.nodes.length} objects · {atlas.edges.length} connections</small></div></section>
    <div className="atlas-filters" role="group" aria-label="Filter Atlas objects">{types.map((type) => <button key={type} className={filter === type ? 'active' : ''} onClick={() => setFilter(type)}>{type === 'all' ? 'Everything' : type === 'ResearchDossier' ? 'Research' : `${type}s`}</button>)}</div>
    <section className="atlas-layout">
      <article className="atlas-canvas">
        {nodes.length ? <svg viewBox="0 0 1000 700" role="img" aria-label="Connected Observatory knowledge map">
          <defs><filter id="glow"><feGaussianBlur stdDeviation="4" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
          {edges.map((edge) => { const a = positions[edge.source]; const b = positions[edge.target]; const active = selectedId && (edge.source === selectedId || edge.target === selectedId); return a && b ? <line key={`${edge.source}-${edge.target}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y} className={active ? 'active' : ''}/> : null; })}
          {nodes.map((node, nodeIndex) => { const point = positions[node.id]; const active = node.id === selectedId; const adjacent = connectedIds.has(node.id); const showLabel = nodes.length <= 24 || active || node.type === 'Project' || (adjacent && connectedIds.size <= 10); const label = node.label.length > 24 ? `${node.label.slice(0, 23)}…` : node.label; const labelWidth = Math.max(78, Math.min(176, label.length * 7.2)); const labelDirection = point.y < 350 ? -1 : 1; const labelOffset = labelDirection * ((active ? 47 : 37) + (nodeIndex % 2) * 24); return <g key={node.id} className={`atlas-node ${atlasTone[node.type] || 'note'}${active ? ' selected' : ''}${adjacent ? ' adjacent' : ''}`} transform={`translate(${point.x} ${point.y})`} onClick={() => setSelectedId(node.id)} role="button" tabIndex="0" onKeyDown={(event) => (event.key === 'Enter' || event.key === ' ') && setSelectedId(node.id)} aria-label={`Open ${node.label}`}>
            <circle r={active ? 24 : node.type === 'Project' ? 19 : 14}/><circle className="node-ring" r={active ? 31 : node.type === 'Project' ? 25 : 19}/>{showLabel ? <g className="atlas-label" transform={`translate(0 ${labelOffset})`}><rect x={-labelWidth / 2} y="-12" width={labelWidth} height="22" rx="7"/><text y="3" textAnchor="middle">{label}</text></g> : null}
          </g>; })}
        </svg> : <div className="empty-copy">Add Markdown cards and ordinary links to populate the Atlas.</div>}
      </article>
      <aside className="atlas-inspector">
        {selected ? <><Badge tone={selected.type === 'Project' ? 'healthy' : 'neutral'}>{selected.type}</Badge><h2>{selected.label}</h2><p>{selected.description || 'No description has been added yet.'}</p><div className="inspector-row"><span>Status</span><strong>{selected.status || 'not specified'}</strong></div><div className="inspector-row"><span>Connections</span><strong>{selected.connections}</strong></div><span className="eyebrow related-label">Directly connected</span><div className="connection-list">{connected.length ? connected.map((node) => <button key={node.id} onClick={() => { setFilter('all'); setSelectedId(node.id); }}><span className={`connection-dot ${atlasTone[node.type] || 'note'}`}/><span><strong>{node.label}</strong><small>{node.type}</small></span><Icon name="arrow" size={14}/></button>) : <p>No direct Markdown links yet.</p>}</div></> : <><h2>No object selected</h2><p>Choose a point to inspect its connected ideas.</p></>}
      </aside>
    </section>
  </main>;
}

function ArchiveConfirmation({ project, onCancel, onConfirm }) {
  return <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onCancel()}><section className="confirm-modal" role="dialog" aria-modal="true" aria-labelledby="archive-title"><Badge tone="setup">Archive project</Badge><h2 id="archive-title">Archive {project.name}?</h2><p>It will leave Active Projects but remain available under Archived Projects. Nothing in the repository will be deleted.</p><div className="modal-actions"><button onClick={onCancel}>Cancel</button><button className="confirm" onClick={onConfirm}>Yes, archive it</button></div></section></div>;
}

const verificationLabel = { 'corroborated-primary': 'Corroborated', 'primary-plus-discussion': 'Primary + discussion', 'single-primary': 'Single primary', 'owner-priority-unverified': 'Owner priority', 'unverified-lead': 'Unverified lead' };
function plainText(value = '') { return value.replace(/<[^>]*>/g, ' ').replace(/[#*_`>\[\]]/g, '').replace(/\s+/g, ' ').trim(); }
function trendTldr(trend) {
  const raw = trend.ai_evaluation?.tldr || trend.summary || (trend.signals || []).find((signal) => signal.summary)?.summary || trend.recommendation || '';
  const clean = plainText(raw);
  if (clean.length <= 230) return clean;
  const shortened = clean.slice(0, 230);
  const sentence = shortened.lastIndexOf('. ');
  const cutoff = sentence > 100 ? sentence + 1 : shortened.lastIndexOf(' ');
  return `${shortened.slice(0, cutoff > 0 ? cutoff : 230)}…`;
}
function trendSummary(trend) {
  const raw = trend.ai_evaluation?.insight || trend.summary || (trend.signals || []).find((signal) => signal.summary)?.summary || trend.recommendation || trend.title || '';
  const clean = plainText(raw);
  if (clean.length <= 720) return clean;
  const shortened = clean.slice(0, 720);
  const sentence = shortened.lastIndexOf('. ');
  const cutoff = sentence > 380 ? sentence + 1 : shortened.lastIndexOf(' ');
  return `${shortened.slice(0, cutoff > 0 ? cutoff : 720)}…`;
}
function trendLatestTimestamp(trend) {
  return Math.max(0, ...(trend.signals || []).map((signal) => new Date(signal.published || signal.updated_at || 0).getTime()).filter(Number.isFinite));
}
function trendSourceGroup(trend) {
  const origins = (trend.origins || []).join(' ').toLowerCase();
  if (trend.verification === 'owner-priority-unverified' || /bookmark|owner|share/.test(origins)) return 'owner';
  if (origins.includes('arxiv')) return 'research';
  if (origins.includes('github')) return 'github';
  if (origins.includes('official:')) return 'official';
  return 'other';
}
function TrendCard({ trend, maxScore }) {
  const score = Number(trend.score || 0);
  const rank = trend._rank;
  const usefulness = trend.usefulness || { band: 'watch', project_matches: [], core_idea_matches: [] };
  const ai = trend.ai_evaluation;
  const priority = usefulness.band === 'act' ? 'Act' : usefulness.band === 'evaluate' ? 'Evaluate' : usefulness.band === 'skip' ? 'Skip' : 'Watch';
  const latest = trendLatestTimestamp(trend);
  return <article className="trend-card">
    <div className="rank-block"><span>Rank</span><strong>#{rank}</strong><small>{priority}</small></div>
    <div>
      <div className="trend-meta"><div><Badge tone={ai ? 'healthy' : 'neutral'}>{ai ? `AI evaluated · ${ai.confidence} confidence` : 'Heuristic rank · AI pending'}</Badge><Badge tone={trend.verification === 'corroborated-primary' ? 'healthy' : trend.verification === 'owner-priority-unverified' ? 'owner' : 'neutral'}>{verificationLabel[trend.verification] || trend.verification || 'Lead'}</Badge></div><div className="trend-numbers"><span>{score.toFixed(1)} signal</span>{latest ? <small>Latest {formatDate(latest)}</small> : null}</div></div>
      {Number.isFinite(Number(usefulness.score)) ? <div className="score-track" aria-label={`Estimated usefulness ${usefulness.score} out of 100`}><i style={{ width: `${Math.max(2, Math.min(100, usefulness.score))}%` }}/></div> : null}
      <h3>{trend.title}</h3>
      <div className="radar-connections"><div><span>Related projects</span><div>{(usefulness.project_matches || []).length ? usefulness.project_matches.map((project) => <Badge key={project.id} tone="healthy">{project.name} · {project.score}%</Badge>) : <small>No project match</small>}</div></div><div><span>Core ideas</span><div>{(usefulness.core_idea_matches || []).length ? usefulness.core_idea_matches.map((idea) => <Badge key={`${idea.project_id}-${idea.id}`} tone="owner">{idea.name}</Badge>) : <small>No core-idea match</small>}</div></div></div>
      <div className="origins"><span>{trend.signal_count ?? trend.signals?.length ?? 0} signals</span>{(trend.origins || []).slice(0, 2).map((origin) => <span key={origin}>{origin}</span>)}</div>
      <div className="trend-accordions"><details className="trend-section tldr-section" open><summary><span>TL;DR</span><small>{ai ? 'AI evaluation' : 'Heuristic fallback'}</small></summary><div className="section-body tldr"><p>{trendTldr(trend)}</p></div></details><details className="trend-section summary-section" open><summary><span>Insight</span><small>{ai ? 'AI synthesis' : 'Source context'}</small></summary><div className="section-body"><p>{trendSummary(trend)}</p>{ai?.why_it_matters ? <p><strong>Why it matters:</strong> {ai.why_it_matters}</p> : null}</div></details><details className="trend-section deep-dive"><summary><span>Full deep dive</span><small>Next action + {trend.signals?.length || 0} sources</small></summary><div className="deep-dive-body"><div className="why"><span className="eyebrow">Next action</span><p>{ai?.next_action || usefulness.next_action || trend.recommendation || 'Review the source evidence'}</p></div>{(trend.signals || []).map((signal, i) => <a className="signal" href={signal.url} target="_blank" rel="noreferrer" key={`${signal.url}-${i}`}><span>{signal.source || 'source'} · {formatDate(signal.published)}</span><strong>{signal.title || signal.url}</strong>{signal.summary ? <p>{plainText(signal.summary)}</p> : null}</a>)}</div></details></div>
    </div>
  </article>;
}

function AIRadarView({ snapshot, onSync, syncing }) {
  const [period, setPeriod] = useState('daily');
  const [query, setQuery] = useState('');
  const [sortBy, setSortBy] = useState('rank');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [verificationFilter, setVerificationFilter] = useState('all');
  const [sourceFilter, setSourceFilter] = useState('all');
  const [visibleLimit, setVisibleLimit] = useState(20);
  const report = snapshot.airadar?.[period] || { trends: [] };
  const trends = report.trends || [];
  const rankedTrends = useMemo(() => trends.map((trend, index) => ({ ...trend, _rank: index + 1 })), [trends]);
  const filtered = useMemo(() => rankedTrends.filter((trend) => {
    if (!JSON.stringify(trend).toLowerCase().includes(query.trim().toLowerCase())) return false;
    if (priorityFilter === 'top' && trend._rank > 5) return false;
    if (priorityFilter === 'high' && (trend._rank < 6 || trend._rank > 20)) return false;
    if (priorityFilter === 'monitor' && trend._rank <= 20) return false;
    if (verificationFilter !== 'all' && trend.verification !== verificationFilter) return false;
    if (sourceFilter !== 'all' && trendSourceGroup(trend) !== sourceFilter) return false;
    return true;
  }).sort((a, b) => {
    if (sortBy === 'latest') return trendLatestTimestamp(b) - trendLatestTimestamp(a) || a._rank - b._rank;
    if (sortBy === 'score') return Number(b.score || 0) - Number(a.score || 0) || a._rank - b._rank;
    if (sortBy === 'signals') return Number(b.signal_count || b.signals?.length || 0) - Number(a.signal_count || a.signals?.length || 0) || a._rank - b._rank;
    return a._rank - b._rank;
  }), [rankedTrends, query, priorityFilter, verificationFilter, sourceFilter, sortBy]);
  const maxScore = Number(trends[0]?.score || 0);
  const x = snapshot.airadar?.x || {};
  const sync = snapshot.airadar?.sync;
  const evaluation = snapshot.airadar?.aiEvaluation;
  const evaluated = trends.filter((trend) => trend.ai_evaluation).length;
  return <main className="page"><section className="hero compact"><div><span className="eyebrow">Signal intelligence</span><h1>AIRadar</h1><p>Ranked primary-source discovery and owner-priority evidence. The browser only renders AIRadar’s generated reports.</p></div><div className="radar-controls"><Badge tone={sync ? 'healthy' : 'setup'}>{sync?.runNumber ? `GitHub run #${sync.runNumber}` : 'Not synced'}</Badge>{snapshot.readOnly ? null : <button className="sync-button" onClick={onSync} disabled={syncing}><Icon name="refresh" size={15}/>{syncing ? 'Syncing…' : 'Sync latest'}</button>}<div className="segment"><button className={period === 'daily' ? 'active' : ''} onClick={() => { setPeriod('daily'); setVisibleLimit(20); }}>Today</button><button className={period === 'weekly' ? 'active' : ''} onClick={() => { setPeriod('weekly'); setVisibleLimit(20); }}>7 days</button></div></div></section>
    <section className="stats-grid"><Stat label="Ranked trends" value={trends.length} detail={sync?.runNumber ? `from run #${sync.runNumber}` : period === 'daily' ? 'today' : 'past seven days'} tone="green"/><Stat label="AI evaluated" value={evaluated} detail={evaluation ? `${evaluation.model} · top visible cards` : 'evaluation pending'} tone="blue"/><Stat label="Owner priority" value={trends.filter((t) => t.verification === 'owner-priority-unverified').length} detail="shares + bookmarks" tone="violet"/><Stat label="X connection" value={x.enabled ? 'Live' : 'Ready'} detail={x.enabled ? `${x.bookmarks?.length || 0} bookmarks` : 'OAuth needed'} tone="amber"/></section>
    <div className="airadar-layout"><section><div className="feed-tools"><div className="feed-search"><span>⌕</span><input aria-label="Search AIRadar" value={query} onChange={(event) => { setQuery(event.target.value); setVisibleLimit(20); }} placeholder="Search titles, summaries, sources, watches…"/>{query ? <button aria-label="Clear search" onClick={() => setQuery('')}>×</button> : null}</div><div className="feed-selects"><label><span>Sort</span><select value={sortBy} onChange={(event) => { setSortBy(event.target.value); setVisibleLimit(20); }}><option value="rank">AIRadar rank</option><option value="latest">Newest first</option><option value="score">Highest score</option><option value="signals">Most signals</option></select></label><label><span>Priority</span><select value={priorityFilter} onChange={(event) => { setPriorityFilter(event.target.value); setVisibleLimit(20); }}><option value="all">All ranks</option><option value="top">Top 5</option><option value="high">High signal</option><option value="monitor">Monitor</option></select></label><label><span>Verification</span><select value={verificationFilter} onChange={(event) => { setVerificationFilter(event.target.value); setVisibleLimit(20); }}><option value="all">All verification</option><option value="corroborated-primary">Corroborated</option><option value="primary-plus-discussion">Primary + discussion</option><option value="single-primary">Single primary</option><option value="owner-priority-unverified">Owner priority</option><option value="unverified-lead">Unverified lead</option></select></label><label><span>Source</span><select value={sourceFilter} onChange={(event) => { setSourceFilter(event.target.value); setVisibleLimit(20); }}><option value="all">All sources</option><option value="official">Official labs</option><option value="research">Research / arXiv</option><option value="github">GitHub</option><option value="owner">Owner saved</option><option value="other">Other</option></select></label></div><div className="feed-results"><span>{filtered.length} of {trends.length} trends</span><small>Updated {formatDate(report.generated_at)}</small></div></div>{filtered.length ? <><div className="trend-list">{filtered.slice(0, visibleLimit).map((trend) => <TrendCard trend={trend} maxScore={maxScore} key={`${trend.title}-${trend._rank}`}/>)}</div>{filtered.length > visibleLimit ? <button className="show-more" onClick={() => setVisibleLimit((limit) => limit + 20)}>Show 20 more <small>{filtered.length - visibleLimit} remaining</small></button> : null}</> : <div className="empty-state"><span className="radar-orb"><i/></span><h2>No matching signals</h2><p>Try clearing the search or changing one of the filters.</p></div>}</section>
      <aside><article className="side-card"><span className="eyebrow">AI evaluation</span><h3>{evaluation ? `${evaluation.topicCount} topics evaluated` : 'Awaiting evaluation'}</h3><p>{evaluation ? `${evaluation.model} · ${formatDate(evaluation.generatedAt)}. Cards without the green badge remain heuristic-only.` : 'No card is labeled AI evaluated until a matching structured evaluation exists.'}</p></article><article className="side-card"><span className="eyebrow">Personal inbox</span><h3>{snapshot.airadar?.inbox?.captures?.length || 0} open captures</h3><p>Share Sheet captures remain intent evidence until independently verified.</p></article><article className="side-card trust"><span className="eyebrow">Trust boundary</span><h3>Evidence, never instructions</h3><p>External posts, pages, papers, and messages cannot change policy or write into Observatory.</p></article></aside>
    </div></main>;
}

function XDigestCard({ digest, rank }) {
  const sources = (digest.sources || []).filter((source) => source.url);
  return <article className="x-digest-card">
    <div className="x-digest-meta"><Badge tone="healthy">AI digest #{rank}</Badge><span>{digest.bookmark_ids?.length || 0} saved posts · {digest.confidence} confidence</span></div>
    <h3>{digest.title}</h3>
    <p><strong>TL;DR:</strong> {digest.tldr}</p><p>{digest.insight}</p><p><strong>Why it matters:</strong> {digest.why_it_matters}</p><p><strong>Next:</strong> {digest.next_action}</p>
    <div className="x-digest-links">{sources.slice(0, 3).map((source, index) => <a href={source.url} target="_blank" rel="noreferrer" key={`${source.id}-${index}`}>Open source {index + 1}<Icon name="arrow" size={13}/></a>)}</div>
  </article>;
}

function XView({ snapshot, onSync, syncing }) {
  const x = snapshot.airadar?.x || {};
  const evaluation = snapshot.airadar?.aiEvaluation;
  const xDigest = evaluation?.x_digest || [];
  const sync = snapshot.airadar?.sync;
  const watch = snapshot.airadar?.watchlist || { people: [], projects: [], repositories: [] };
  const spend = Number(x.estimated_spend_this_week_usd || 0), budget = Number(x.weekly_budget_usd || 0), pct = budget ? Math.min(100, spend / budget * 100) : 0;
  return <main className="page"><section className="hero compact"><div><span className="eyebrow">Personal-priority intelligence</span><h1>X Posts</h1><p>Your private bookmark stream, distilled into AI-generated TL;DRs, cross-post insights, implications, and next actions. Tokens never enter the browser.</p></div><div className="radar-controls"><Badge tone={evaluation ? 'healthy' : 'setup'}><StateDot state={evaluation ? 'healthy' : 'setup'}/>{evaluation ? `AI synthesized · ${evaluation.model}` : 'AI synthesis pending'}</Badge>{snapshot.readOnly ? null : <button className="sync-button" onClick={onSync} disabled={syncing}><Icon name="refresh" size={15}/>{syncing ? 'Syncing…' : 'Sync latest'}</button>}</div></section>
    <section className="stats-grid"><Stat label="AI digest themes" value={xDigest.length} detail={evaluation ? `evaluated ${formatDate(evaluation.generatedAt)}` : 'awaiting evaluation'} tone="violet"/><Stat label="Bookmarks indexed" value={x.bookmarks?.length || 0} detail={sync?.runNumber ? `GitHub run #${sync.runNumber}` : 'local report'} tone="green"/><Stat label="New this run" value={x.resources_returned_this_run || 0} detail={`${x.pages_fetched_this_run || 0} API pages`} tone="blue"/><Stat label="Weekly API guard" value={`$${spend.toFixed(2)}`} detail={`of $${budget.toFixed(2)} software limit`} tone="amber"/></section>
    <section className="x-status"><div className="x-status-main"><span className="x-glyph">𝕏</span><div><span className="eyebrow">Bookmark ingestion</span><h2>{x.enabled ? 'Your bookmarks are flowing' : 'Collector is ready for credentials'}</h2><p>{x.enabled ? `${x.bookmarks?.length || 0} bookmarks are available as personal-priority evidence.` : 'The collector remains disabled until a user completes OAuth and explicitly configures a nonzero budget.'}</p></div></div><div className="budget"><div><span>Weekly API guard</span><strong>${spend.toFixed(2)} <small>/ ${budget.toFixed(2)}</small></strong></div><div className="progress"><i style={{ width: `${pct}%` }}/></div><small>{x.resources_read_this_week || 0} owned reads this week</small></div></section>
    <section className="x-digest-section"><div className="section-heading"><div><span className="eyebrow">AI synthesis</span><h2>Bookmark TL;DRs and insights</h2></div><span>{evaluation ? `Evaluated ${formatDate(evaluation.generatedAt)}` : 'Not evaluated yet'}</span></div>{xDigest.length ? <div className="x-digest-grid">{xDigest.map((digest, index) => <XDigestCard digest={digest} rank={index + 1} key={`${digest.title}-${index}`}/>)}</div> : <div className="empty-state small"><h2>AI synthesis pending</h2><p>Bookmarks remain visible below, but they are not called a digest until the bounded evaluator runs.</p></div>}</section>
    <div className="x-grid"><section><div className="section-heading"><div><span className="eyebrow">Saved posts</span><h2>Recent bookmarks</h2></div><span>20 of {x.bookmarks?.length || 0}</span></div>{x.bookmarks?.length ? <div className="bookmark-list">{x.bookmarks.slice(0, 20).map((bookmark, index) => <a href={bookmark.url} target="_blank" rel="noreferrer" className="bookmark" key={`${bookmark.url}-${index}`}><Badge tone="owner">Owner saved</Badge><h3>{bookmark.text || 'X post'}</h3><span>{bookmark.author_name || (bookmark.author_username ? `@${bookmark.author_username}` : 'X')} · {formatDate(bookmark.created_at)}</span></a>)}</div> : <div className="empty-state small"><h2>No bookmarks on this Mac yet</h2><p>Until OAuth is connected, the iPhone Share Sheet remains the free capture path.</p></div>}</section>
      <aside className="watch-panel"><span className="eyebrow">Watch network</span><h2>Accounts & projects</h2><p>Configured interests for discovery. Watched items are leads, not automatic verification.</p><h3>People</h3><div className="watch-cloud">{watch.people.map((name) => <Badge tone="owner" key={name}>{name}</Badge>)}</div><h3>Labs & tools</h3><div className="watch-cloud">{watch.projects.map((name) => <Badge key={name}>{name}</Badge>)}</div><h3>Repository watches</h3><div className="repo-list">{watch.repositories.map((repo) => <span key={repo}><Icon name="git" size={14}/>{repo}</span>)}</div></aside>
    </div></main>;
}

function App() {
  const [tab, setTab] = useState(() => window.location.hash.slice(1) || 'mission');
  const [snapshot, setSnapshot] = useState(null);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [archiveCandidate, setArchiveCandidate] = useState(null);
  async function load() { const response = await fetch(`${BASE}data/snapshot.json?time=${Date.now()}`, { cache: 'no-store' }); if (!response.ok) throw new Error(`Snapshot HTTP ${response.status}`); setSnapshot(await response.json()); }
  useEffect(() => { load().catch((err) => setError(err.message)); }, []);
  useEffect(() => { window.location.hash = tab; }, [tab]);
  async function refresh() { setRefreshing(true); setError(''); try { const response = await fetch(`${BASE}api/refresh`, { method: 'POST' }); if (response.ok) setSnapshot(await response.json()); else await load(); } catch { await load(); } finally { setRefreshing(false); } }
  async function syncAiradar() { setSyncing(true); try { const response = await fetch(`${BASE}api/airadar/sync`, { method: 'POST' }); if (response.ok) setSnapshot(await response.json()); else alert('Sign into GitHub CLI on this Mac to enable future AIRadar syncs.'); } finally { setSyncing(false); } }
  if (error) return <div className="load-screen"><h1>Observatory unavailable</h1><p>{error}</p></div>;
  if (!snapshot) return <div className="load-screen"><span className="radar-orb"><i/></span><p>Powering up Observatory…</p></div>;
  async function setArchived(project, archived) { setRefreshing(true); setError(''); try { const response = await fetch(`${BASE}api/projects/${project.id}/archive`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ archived }) }); if (!response.ok) throw new Error('Archive update failed'); setSnapshot(await response.json()); } catch (err) { setError(err.message); } finally { setRefreshing(false); } }
  function requestArchive(project, archived) { if (archived) setArchiveCandidate(project); else setArchived(project, false); }
  async function confirmArchive() { const project = archiveCandidate; setArchiveCandidate(null); await setArchived(project, true); }
  return <div className="app"><Header tab={tab} setTab={setTab} snapshot={snapshot} refreshing={refreshing} onRefresh={refresh}/>{tab === 'atlas' ? <AtlasView snapshot={snapshot}/> : tab === 'airadar' ? <AIRadarView snapshot={snapshot} onSync={syncAiradar} syncing={syncing}/> : tab === 'x' ? <XView snapshot={snapshot} onSync={syncAiradar} syncing={syncing}/> : <MissionView snapshot={snapshot} onArchive={requestArchive} onKeepArchived={(project) => setArchived(project, true)}/>}<footer><span>Observatory Mission Control · {snapshot.readOnly ? 'authenticated read-only share' : 'private on this Mac'}</span><span>Refreshed {formatDate(snapshot.generatedAt)}</span></footer>{archiveCandidate ? <ArchiveConfirmation project={archiveCandidate} onCancel={() => setArchiveCandidate(null)} onConfirm={confirmArchive}/> : null}</div>;
}

createRoot(document.getElementById('root')).render(<React.StrictMode><App/></React.StrictMode>);
