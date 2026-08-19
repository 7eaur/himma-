"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Mic, MicOff, RotateCcw, Play } from "lucide-react";

interface AssessmentRunnerProps {
  sessionId: string;
}

interface Question {
  id: string;
  type: string;
  text: string;
  image_url?: string;
  options?: string[];
}

export default function AssessmentRunner({ sessionId }: AssessmentRunnerProps) {
  const router = useRouter();
  const [question, setQuestion] = useState<Question | null>(null);
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState(0); // 0 to 100
  const [questionNumber, setQuestionNumber] = useState(1);
  const [totalQuestions, setTotalQuestions] = useState(30);
  const [finished, setFinished] = useState(false);
  
  // Audio recording state
  const [isRecording, setIsRecording] = useState(false);

  useEffect(() => {
    // Fake fetch for now, waiting for real API
    // Replace with real logic when ready
    const timer = setTimeout(() => {
      setQuestion({
        id: "q1",
        type: "mcq",
        text: "ما هو الحرف الناقص في الكلمة؟ _ـيـّارة",
        options: ["س", "ش", "ص", "ض"]
      });
      setProgress(10);
      setLoading(false);
    }, 1000);
    
    return () => clearTimeout(timer);
  }, [sessionId]);

  const handleOptionClick = (option: string) => {
    // Fake submit logic
    if (questionNumber >= 3) {
      setFinished(true);
    } else {
      setLoading(true);
      setTimeout(() => {
        setQuestionNumber(prev => prev + 1);
        setProgress(prev => Math.min(prev + 15, 100));
        setQuestion({
          id: `q${questionNumber + 1}`,
          type: "read_aloud",
          text: "اقرأ الجملة التالية بصوت واضح:",
          image_url: "/placeholder-text.png"
        });
        setLoading(false);
      }, 500);
    }
  };

  const toggleRecording = () => {
    setIsRecording(!isRecording);
    if (isRecording) {
      // Fake submit audio
      setTimeout(() => {
        handleOptionClick("audio_submitted");
      }, 1000);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="spinner w-12 h-12 border-4"></div>
      </div>
    );
  }

  if (finished) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-center">
        <div className="relative w-48 h-64 mb-8">
          <Image src="/characters/girl/welcome.png" alt="Success" fill className="object-contain" />
        </div>
        <h2 className="text-4xl font-bold text-navy mb-4">أحسنت يا بطل!</h2>
        <p className="text-xl text-muted mb-8 max-w-md">
          لقد أتممت الاختبار بنجاح. نحن فخورون بك!
        </p>
        <button 
          onClick={() => router.push("/student")}
          className="btn-primary text-xl px-12 py-4 rounded-full shadow-lg min-h-[60px]"
        >
          العودة للرئيسية
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col max-w-3xl w-full mx-auto">
      {/* Progress Bar */}
      <div className="mb-8 w-full">
        <div className="flex justify-between items-center mb-2 font-bold text-navy">
          <span>السؤال {questionNumber} من {totalQuestions}</span>
          <span className="text-primary">{Math.round(progress)}%</span>
        </div>
        <div className="progress-bar h-4 rounded-full">
          <div className="progress-bar-fill h-4 rounded-full bg-gradient-to-l from-primary to-green" style={{ width: `${progress}%` }}></div>
        </div>
      </div>

      <div className="card flex-1 flex flex-col p-6 md:p-10 shadow-lg border-2 border-border/50 rounded-3xl">
        {/* Question Text */}
        <h2 className="text-3xl md:text-4xl font-bold text-navy mb-8 text-center leading-relaxed">
          {question?.text}
        </h2>
        
        {/* Question Content based on type */}
        <div className="flex-1 flex flex-col items-center justify-center w-full">
          {question?.type === "mcq" ? (
            <div className="grid grid-cols-2 gap-4 w-full">
              {question.options?.map((opt, i) => (
                <button 
                  key={i}
                  onClick={() => handleOptionClick(opt)}
                  className="bg-white border-4 border-border hover:border-primary hover:bg-bg text-navy font-bold text-3xl py-8 rounded-2xl transition-all hover:scale-[1.02] active:scale-95 shadow-sm min-h-[100px]"
                >
                  {opt}
                </button>
              ))}
            </div>
          ) : question?.type === "read_aloud" ? (
            <div className="w-full flex flex-col items-center">
              <div className="bg-bg p-8 rounded-2xl w-full text-center border-2 border-border mb-8 min-h-[150px] flex items-center justify-center">
                <span className="text-4xl font-bold text-navy leading-loose">
                  ذَهَبَ أَحْمَدُ إِلَى الْمَدْرَسَةِ مُبَكِّراً
                </span>
              </div>
              
              <div className="flex justify-center gap-6 w-full">
                <button 
                  onClick={toggleRecording}
                  className={`w-24 h-24 rounded-full flex items-center justify-center shadow-lg transition-all ${
                    isRecording 
                      ? "bg-red-500 text-white animate-pulse shadow-red-500/50" 
                      : "bg-primary text-white hover:bg-[#276bb8] hover:scale-105"
                  }`}
                >
                  {isRecording ? <MicOff size={40} /> : <Mic size={40} />}
                </button>
              </div>
              <p className={`mt-6 font-bold text-lg ${isRecording ? "text-red-500" : "text-primary"}`}>
                {isRecording ? "جاري التسجيل... اضغط للإيقاف" : "اضغط الميكروفون للبدء"}
              </p>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
