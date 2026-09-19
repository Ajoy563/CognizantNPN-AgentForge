import { initializeApp } from 'firebase/app';
import { 
  getAuth, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signOut as firebaseSignOut,
  updateProfile,
  GoogleAuthProvider,
  signInWithPopup,
  browserSessionPersistence,
  setPersistence
} from 'firebase/auth';
import { getDownloadURL, getStorage, ref, uploadBytes } from 'firebase/storage';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
// Do not silently restore a previous user after the browser is restarted.
// Firebase remains authenticated for the active browser session only.
void setPersistence(auth, browserSessionPersistence);

type AuthResult = { error: string | null };

export async function getSession(): Promise<{ user?: { email?: string; user_metadata?: { full_name?: string, avatar_url?: string } } } | null> {
  await auth.authStateReady();
  const user = auth.currentUser;
  if (!user) return null;
  
  let dbProfile = null;
  try {
    const { getUserProfileAPI } = await import('./apiClient');
    dbProfile = await getUserProfileAPI();
  } catch(e) {}

  return { 
    user: { 
      email: user.email || undefined, 
      user_metadata: { 
        full_name: dbProfile?.name || user.displayName || undefined, 
        avatar_url: dbProfile?.photo_url || user.photoURL || undefined
      } 
    } 
  };
}

export async function signIn(email: string, password: string): Promise<AuthResult> {
  try {
    await signInWithEmailAndPassword(auth, email, password);
    return { error: null };
  } catch (err: any) {
    return { error: err.message || 'Failed to sign in' };
  }
}

export async function signUp(email: string, password: string, name: string): Promise<AuthResult> {
  try {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    if (name) {
      await updateProfile(userCredential.user, { displayName: name });
    }
    return { error: null };
  } catch (err: any) {
    return { error: err.message || 'Failed to sign up' };
  }
}

export async function signInWithGoogle(): Promise<AuthResult> {
  try {
    const provider = new GoogleAuthProvider();
    await signInWithPopup(auth, provider);
    return { error: null };
  } catch (err: any) {
    return { error: err.message || 'Failed to sign in with Google' };
  }
}

export async function signOut(): Promise<void> { 
  await firebaseSignOut(auth); 
}

export async function uploadProfileImage(file: File): Promise<string> {
  const user = auth.currentUser;
  if (!user) throw new Error('Please sign in again.');
  const storage = getStorage(app);
  const imageRef = ref(storage, `profile-images/${user.uid}/${Date.now()}-${file.name}`);
  await uploadBytes(imageRef, file, { contentType: file.type });
  return getDownloadURL(imageRef);
}
