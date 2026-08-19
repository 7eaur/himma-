import Image from "next/image";
import Link from "next/link";

export default function WelcomePage() {
  return (
    <div className="min-h-screen bg-bg flex flex-col font-plex">
      <header className="w-full p-6 flex justify-between items-center border-b border-border bg-white">
        <div className="flex items-center gap-2">
          <Image src="/brand/logo-navy.svg" alt="Himma Logo" width={120} height={40} />
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-8 max-w-5xl mx-auto w-full">
        <div className="text-center mb-12">
          <Image 
            src="/brand/logo-gradient.svg" 
            alt="Himma Logo" 
            width={200} 
            height={80} 
            className="mx-auto mb-6"
          />
          <h1 className="text-3xl font-bold text-navy mb-2">أتعلم، أتطور، أصل إلى القمة</h1>
          <p className="text-muted text-lg">مرحباً بك في منصة همة التعليمية</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-3xl">
          {/* Researcher Card */}
          <Link href="/admin/login" className="card flex flex-col items-center hover:shadow-md transition-shadow cursor-pointer text-center">
            <h2 className="text-2xl font-semibold text-primary mb-6">دخول الباحثة</h2>
            <div className="flex-1 w-full flex justify-center mb-6 min-h-[200px]">
              <Image 
                src="/characters/boy-welcome.png" 
                alt="Researcher Welcome" 
                width={150} 
                height={200} 
                className="object-contain"
              />
            </div>
            <span className="btn-primary w-full text-lg">تسجيل الدخول كباحثة</span>
          </Link>

          {/* Student Card */}
          <Link href="/student/login" className="card flex flex-col items-center hover:shadow-md transition-shadow cursor-pointer text-center font-tajawal">
            <h2 className="text-2xl font-bold text-primary mb-6">دخول الطالب</h2>
            <div className="flex-1 w-full flex justify-center mb-6 min-h-[200px]">
              <Image 
                src="/characters/girl-welcome.png" 
                alt="Student Welcome" 
                width={150} 
                height={200} 
                className="object-contain"
              />
            </div>
            <span className="btn-primary w-full text-lg">تسجيل الدخول كطالب</span>
          </Link>
        </div>
      </main>
    </div>
  );
}
