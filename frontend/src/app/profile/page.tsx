"use client";
import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";
import FileUpload from "@/components/FileUpload";

export default function ProfilePage() {
  const [user, setUser] = useState<any>(null);
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const supabase = createClient();

  useEffect(() => {
    const checkUser = async () => {
      // 1. Get Auth User
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        router.push("/login");
        return;
      }
      setUser(user);

      // 2. Fetch Profile Data from DB
      const { data: profileData } = await supabase
        .from("master_profiles")
        .select("*, experience_items(*), project_items(*)") // Join tables
        .eq("user_id", user.id)
        .single();

      setProfile(profileData);
      setLoading(false);
    };

    checkUser();
  }, []);

  if (loading) return <div className="p-8">Loading Profile...</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* HEADER */}
        <div className="flex justify-between items-center">
          <h1 className="text-3xl text-gray-800 text-sans font-bold">Your Career Profile</h1>
          <button 
            onClick={() => router.push("/")} // This will be the Generator page
            className="bg-black text-white px-6 py-2 rounded-lg"
          >
            Go to Resume Generator &rarr;
          </button>
        </div>

        {/* IF NO PROFILE, SHOW UPLOAD */}
        {!profile ? (
          <div className="bg-white p-8 rounded-xl shadow">
            <h2 className="text-xl text-gray-500 text-sans font-bold mb-4">You have no profile data yet.</h2>
            <FileUpload userId={user.id} onUploadComplete={() => window.location.reload()} />
          </div>
        ) : (
          <div className="space-y-6">
            
            {/* PERSONAL DETAILS */}
            <div className="bg-white p-6 rounded-xl shadow border">
              <h2 className="text-xl font-bold mb-4">Personal Details</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-500">Name</label>
                  <p className="font-medium">{profile.full_name}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Email</label>
                  <p className="font-medium">{profile.email || user.email}</p>
                </div>
                <div className="col-span-2">
                  <label className="text-sm text-gray-500">Summary</label>
                  <p className="text-gray-700">{profile.summary}</p>
                </div>
              </div>
            </div>

            {/* EXPERIENCE LIST */}
            <div className="bg-white p-6 rounded-xl shadow border">
              <h2 className="text-xl font-bold mb-4 text-blue-600">Experience</h2>
              {profile.experience_items?.map((job: any) => (
                <div key={job.id} className="mb-4 pb-4 border-b last:border-0">
                  <h3 className="font-bold">{job.title} at {job.company}</h3>
                  <p className="text-sm text-gray-500">{job.start_date} - {job.end_date}</p>
                  <p className="text-gray-700 mt-2 text-sm">{job.description}</p>
                </div>
              ))}
            </div>

            {/* PROJECTS LIST */}
            <div className="bg-white p-6 rounded-xl shadow border">
              <h2 className="text-xl font-bold mb-4 text-green-600">Projects</h2>
              {profile.project_items?.map((proj: any) => (
                <div key={proj.id} className="mb-4 pb-4 border-b last:border-0">
                  <h3 className="font-bold">{proj.name}</h3>
                  <p className="text-xs text-gray-500">Tech: {proj.tech_stack}</p>
                  <p className="text-gray-700 mt-2 text-sm">{proj.description}</p>
                </div>
              ))}
            </div>

          </div>
        )}
      </div>
    </div>
  );
}