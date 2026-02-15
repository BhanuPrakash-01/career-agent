// src/app/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabaseClient";
import FileUpload from "@/components/FileUpload";
import ProfileEditor from "@/components/ProfileEditor"; // We'll reuse this if they want to edit
import { generateResume } from "@/lib/api";
import { Loader2, User, LogOut, FileText } from "lucide-react";
import Link from "next/link";

export default function Home() {
  const [user, setUser] = useState<any>(null);
  const [hasProfile, setHasProfile] = useState(false);
  const [loading, setLoading] = useState(true);
  
  // Generator States
  const [jobDescription, setJobDescription] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<any>(null);

  const router = useRouter();
  const supabase = createClient();

  // 1. CHECK AUTH & PROFILE ON LOAD
  useEffect(() => {
    const init = async () => {
      // A. Check User
      const { data: { user } } = await supabase.auth.getUser();
      
      if (!user) {
        // Not logged in? Go to login page immediately.
        router.push("/login");
        return;
      }
      setUser(user);

      // B. Check if they have a profile (resume uploaded)
      const { data: profile } = await supabase
        .from("master_profiles")
        .select("id")
        .eq("user_id", user.id)
        .single();

      if (profile) {
        setHasProfile(true);
      }
      setLoading(false);
    };

    init();
  }, [router]);

  // 2. HANDLE LOGOUT
  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push("/login");
  };

  // 3. GENERATE RESUME LOGIC
  const handleGenerate = async () => {
    if (!jobDescription || !user) return;
    setIsGenerating(true);
    try {
      // We pass the user.id so the backend knows WHO is asking
      const data = await generateResume(jobDescription, user.id);
      setResult(data);
    } catch (error) {
      alert("Error generating resume. See console.");
      console.error(error);
    } finally {
      setIsGenerating(false);
    }
  };

  // --- RENDERING STATES ---

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  // If we are here, we are logged in.
  return (
    <main className="min-h-screen bg-gray-50 text-gray-900 font-sans">
      
      {/* HEADER (Navbar) */}
      <header className="bg-white border-b sticky top-0 z-20 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2 font-bold text-xl">
          <span>CareerAgent</span>
          <span className="text-blue-600 text-xs bg-blue-100 px-2 py-1 rounded-full">BETA</span>
        </div>
        
        <div className="flex items-center gap-4">
          <Link href="/profile" className="text-sm font-medium hover:text-blue-600 flex items-center gap-1">
            <User className="w-4 h-4" /> View Profile
          </Link>
          <button onClick={handleLogout} className="text-sm text-red-600 hover:text-red-700 flex items-center gap-1">
            <LogOut className="w-4 h-4" /> Sign Out
          </button>
        </div>
      </header>

      <div className="max-w-6xl mx-auto py-12 px-4">

        {/* STATE 1: NO PROFILE (Show Upload) */}
        {!hasProfile ? (
          <div className="max-w-xl mx-auto text-center space-y-8 animate-in fade-in slide-in-from-bottom-4">
            <div className="space-y-2">
              <h1 className="text-3xl font-bold">Welcome, {user.email}</h1>
              <p className="text-gray-500">To get started, we need to index your experience.</p>
            </div>
            
            {/* Pass userId so the upload is linked to THIS account */}
            <FileUpload 
              userId={user.id} 
              onUploadComplete={() => {
                // When done, refresh to find the profile and show the generator
                window.location.reload(); 
              }} 
            />
          </div>
        ) : (
          
          /* STATE 2: HAS PROFILE (Show Generator) */
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-in fade-in zoom-in duration-300">
            
            {/* LEFT: JOB DESCRIPTION INPUT */}
            <div className="space-y-6">
              <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                <h2 className="text-lg font-bold mb-4">1. Paste Job Description</h2>
                <textarea
                  className="w-full h-64 p-4 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 resize-none text-sm"
                  placeholder="Paste the JD here (e.g., 'Looking for a Senior Python Developer...')"
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                />
                <button
                  onClick={handleGenerate}
                  disabled={isGenerating || !jobDescription}
                  className="mt-4 w-full bg-black text-white py-3 px-4 rounded-lg font-bold hover:bg-gray-800 disabled:opacity-50 transition-all flex justify-center items-center gap-2"
                >
                  {isGenerating ? <Loader2 className="animate-spin" /> : "Generate Tailored Resume"}
                </button>
              </div>

              {/* Debug/Feedback Panel */}
              {result && (
                <div className="bg-slate-900 text-slate-300 p-4 rounded-lg text-xs font-mono">
                  <p>STATUS: Generated in {result.revisions} revisions.</p>
                  <p className="mt-2 text-yellow-400">CRITIC: "{result.critic_feedback}"</p>
                </div>
              )}
            </div>

            {/* RIGHT: LATEX EDITOR VIEW */}
            <div className="bg-slate-900 rounded-xl shadow-lg border border-slate-700 min-h-[600px] flex flex-col overflow-hidden">
              <div className="bg-slate-800 px-4 py-2 border-b border-slate-700 flex justify-between items-center">
                <span className="text-xs text-slate-400 font-mono">resume.tex</span>
                {result && (
                  <button 
                    onClick={() => navigator.clipboard.writeText(result.final_resume)}
                    className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded"
                  >
                    Copy Code
                  </button>
                )}
              </div>
              
              <div className="flex-1 overflow-auto p-4">
                {result ? (
                  <pre className="font-mono text-sm text-green-400 whitespace-pre-wrap">
                    {result.final_resume}
                  </pre>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-4">
                     <FileText className="w-12 h-12 opacity-50"/>
                     <p>Generated LaTeX code will appear here.</p>
                  </div>
                )}
              </div>
            </div>

          </div>
        )}
      </div>
    </main>
  );
}