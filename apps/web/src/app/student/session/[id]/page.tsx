"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useParams, useRouter } from "next/navigation";
import AssessmentRunner from "@/components/AssessmentRunner";

export default function StudentSessionPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  
  const [student, setStudent] = useState<any>(null);

  useEffect(() => {
    const fetchMe = async () => {
      try {
        const res = await fetch("/api/me");
        if (res.ok) {
          setStudent(await res.json());
        }
      } catch (err) {
        console.error("Error fetching student info", err);
      }
    };
    
    fetchMe();
  }, []);

  return (
    <div className="min-h-screen bg-bg flex flex-col font-tajawal relative">
      <header className="p-4 flex justify-between items-center bg-white border-b border-border z-10 shadow-sm">
        <Image src="/brand/logo-gradient.svg" alt="Himma Logo" width={120} height={40} />
        <div className="flex items-center gap-3">
          <span className="font-bold text-navy">{student?.full_name?.split(' ')[0] || "طالب"}</span>
          <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center text-primary font-bold overflow-hidden border-2 border-primary">
            <Image src="/characters/boy/welcome.png" alt="Avatar" width={40} height={40} className="object-cover translate-y-1" />
          </div>
        </div>
      </header>

      <main className="flex-1 flex w-full max-w-5xl mx-auto h-[calc(100vh-73px)]">
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col p-4 md:p-8 overflow-y-auto">
          <AssessmentRunner sessionId={id} />
        </div>
        
        {/* Character Sidebar (Desktop only) */}
        <div className="hidden md:flex flex-col justify-end w-64 p-4 shrink-0">
          <div className="relative">
            <div className="absolute top-[-40px] right-[20px] bg-white p-3 rounded-2xl rounded-br-none shadow-md border border-border">
              <p className="font-bold text-primary">أنت بطل! استمر</p>
            </div>
            <Image 
              src="/characters/boy/welcome.png" 
              alt="Encouraging Character" 
              width={180} 
              height={240}
              className="object-contain" 
            />
          </div>
        </div>
      </main>
    </div>
  );
}
