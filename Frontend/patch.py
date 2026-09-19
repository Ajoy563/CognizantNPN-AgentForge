import re

with open('/Users/ajoydas/Desktop/Demo/Frontend/src/App.tsx', 'r') as f:
    content = f.read()

# Add imports
content = content.replace(
    "import { getSession, signIn, signOut, signUp } from './services/authClient';",
    "import { getSession, signIn, signOut, signUp, signInWithGoogle, signInWithMicrosoft } from './services/authClient';"
)

# Update auth function handler to be generic
auth_func = """
  const handleSocialAuth = async (provider: 'google' | 'microsoft') => {
    setLoading(true); setError('');
    const result = provider === 'google' ? await signInWithGoogle() : await signInWithMicrosoft();
    if (result.error) { setError(result.error); setLoading(false); return; }
    const session = await getSession();
    if (session?.user) {
      setProfile({ name: session.user.user_metadata?.full_name || 'Alex Morgan', email: session.user.email || 'alex@solutionforge.ai' });
      setScreen('app'); setView('new');
    }
    setLoading(false);
  };
"""

content = content.replace("  const auth = async", auth_func.strip() + "\n  const auth = async")

# Add onGoogle and onMicrosoft to Auth usage
content = content.replace(
    "<Auth mode={screen} error={error} loading={loading} onBack={() => setScreen('home')} onSwitch={() => openAuth(screen === 'signin' ? 'signup' : 'signin')} onSubmit={(event) => auth(event, screen)} />",
    "<Auth mode={screen} error={error} loading={loading} onBack={() => setScreen('home')} onSwitch={() => openAuth(screen === 'signin' ? 'signup' : 'signin')} onSubmit={(event) => auth(event, screen)} onGoogle={() => handleSocialAuth('google')} onMicrosoft={() => handleSocialAuth('microsoft')} />"
)

# Add onGoogle and onMicrosoft to Auth signature and UI
auth_comp_sig = "function Auth({ mode, onBack, onSwitch, onSubmit, error, loading }: { mode: 'signin' | 'signup'; onBack: () => void; onSwitch: () => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void; error: string; loading: boolean }) {"
auth_comp_sig_new = "function Auth({ mode, onBack, onSwitch, onSubmit, error, loading, onGoogle, onMicrosoft }: { mode: 'signin' | 'signup'; onBack: () => void; onSwitch: () => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void; error: string; loading: boolean; onGoogle: () => void; onMicrosoft: () => void }) {"
content = content.replace(auth_comp_sig, auth_comp_sig_new)

# Add onclicks to buttons
content = content.replace(
    '<button><b className="google">G</b> Continue with Google</button>',
    '<button type="button" onClick={onGoogle} disabled={loading}><b className="google">G</b> Continue with Google</button>'
)
content = content.replace(
    '<button><b className="ms"><i /><i /><i /><i /></b> Continue with Microsoft</button>',
    '<button type="button" onClick={onMicrosoft} disabled={loading}><b className="ms"><i /><i /><i /><i /></b> Continue with Microsoft</button>'
)

with open('/Users/ajoydas/Desktop/Demo/Frontend/src/App.tsx', 'w') as f:
    f.write(content)
