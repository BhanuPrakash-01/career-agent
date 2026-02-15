"use client";
import { useState } from "react";

export default function ProfileEditor({ initialData, onSave }: { initialData: any, onSave: () => void }) {
  const [data, setData] = useState(initialData);

  // A simple function to delete a hallucinated link
  const removeLink = (index: number) => {
    const newProjects = [...data.projects];
    newProjects[index].link = ""; // Clear the link
    setData({ ...data, projects: newProjects });
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200 space-y-8">
      
      <div className="border-b pb-4">
        <h2 className="text-2xl font-bold">Review Your Master Profile</h2>
        <p className="text-gray-500">The AI extracted this. Verify it before we generate resumes.</p>
      </div>

      {/* WORK EXPERIENCE SECTION */}
      <div>
        <h3 className="text-lg font-bold text-blue-600 mb-2">Work Experience</h3>
        {data.work_experience.map((job: any, i: number) => (
          <div key={i} className="mb-4 p-4 bg-gray-50 rounded-lg border">
            <p className="font-bold">{job.role} <span className="text-gray-500">at {job.company}</span></p>
            <textarea 
              className="w-full mt-2 p-2 text-sm border rounded"
              value={job.description}
              readOnly // Make editable if you want full CRUD later
            />
          </div>
        ))}
      </div>

      {/* PROJECTS SECTION */}
      <div>
        <h3 className="text-lg font-bold text-green-600 mb-2">Projects</h3>
        {data.projects.map((proj: any, i: number) => (
          <div key={i} className="mb-4 p-4 bg-gray-50 rounded-lg border">
            <div className="flex justify-between items-center">
              <p className="font-bold">{proj.name}</p>
              {proj.link && (
                <div className="flex items-center gap-2">
                  <a href={proj.link} target="_blank" className="text-blue-500 text-sm underline">
                    {proj.link}
                  </a>
                  <button 
                    onClick={() => removeLink(i)}
                    className="text-xs bg-red-100 text-red-600 px-2 py-1 rounded hover:bg-red-200"
                  >
                    Remove Link
                  </button>
                </div>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-1">Tech: {proj.tech_stack}</p>
            <p className="text-sm mt-2">{proj.description}</p>
          </div>
        ))}
      </div>

      <button 
        onClick={onSave}
        className="w-full bg-black text-white py-3 rounded-lg font-bold hover:bg-gray-800"
      >
        Confirm & Save Profile
      </button>
    </div>
  );
}