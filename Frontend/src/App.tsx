import { FormEvent, useEffect, useState } from 'react';
import { ArrowLeft, ArrowRight, BarChart3, BookOpen, Bot, CheckCircle2, ChevronRight, Circle, Clock, Cloud, Code2, Database, Download, Eye, FileText, Gauge, Globe2, Hexagon, History as HistoryIcon, Inbox, Layers3, Lightbulb, LoaderCircle, LockKeyhole, LogOut, Menu, Network, PanelLeft, PenLine, Rocket, Search, Settings, ShieldCheck, Sparkles, Target, Users, X, Zap } from 'lucide-react';
import { getSession, signIn, signOut, signUp, signInWithGoogle, uploadProfileImage } from './services/authClient';
import { COUNTRIES } from './countries';

type Screen = 'home' | 'signin' | 'signup' | 'app';
type View = 'new' | 'processing' | 'dashboard' | 'history' | 'settings';
type Tab = 'Overview' | 'Architecture' | 'Technology' | 'Delivery Plan' | 'Risks' | 'Full Report';
type Blueprint = { idea: string; technology: string; cloud: string; traffic: string; timeline: string; country: string; summary?: string; scope?: string[]; stack?: string[][]; risks?: string[][]; architecture?: any; delivery?: any; blueprint_html?: string; generation_id?: string; project_id?: string; };
type Profile = { name: string; email: string; photo?: string };

const defaultBlueprint: Blueprint = { idea: '', technology: 'Enterprise', cloud: 'AWS', traffic: '', timeline: '4', country: '' };
const agents = [['Business Analyst', 'Clarifies goals & requirements', Target], ['Solution Architect', 'Designs the right blueprint', Network], ['Technology Advisor', 'Recommends the best-fit stack', Code2], ['Delivery Planner', 'Maps the path to launch', Rocket]] as const;
const capabilities = [['Business Analysis', 'Understand the problem before writing a line of code.', Users], ['Solution Architecture', 'Turn ambition into a clear, scalable system design.', Layers3], ['Technology Recommendations', 'Choose tools that fit your context, scale, and budget.', ShieldCheck], ['Delivery Planning', 'Move from idea to execution with confidence.', BarChart3]] as const;
const summary = '';
const scope: string[] = [];
const stack: string[][] = [];
const risks: string[][] = [];

async function loadProjectBlueprint(projectId: string): Promise<Blueprint | null> {
  const { getProjectDetailAPI, getGenerationDetailAPI } = await import('./services/apiClient');
  const detail = await getProjectDetailAPI(projectId);
  const gens = detail.generations || [];
  if (gens.length === 0) return null;
  const bp = await getGenerationDetailAPI(gens[0].generation_id);
  const inputs = bp.project_inputs || {};
  return {
    idea: inputs.business_idea || detail.name,
    technology: inputs.tech_preference || '',
    cloud: inputs.cloud_preference || '',
    traffic: String(inputs.expected_daily_traffic || ''),
    timeline: String(inputs.delivery_timeline_months || ''),
    country: inputs.country || '',
    summary: bp.requirements?.problem,
    scope: (bp.requirements?.requirements || [])
      .filter((r: any) => (bp.requirements?.mvp_requirement_ids || []).includes(r.id))
      .map((r: any) => r.text),
    stack: (bp.technology?.decisions || []).map((item: any) => [item.category, item.technology]),
    risks: (bp.delivery?.risks || []).map((item: any) => [item.risk, item.impact, item.mitigation]),
    architecture: bp.architecture,
    delivery: bp.delivery,
    blueprint_html: bp.blueprint_html,
    generation_id: bp.generation_id,
    project_id: bp.project_id,
  };
}

function Logo({ light = false }: { light?: boolean }) { return <div className={`logo ${light ? 'logo-light' : ''}`}><span className="logo-mark"><Hexagon size={30} /><span /></span><span>SolutionForge <b>AI</b></span></div>; }
function Button({ children, onClick, type = 'button', kind = 'primary', className = '' }: { children: React.ReactNode; onClick?: () => void; type?: 'button' | 'submit'; kind?: 'primary' | 'ghost' | 'outline'; className?: string }) { return <button type={type} onClick={onClick} className={`button ${kind} ${className}`}>{children}</button>; }

export default function App() {
  const [screen, setScreen] = useState<Screen>('home'); const [view, setView] = useState<View>('new'); const [tab, setTab] = useState<Tab>('Overview'); const [blueprint, setBlueprint] = useState(defaultBlueprint); const [profile, setProfile] = useState<Profile>({ name: '', email: '' }); const [error, setError] = useState(''); const [loading, setLoading] = useState(false); const [mobileNav, setMobileNav] = useState(false);
  useEffect(() => { getSession().then((session) => { if (session?.user) { setProfile({ name: session.user.user_metadata?.full_name || '', email: session.user.email || '', photo: (session.user.user_metadata as any)?.avatar_url }); setScreen('app'); } }); }, []);
  const openAuth = (mode: 'signin' | 'signup') => { setError(''); setScreen(mode); };
const handleSocialAuth = async () => {
    setLoading(true); setError('');
    const result = await signInWithGoogle();
    if (result.error) { setError(result.error); setLoading(false); return; }
    const session = await getSession();
    if (session?.user) {
      setProfile({ name: session.user.user_metadata?.full_name || 'Alex Morgan', email: session.user.email || 'alex@solutionforge.ai', photo: (session.user.user_metadata as any)?.avatar_url });
      setScreen('app'); setView('new');
    }
    setLoading(false);
  };
  const auth = async (event: FormEvent<HTMLFormElement>, mode: 'signin' | 'signup') => { event.preventDefault(); setLoading(true); setError(''); const data = new FormData(event.currentTarget); const email = String(data.get('email') || ''); const password = String(data.get('password') || ''); const name = String(data.get('name') || ''); const result = mode === 'signin' ? await signIn(email, password) : await signUp(email, password, name); setLoading(false); if (result.error) { setError(result.error); return; } const session = await getSession(); setProfile({ name: session?.user?.user_metadata?.full_name || name, email: session?.user?.email || email, photo: session?.user?.user_metadata?.avatar_url }); setScreen('app'); setView('new'); };
  const generate = async (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); const data = new FormData(event.currentTarget); const next = { idea: String(data.get('idea') || ''), technology: String(data.get('technology') || ''), cloud: String(data.get('cloud') || ''), traffic: String(data.get('traffic') || ''), timeline: String(data.get('timeline') || ''), country: String(data.get('country') || '') }; if (Object.values(next).some((value) => !value.trim())) return; setBlueprint(next); setView('processing'); try { const { generateBlueprintAPI } = await import('./services/apiClient'); const result = await generateBlueprintAPI({
      business_idea: next.idea,
      tech_preference: next.technology.toLowerCase() === 'enterprise' ? 'enterprise' : 'opensource',
      cloud_preference: next.cloud === 'No Preference' ? 'none' : next.cloud.toLowerCase() as 'aws' | 'azure' | 'gcp',
      expected_daily_traffic: Number(next.traffic.replace(/,/g, '')),
      delivery_timeline_months: parseInt(next.timeline) || 4,
      country: next.country
    });
    const bp = result.blueprint || result;
    const mapped = {
      ...next,
      summary: bp?.requirements?.problem,
      scope: (bp?.requirements?.requirements || [])
        .filter((r: any) => (bp?.requirements?.mvp_requirement_ids || []).includes(r.id))
        .map((r: any) => r.text),
      stack: (bp?.technology?.decisions || []).map((item: any) => [item.category, item.technology]),
      risks: (bp?.delivery?.risks || []).map((item: any) => [item.risk, item.impact, item.mitigation]),
      architecture: bp?.architecture,
      delivery: bp?.delivery,
      blueprint_html: bp?.blueprint_html,
      generation_id: result.generation_id || bp?.generation_id,
      project_id: result.project_id || bp?.project_id
    };
    setBlueprint(mapped);
    setView('dashboard');
 } catch(e) { const message = e instanceof Error ? e.message : 'Blueprint generation failed.'; setError(message); window.alert(message); setView('new'); } };
  if (screen === 'home') return <Home onAuth={() => openAuth('signin')} />;
  if (screen === 'signin' || screen === 'signup') return <Auth mode={screen} error={error} loading={loading} onBack={() => setScreen('home')} onSwitch={() => openAuth(screen === 'signin' ? 'signup' : 'signin')} onSubmit={(event) => auth(event, screen)} onGoogle={() => handleSocialAuth()} />;
  // Generation takes over the whole window: no sidebar, no app bar, and no
  // way to navigate away mid-run. generate() is what leaves this state.
  if (view === 'processing') return <Processing />;
  return <Shell view={view} tab={tab} setTab={setTab} profile={profile} setProfile={setProfile} blueprint={blueprint} setBlueprint={setBlueprint} mobileNav={mobileNav} setMobileNav={setMobileNav} navigate={(next) => { setView(next); setMobileNav(false); }} onSignOut={async () => { await signOut(); setScreen('home'); }} onGenerate={generate} />;
}

function Home({ onAuth }: { onAuth: () => void }) { return <div className="site home"><header className="topbar"><Logo /><nav><a href="#home">Home</a><a href="#how">How It Works</a><a href="#about">About</a></nav><Button onClick={onAuth}>Sign In <ArrowRight size={17} /></Button></header><main id="home" className="hero"><div className="hero-copy"><div className="eyebrow"><Sparkles size={16} /> AI-Powered Solution Consulting</div><h1>Turn Your Business Idea into a <span>Real-World Solution</span></h1><p>Get a complete technology blueprint — from business analysis to architecture, technology and delivery plan — in minutes using the power of multi-agent AI.</p><Button onClick={onAuth} className="hero-button">Generate My Solution <ArrowRight size={19} /></Button></div><div className="agent-flow"><div className="flow-label"><span>MEET YOUR AI TEAM</span><span>4 AGENTS · 1 BLUEPRINT</span></div>{agents.map(([name, detail, Icon], index) => <div className="agent-row" key={name}><div className="agent-icon"><Icon size={21} /></div><div><strong>{name}</strong><small>{detail}</small></div><em>0{index + 1}</em>{index < 3 && <i />}</div>)}</div></main><section id="how" className="capabilities">{capabilities.map(([title, detail, Icon]) => <div className="capability" key={title}><div className="cap-icon"><Icon size={22} /></div><div><h3>{title}</h3><p>{detail}</p></div></div>)}</section><section id="about" className="home-footer"><div><small>FROM FIRST THOUGHT TO FIRST RELEASE</small><h2>Ideas are everywhere.<br /><span>Execution is rare.</span></h2></div><p>SolutionForge AI gives teams the clarity to build what matters next.</p></section></div>; }

function Auth({ mode, onBack, onSwitch, onSubmit, error, loading, onGoogle }: { mode: 'signin' | 'signup'; onBack: () => void; onSwitch: () => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void; error: string; loading: boolean; onGoogle: () => void }) { const signInMode = mode === 'signin'; const [show, setShow] = useState(false); return <div className="auth"><button className="back-link" onClick={onBack}><ArrowLeft size={16} /> Back to Home</button><div className="auth-card"><Logo light /><div className="auth-title"><h1>{signInMode ? 'Welcome Back' : 'Create Your Account'}</h1><p>{signInMode ? 'Sign in to continue to SolutionForge AI' : 'Start building your solution with SolutionForge AI'}</p></div><form onSubmit={onSubmit} className="auth-form">{!signInMode && <label>Full Name<input name="name" placeholder="John Doe" required /></label>}<label>Email address<input name="email" type="email" placeholder="you@company.com" required /></label><label>Password<div className="password"><input name="password" type={show ? 'text' : 'password'} placeholder={signInMode ? 'Enter your password' : 'Create a password'} minLength={6} required /><button type="button" onClick={() => setShow(!show)}><Eye size={17} /></button></div></label>{!signInMode && <label>Confirm Password<input name="confirmPassword" type="password" placeholder="Confirm your password" required /></label>}{signInMode ? <div className="form-meta"><label className="check"><input type="checkbox" /> Remember me</label><a href="#forgot">Forgot password?</a></div> : <label className="check terms"><input type="checkbox" required /> I agree to the <a href="#terms">Terms of Service</a> and <a href="#privacy">Privacy Policy</a></label>}{error && <div className="form-error">{error}</div>}<Button type="submit" className="full">{loading ? <LoaderCircle className="spin" size={18} /> : signInMode ? 'Sign In' : 'Create Account'} {!loading && <ArrowRight size={17} />}</Button></form><div className="divider"><span>or continue with</span></div><div className="social"><button type="button" onClick={onGoogle} disabled={loading}><b className="google">G</b> Continue with Google</button></div><p className="switch">{signInMode ? "Don't have an account?" : 'Already have an account?'} <button onClick={onSwitch}>{signInMode ? 'Create an Account' : 'Sign In'}</button></p></div></div>; }

function Shell({ view, tab, setTab, profile, setProfile, blueprint, setBlueprint, mobileNav, setMobileNav, navigate, onSignOut, onGenerate }: { view: View; tab: Tab; setTab: (tab: Tab) => void; profile: Profile; setProfile: (p: Profile) => void; blueprint: Blueprint; setBlueprint: (b: Blueprint) => void; mobileNav: boolean; setMobileNav: (open: boolean) => void; navigate: (view: View) => void; onSignOut: () => void; onGenerate: (event: FormEvent<HTMLFormElement>) => void }) { const nav = [['new', 'New Blueprint', PenLine], ['dashboard', 'Dashboard', PanelLeft], ['history', 'History', HistoryIcon], ['settings', 'Settings', Settings]] as const; return <div className="app"><aside className={`sidebar ${mobileNav ? 'open' : ''}`}><div className="side-head"><Logo /><button onClick={() => setMobileNav(false)}><X size={18} /></button></div><small className="side-label">WORKSPACE</small><div className="side-nav">{nav.map(([key, label, Icon]) => <button className={view === key ? 'active' : ''} onClick={() => navigate(key as View)} key={key as string}><Icon size={18} />{label as string}</button>)}</div><div className="side-bottom"><div className="mini-user" onClick={() => navigate('settings' as View)} style={{cursor: 'pointer'}}><span className="avatar">{profile.name[0]}</span><div><b>{profile.name}</b><small>{profile.email}</small></div></div><button className="signout" onClick={onSignOut}><LogOut size={16} /> Sign Out</button></div></aside>{mobileNav && <button className="overlay" onClick={() => setMobileNav(false)} aria-label="Close menu" />}<div className="app-main"><header className="app-bar"><button className="menu" onClick={() => setMobileNav(true)}><Menu size={20} /></button><span>Workspace <ChevronRight size={14} /> <b>{view === 'new' ? 'New Blueprint' : view[0].toUpperCase() + view.slice(1)}</b></span><div className="online"><i /> AI agents online <span className="avatar" onClick={() => navigate('settings' as View)} style={{cursor: 'pointer'}}>{profile.name[0]}</span></div></header><main className="app-content">{view === 'new' && <BlueprintForm blueprint={blueprint} onGenerate={onGenerate} />}{view === 'dashboard' && <Dashboard tab={tab} setTab={setTab} blueprint={blueprint} navigate={navigate} />}{view === 'history' && <History setBlueprint={setBlueprint} setTab={setTab} navigate={navigate} />}{view === 'settings' && <SettingsView profile={profile} setProfile={setProfile} onSignOut={onSignOut} />}</main></div></div>; }

function BlueprintForm({ blueprint, onGenerate }: { blueprint: Blueprint; onGenerate: (event: FormEvent<HTMLFormElement>) => void }) { return <div className="narrow"><div className="intro"><small>NEW BLUEPRINT</small><h1>Let's Build Your Solution</h1><p>Provide a few details about your business idea and constraints. Our AI agents will do the rest.</p></div><form className="blueprint-card" onSubmit={onGenerate}><div className="card-top"><div><h2>Tell us about your idea</h2><p>The more context you share, the more precise your blueprint.</p></div><span className="private"><LockKeyhole size={14} /> Private workspace</span></div><label className="wide">Business idea / problem statement<textarea name="idea" defaultValue={blueprint.idea} placeholder="Enter the problem statement/ description" required /></label><div className="fields"><label>Technology preference<select name="technology" defaultValue={blueprint.technology}><option>Open Source</option><option>Enterprise</option></select></label><label>Cloud preference<select name="cloud" defaultValue={blueprint.cloud}><option>No Preference</option><option>AWS</option><option>Azure</option><option>GCP</option></select></label><label>Expected daily traffic<input name="traffic" defaultValue={blueprint.traffic} placeholder="e.g. 20,000" required /></label><label>Delivery timeline<select name="timeline" defaultValue={blueprint.timeline}><option value="2">2 months</option><option value="4">4 months</option><option value="6">6 months</option><option value="9">9+ months</option></select></label><label className="country">Country / data residency<select name="country" defaultValue={blueprint.country} required><option value="" disabled>Select a location...</option>{COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}</select></label></div><div className="card-bottom"><span><ShieldCheck size={16} /> Your inputs are used only to shape this blueprint.</span><Button type="submit">Generate Blueprint <ArrowRight size={18} /></Button></div></form><div className="agent-note"><Bot size={18} /><div><b>Built by a team of AI specialists</b><p>Five agents will review your brief, challenge assumptions, and assemble a practical plan.</p></div></div></div>; }

const PROCESSING_STAGES = [
  { label: 'Business Analysis', status: 'Clarifying goals, users and requirements...' },
  { label: 'Solution Architecture', status: 'Designing the system architecture...' },
  { label: 'Technology Selection', status: 'Choosing the technology stack...' },
  { label: 'Delivery Planning', status: 'Planning delivery, effort and risks...' },
  { label: 'Finalizing Blueprint', status: 'Assembling your final blueprint...' },
] as const;
// Each stage is shown for this long before the next one starts. The LAST
// stage is never left behind -- it stays active for as long as the request
// takes, however long that is.
const STAGE_SECONDS = 12;

// The backend emits no per-agent progress events: POST /api/generate
// resolves exactly once, at the end. These stages are descriptive UI only.
// They advance forwards once, never loop back, never randomise, and never
// show a completion checkmark. Once "Finalizing Blueprint" is reached it
// stays active until the real request resolves -- App.generate() is the
// only thing that leaves this screen.
function Processing() {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    const start = Date.now();
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - start) / 1000)), 500);
    return () => clearInterval(id);
  }, []);

  const activeIndex = Math.min(
    Math.floor(elapsed / STAGE_SECONDS),
    PROCESSING_STAGES.length - 1
  );
  const active = PROCESSING_STAGES[activeIndex];
  const clock = `${Math.floor(elapsed / 60)}:${String(elapsed % 60).padStart(2, '0')}`;

  return <div className="processing-screen"><div className="processing">
    <div className="intro centered"><small><i className="live" /> LIVE RUN</small><h1>Building Your Solution</h1><p>Our AI consulting team is working through your brief. This usually takes about 1&ndash;2 minutes &mdash; your blueprint opens automatically when it's ready.</p></div>
    <div className="processing-ring-wrap">
      <div className="processing-ring spinning"><div className="processing-ring-inner"><Sparkles size={26} className="pulse" /></div></div>
      <p className="processing-status">{active.status}</p>
      <div className="processing-bar"><span /></div>
      <p className="processing-elapsed"><Clock size={14} /> {clock} elapsed</p>
    </div>
    <div className="processing-card">{PROCESSING_STAGES.map((stage, index) => { const current = index === activeIndex; const past = index < activeIndex; return <div className={`process ${current ? 'current' : past ? 'past' : ''}`} key={stage.label}><span>{current ? <LoaderCircle className="spin" size={16} /> : <Circle size={9} />}</span><div><b>{stage.label}</b></div>{current && <em>WORKING</em>}</div>; })}</div>
    <p className="processing-foot"><Sparkles size={16} /> Four specialist agents are assembling your blueprint.</p>
  </div></div>;
}

function Dashboard({ tab, setTab, blueprint, navigate }: { tab: Tab; setTab: (tab: Tab) => void; blueprint: Blueprint; navigate: (view: View) => void; }) {
  if (!blueprint.idea) return <div className="dashboard"><div className="history-state empty"><Inbox size={28} /><h3>No blueprint open</h3><p>Generate a new blueprint or reopen one of your previous projects from History.</p><div className="history-empty-actions"><Button onClick={() => navigate('new')}>New Blueprint <ArrowRight size={16} /></Button><Button kind="outline" onClick={() => navigate('history')}><HistoryIcon size={16} /> View History</Button></div></div></div>;

  return <div className="dashboard"><div className="dash-head"><div><small>SOLUTION BLUEPRINT · GENERATED JUST NOW</small><h1>Your Solution Blueprint is Ready!</h1><p>Built from your brief for {blueprint.country} · {blueprint.timeline} month delivery target · {blueprint.traffic} daily users</p></div><div className="downloads"><button onClick={async () => { if (blueprint.generation_id) { const { downloadReport } = await import('./services/apiClient'); await downloadReport(blueprint.generation_id, 'report'); } }}><FileText size={16} /> Download HTML</button>
  <Button onClick={async () => { if (blueprint.generation_id) { const { downloadReport } = await import('./services/apiClient'); await downloadReport(blueprint.generation_id, 'pdf'); } }}><Download size={16} /> Download PDF</Button></div></div><div className="tabs">{(['Overview', 'Architecture', 'Technology', 'Delivery Plan', 'Risks', 'Full Report'] as Tab[]).map((item) => <button className={tab === item ? 'active' : ''} onClick={() => setTab(item)} key={item}>{item}</button>)}</div>{tab === 'Overview' && <Overview blueprint={blueprint} />}{tab === 'Architecture' && <Architecture blueprint={blueprint} />}{tab === 'Technology' && <Technology blueprint={blueprint} />}{tab === 'Delivery Plan' && <DeliveryPlan blueprint={blueprint} />}{tab === 'Risks' && <Risks blueprint={blueprint} />}{tab === 'Full Report' && <FullReport blueprint={blueprint} />}</div>; }

type HistoryEntry = { project_id: string; name: string; created_at: string; generation_count: number; last_generated_at?: string };

function History({ setBlueprint, setTab, navigate }: { setBlueprint: (b: Blueprint) => void; setTab: (tab: Tab) => void; navigate: (view: View) => void }) {
  const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading');
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [errorMsg, setErrorMsg] = useState('');
  const [query, setQuery] = useState('');
  const [openingId, setOpeningId] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setState('loading'); setErrorMsg('');
      try {
        const { getProjectsAPI, getProjectDetailAPI } = await import('./services/apiClient');
        const projects: any[] = await getProjectsAPI();
        const details = await Promise.all(projects.map((p) => getProjectDetailAPI(p.project_id).catch(() => null)));
        if (cancelled) return;
        const merged: HistoryEntry[] = projects.map((p, index) => {
          const gens = details[index]?.generations || [];
          return {
            project_id: p.project_id,
            name: p.name,
            created_at: p.created_at,
            generation_count: gens.length,
            last_generated_at: gens[0]?.created_at,
          };
        });
        setEntries(merged);
        setState('ready');
      } catch (e) {
        if (cancelled) return;
        setErrorMsg(e instanceof Error ? e.message : 'Failed to load your project history.');
        setState('error');
      }
    })();
    return () => { cancelled = true; };
  }, [retryKey]);

  const openProject = async (entry: HistoryEntry) => {
    setOpeningId(entry.project_id);
    try {
      const opened = await loadProjectBlueprint(entry.project_id);
      if (opened) { setBlueprint(opened); setTab('Overview'); navigate('dashboard'); }
      else { window.alert('This project does not have a generated blueprint yet.'); }
    } catch (e) {
      window.alert(e instanceof Error ? e.message : 'Failed to open this project.');
    } finally {
      setOpeningId(null);
    }
  };

  const filtered = entries.filter((entry) => entry.name.toLowerCase().includes(query.trim().toLowerCase()));

  return <div className="narrow history">
    <div className="intro"><small>HISTORY</small><h1>Your Projects</h1><p>Every blueprint you've generated, pulled from your account.</p></div>

    {state === 'ready' && entries.length > 0 && <div className="history-search"><Search size={16} /><input type="text" placeholder="Search by project name or idea..." value={query} onChange={(event) => setQuery(event.target.value)} /></div>}

    {state === 'loading' && <div className="history-state"><LoaderCircle className="spin" size={20} /> Loading your projects…</div>}

    {state === 'error' && <div className="history-state error"><p>{errorMsg}</p><Button kind="outline" onClick={() => setRetryKey((k) => k + 1)}>Retry</Button></div>}

    {state === 'ready' && entries.length === 0 && <div className="history-state empty"><Inbox size={28} /><h3>No projects yet</h3><p>Generate your first blueprint and it will show up here.</p><Button onClick={() => navigate('new')}>New Blueprint <ArrowRight size={16} /></Button></div>}

    {state === 'ready' && entries.length > 0 && filtered.length === 0 && <div className="history-state empty"><p>No projects match "{query}".</p></div>}

    {state === 'ready' && filtered.length > 0 && <div className="history-list">{filtered.map((entry) => <div className="result-card history-item" key={entry.project_id}>
      <div className="history-item-head"><h2>{entry.name}</h2>{entry.generation_count === 0 && <span className="badge none">NO GENERATION</span>}</div>
      <div className="history-item-meta">
        <span><Clock size={13} /> Created {new Date(entry.created_at).toLocaleDateString()}</span>
        {entry.last_generated_at && <span><Sparkles size={13} /> Last generated {new Date(entry.last_generated_at).toLocaleDateString()}</span>}
        <span><Layers3 size={13} /> {entry.generation_count} generation{entry.generation_count === 1 ? '' : 's'}</span>
      </div>
      <div className="history-item-actions"><Button kind="outline" onClick={() => openProject(entry)}>{openingId === entry.project_id ? <LoaderCircle className="spin" size={16} /> : <Eye size={16} />} {entry.generation_count > 0 ? 'View Blueprint' : 'Open Project'}</Button></div>
    </div>)}</div>}
  </div>;
}

function Overview({ blueprint }: { blueprint: Blueprint }) { return <><div className="summary-grid"><div className="result-card summary"><small><Lightbulb size={16} /> EXECUTIVE SUMMARY</small><h2>Build a focused customer operations hub that scales with your team.</h2><p>{blueprint.summary || summary}</p></div><div className="result-card signal"><small><Gauge size={16} /> BLUEPRINT SIGNAL</small><b>Strong foundation</b><p>Clear scope and a practical path to MVP.</p><div><span /></div></div></div><div className="metrics">{[[Rocket, 'MVP timeline', `${blueprint.timeline} months`], [BarChart3, 'Expected scale', `${blueprint.traffic} / day`], [Cloud, 'Cloud platform', blueprint.cloud], [Code2, 'Technology approach', blueprint.technology]].map(([Icon, label, value]) => <div key={String(label)}><Icon size={19} /><span>{label as string}<b>{value as string}</b></span></div>)}</div><div className="detail-grid"><Info title="MVP scope" items={blueprint.scope || scope} /><div className="result-card brief"><h2>Your brief <small>INPUT</small></h2><p>{blueprint.idea}</p><div><span>{blueprint.cloud}</span><span>{blueprint.country}</span><span>{blueprint.technology}</span></div></div></div></>; }
function Info({ title, items }: { title: string; items: string[] }) { return <div className="result-card"><h2>{title} <small>{items.length} ITEMS</small></h2><ul>{items.map((item, index) => <li key={index}><CheckCircle2 size={17} />{item}</li>)}</ul></div>; }
function Architecture({ blueprint }: { blueprint?: Blueprint }) { const architecture = blueprint?.architecture; const components = (architecture?.components || []).map((item: any) => `${item.id} [${item.layer}] ${item.name}: ${item.responsibility}`); const security = (architecture?.security_controls || []).map((item: any) => `${item.id}: ${item.control}`); return <div className="tab-content"><div className="result-card"><h2>Architecture overview <small>{architecture?.architecture_style || 'GENERATED DESIGN'}</small></h2><p className="lead">{architecture?.rationale || (architecture?.mvp_architecture || []).join(' ') || 'No architecture data is available for this generation.'}</p><div className="arch-map">{components.map((label: string) => <div key={label}><span><Network size={18} />{label}</span></div>)}</div></div><div className="detail-grid"><Info title="Major components" items={components} /><Info title="Security & scalability" items={[...security, ...(architecture?.scalability_strategy || [])]} /></div></div>; }
function Technology({ blueprint }: { blueprint?: Blueprint }) { const rows = blueprint?.stack || stack; return <div className="result-card"><h2>Recommended technology stack <small>{rows.length} ITEMS</small></h2><p className="lead">A balanced stack optimized for velocity, maintainability, and operational clarity.</p><div className="stack">{rows.map(([category, value], index) => <div key={`${category}-${value}-${index}`}><b><Code2 size={17} />{category}</b><span>{value}</span><ChevronRight size={16} /></div>)}</div></div>; }
function DeliveryPlan({ blueprint }: { blueprint?: Blueprint }) { const delivery = blueprint?.delivery; const timeline = delivery?.timeline || []; const workstreams = (delivery?.workstreams || []).map((item: any) => `${item.id} ${item.name} (${item.effort})`); return <div className="tab-content"><div className="result-card"><h2>Delivery timeline <small>{blueprint?.timeline || ''} MONTHS</small></h2><div className="timeline">{timeline.map((item: any, i: number) => <div key={i}><b>0{i + 1}</b><span><strong>{item.phase} · {item.duration}</strong><p>{item.milestone ? `Milestone: ${item.milestone} — ` : ''}{item.deliverables?.join(', ')}</p></span></div>)}</div></div><div className="detail-grid"><Info title="Implementation workstreams" items={workstreams} /><Info title="Team & dependencies" items={[...(delivery?.team_roles?.map((item: any) => `${item.role} x${item.count}`) || []), ...(delivery?.dependencies || [])]} /></div></div>; }
function Risks({ blueprint }: { blueprint?: Blueprint }) { const rows = blueprint?.risks || risks; return <div className="result-card"><h2>Risks & mitigations <small>{rows.length} WATCH ITEMS</small></h2><p className="lead">Keep these visible as the solution moves from blueprint to build.</p><div className="risks">{rows.map(([risk, impact, mitigation], index) => <div key={index}><div><b>{risk}</b><span className={impact.toLowerCase()}>{impact} impact</span></div><p>{mitigation}</p></div>)}</div></div>; }
function FullReport({ blueprint }: { blueprint?: Blueprint }) { const html = blueprint?.blueprint_html; if (!html) { return <div className="result-card"><h2>Full report</h2><p className="lead">No full report is available for this generation yet.</p></div>; } return <div className="tab-content"><div className="result-card" style={{ padding: 0, overflow: 'hidden' }}><iframe title="Full blueprint report" srcDoc={html} style={{ width: '100%', height: '80vh', border: 'none', background: '#fff' }} /></div></div>; }
function SettingsView({ profile, setProfile, onSignOut }: { profile: Profile; setProfile: (p: Profile) => void; onSignOut: () => void }) { const [isEditing, setIsEditing] = useState(false); return <div className="narrow settings"><div className="intro"><small>WORKSPACE SETTINGS</small><h1>Settings</h1><p>Manage your profile and report preferences.</p></div><div className="settings-card">{!isEditing ? <div className="profile"><span className="avatar large" style={profile.photo ? {backgroundImage: `url(${profile.photo})`, backgroundSize: "cover", color: "transparent"} : {}}>{profile.name[0]}</span><div><h2>{profile.name}</h2><p>{profile.email}</p></div><button onClick={() => setIsEditing(true)}><PenLine size={16} /> Edit</button></div> : <form className="profile-edit" onSubmit={async (e) => { e.preventDefault(); const fd = new FormData(e.currentTarget); const name = String(fd.get('name') || ''); const pass = String(fd.get('password') || ''); let base64Photo = ''; try { const { getAuth, updateProfile, updatePassword } = await import('firebase/auth'); const auth = getAuth(); if(auth.currentUser) { const photoFile = fd.get('photo') as File;
if(photoFile && photoFile.size > 0) { base64Photo = await uploadProfileImage(photoFile); }
if(auth.currentUser) {
  if(name) await updateProfile(auth.currentUser, {displayName: name});
  const { updateUserProfileAPI } = await import('./services/apiClient');
  await updateUserProfileAPI(name, base64Photo);
}
 if(pass) await updatePassword(auth.currentUser, pass); } setIsEditing(false); setProfile({ ...profile, name: name || profile.name, photo: base64Photo || profile.photo }); } catch(err: any) { console.error(err); alert(err.message || err); } }} style={{display: 'flex', flexDirection: 'column', gap: '1rem', width: '100%', marginBottom: '2rem'}}><div style={{display: 'flex', flexDirection: 'column', gap: '0.5rem'}}><b>Profile Picture</b><div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}><span className="avatar large" style={profile.photo ? {backgroundImage: `url(${profile.photo})`, backgroundSize: "cover", color: "transparent"} : {}}>{profile.name[0]}</span><input type="file" name="photo" accept="image/*" /></div></div><label style={{display: 'flex', flexDirection: 'column', gap: '0.5rem'}}><b>Full Name</b><input type="text" name="name" defaultValue={profile.name} required /></label><label style={{display: 'flex', flexDirection: 'column', gap: '0.5rem'}}><b>New Password</b><input type="password" name="password" placeholder="Leave blank to keep current" /></label><div style={{display: 'flex', gap: '0.5rem'}}><Button type="submit">Save Changes</Button><Button type="button" kind="ghost" onClick={() => setIsEditing(false)}>Cancel</Button></div></form>}<hr /><h3>Report preferences</h3>{[['PDF report', 'Include a polished report when your blueprint is ready.', FileText], ['Markdown report', 'Keep an editable version of your blueprint.', BookOpen]].map(([title, detail, Icon]) => <label className="preference" key={String(title)}><span><Icon size={18} /><span><b>Generate {title as string}</b><small>{detail as string}</small></span></span><input type="checkbox" defaultChecked /></label>)}<div className="danger"><div><b>Sign out of this workspace</b><p>You can sign back in at any time.</p></div><button onClick={onSignOut}><LogOut size={16} /> Sign Out</button></div></div></div>; }
function downloadMarkdown(blueprint: Blueprint) { const content = `# SolutionForge AI Blueprint\n\n## Executive Summary\n${summary}\n\n## Original Brief\n${blueprint.idea}\n\n## MVP Scope\n${scope.map((item) => `- ${item}`).join('\n')}\n\n## Technology Stack\n${(blueprint?.stack || stack).map(([key, value]) => `- **${key}:** ${value}`).join('\n')}\n\n## Risks\n${(blueprint?.risks || risks).map(([risk, impact, mitigation]) => `- ${risk} (${impact}): ${mitigation}`).join('\n')}`; const url = URL.createObjectURL(new Blob([content], { type: 'text/markdown' })); const link = document.createElement('a'); link.href = url; link.download = 'solutionforge-blueprint.md'; link.click(); URL.revokeObjectURL(url); }
