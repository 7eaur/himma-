import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import StudentRetryTasks from "./StudentRetryTasks";

describe("V2 student rerecord microphone privacy", () => {
  const originalMediaDevices = Object.getOwnPropertyDescriptor(navigator, "mediaDevices");
  const originalRecorder = Object.getOwnPropertyDescriptor(globalThis, "MediaRecorder");

  afterEach(() => {
    jest.restoreAllMocks();
    if (originalMediaDevices) Object.defineProperty(navigator, "mediaDevices", originalMediaDevices);
    else Reflect.deleteProperty(navigator, "mediaDevices");
    if (originalRecorder) Object.defineProperty(globalThis, "MediaRecorder", originalRecorder);
    else Reflect.deleteProperty(globalThis, "MediaRecorder");
  });

  it("closes a late microphone grant after the child navigates away", async () => {
    const stop = jest.fn();
    const stream = { getTracks: () => [{ stop }] } as unknown as MediaStream;
    let grant: (stream: MediaStream) => void = () => { throw new Error("uninitialized"); };
    const permission = new Promise<MediaStream>((resolve) => { grant = resolve; });
    const getUserMedia = jest.fn().mockReturnValue(permission);
    Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: { getUserMedia } });
    const construct = jest.fn();
    Object.defineProperty(globalThis, "MediaRecorder", { configurable: true, value: construct });

    global.fetch = jest.fn().mockResolvedValue({
      ok: true, status: 200, json: async () => ({
        items: [{
          task_id: 77, kind: "lesson", session_id: 10, question_id: "L1-05-GP-04",
          status: "requested", request_kind: "rerecord", reason: "القراءة غير واضحة",
          prompt: "اقرأ الكلمة مرة أخرى", stimulus: { text: "بَابٌ" }, staged_audio: null,
        }],
        next_offset: null,
      }),
    });
    const { unmount } = render(<StudentRetryTasks dashboard />);
    const start = await screen.findByRole("button", { name: "تسجيل القراءة من جديد" });
    expect(screen.getByTestId("retry-original-stimulus")).toHaveTextContent("بَابٌ");
    fireEvent.click(start);
    await waitFor(() => expect(getUserMedia).toHaveBeenCalledTimes(1));
    expect(screen.getByRole("button", { name: "جارٍ تشغيل الميكروفون..." })).toBeDisabled();
    unmount();
    await act(async () => { grant(stream); await permission; });
    expect(stop).toHaveBeenCalledTimes(1);
    expect(construct).not.toHaveBeenCalled();
  });
  it("keeps the child's recording blocked when the pinned reading text is missing", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true, status: 200, json: async () => ({
        items: [{
          task_id: 78, kind: "lesson", session_id: 10, question_id: "L1-05-GP-04",
          status: "requested", request_kind: "rerecord", reason: "أعد القراءة بوضوح",
          prompt: "اقرأ الكلمة", staged_audio: null,
        }],
        next_offset: null,
      }),
    });
    render(<StudentRetryTasks dashboard />);
    expect(await screen.findByRole("alert")).toHaveTextContent("تعذر عرض النص الأصلي");
    expect(screen.queryByRole("button", { name: "تسجيل القراءة من جديد" })).not.toBeInTheDocument();
  });

});

it("focuses the rerecording interface on its own requested question", async () => {
  global.fetch = jest.fn().mockResolvedValue({
    ok:true,status:200,json:async()=>({items:[
      {task_id:77,kind:"lesson",session_id:10,question_id:"L1-05-GP-04",status:"requested",
        request_kind:"rerecord",reason:"أعد القراءة",prompt:"اقرأ النص",stimulus:{text:"بَابٌ"},staged_audio:null},
      {task_id:78,kind:"lesson",session_id:12,question_id:"L1-06-GP-04",status:"requested",
        request_kind:"rerecord",reason:"أعد القراءة",prompt:"اقرأ النص",stimulus:{text:"قَلَمٌ"},staged_audio:null},
    ],next_offset:null}),
  });
  render(<StudentRetryTasks taskId={77}/>);
  expect(await screen.findByTestId("retry-original-stimulus")).toHaveTextContent("بَابٌ");
  expect(screen.queryByText("قَلَمٌ")).not.toBeInTheDocument();
});

it("reuses an uploaded recording after the academic submit fails and prevents repeated upload", async () => {
  const originalMediaDevices = Object.getOwnPropertyDescriptor(navigator, "mediaDevices");
  const originalRecorder = Object.getOwnPropertyDescriptor(globalThis, "MediaRecorder");
  const originalCreateObjectURL = Object.getOwnPropertyDescriptor(URL, "createObjectURL");
  const originalRevokeObjectURL = Object.getOwnPropertyDescriptor(URL, "revokeObjectURL");
  const trackStop = jest.fn();
  const stream = {getTracks:()=>[{stop:trackStop}]} as unknown as MediaStream;
  Object.defineProperty(navigator, "mediaDevices", {configurable:true,value:{getUserMedia:jest.fn().mockResolvedValue(stream)}});
  class RecorderStub {
    static isTypeSupported = (_type:string) => true;
    state: RecordingState = "inactive";
    mimeType = "audio/webm";
    stream = stream;
    ondataavailable: ((event: {data:Blob})=>void) | null = null;
    onstop: (()=>void) | null = null;
    onerror: (()=>void) | null = null;
    start() {this.state="recording";}
    stop() {
      this.state="inactive";
      this.ondataavailable?.({data:new Blob(["synthetic-audio-bytes"],{type:"audio/webm"})});
      this.onstop?.();
    }
  }
  Object.defineProperty(globalThis,"MediaRecorder",{configurable:true,value:RecorderStub});
  Object.defineProperty(URL,"createObjectURL",{configurable:true,value:jest.fn(()=> "blob:synthetic-lesson-retry")});
  Object.defineProperty(URL,"revokeObjectURL",{configurable:true,value:jest.fn()});
  const uploaded = {audio_storage_key:"private-synthetic",audio_file_size:21,audio_mime_type:"audio/webm",audio_duration_seconds:1};
  let submits = 0;
  let success = false;
  const fetcher=jest.fn(async (url: string,options?:RequestInit) => {
    if (url.includes("/student/tasks?")) return {ok:true,json:async()=>({items:[{
      task_id:77,kind:"lesson",session_id:10,question_id:"L1-05-GP-04",
      status:success?"submitted":"requested",request_kind:"rerecord",
      reason:"اقرأ النص بصوت واضح",prompt:"اقرأ الكلمة",stimulus:{text:"بَابٌ"},staged_audio:null,
    }],next_offset:null})};
    if (url.endsWith("/recording")) return {ok:true,json:async()=>uploaded};
    if (url.endsWith("/submit")) {
      submits++;
      if(submits===1) return {ok:false,status:503,json:async()=>({detail:"تعذر إكمال الإرسال الآن"})};
      success=true;
      return {ok:true,json:async()=>({status:"submitted",awaiting_human_review:true})};
    }
    throw new Error("Unexpected endpoint "+url);
  });
  global.fetch=fetcher as unknown as typeof fetch;
  try {
    render(<StudentRetryTasks taskId={77}/>);
    fireEvent.click(await screen.findByRole("button",{name:"تسجيل القراءة من جديد"}));
    fireEvent.click(await screen.findByRole("button",{name:"إيقاف التسجيل"}));
    fireEvent.click(screen.getByRole("button",{name:"إرسال الإجابة الجديدة للمراجعة"}));
    expect(await screen.findByRole("alert")).toHaveTextContent("تعذر إكمال الإرسال الآن");
    await waitFor(()=>expect(screen.getByRole("button",{name:"إرسال الإجابة الجديدة للمراجعة"})).toBeEnabled());
    fireEvent.click(screen.getByRole("button",{name:"إرسال الإجابة الجديدة للمراجعة"}));
    expect(await screen.findByText(/وصلت إجابتك الجديدة/)).toBeInTheDocument();
    expect(fetcher.mock.calls.filter(([url])=>url.endsWith("/recording"))).toHaveLength(1);
    expect(fetcher.mock.calls.filter(([url])=>url.endsWith("/submit"))).toHaveLength(2);
    const answers=fetcher.mock.calls.filter(([url])=>url.endsWith("/submit")).map(([,options])=>JSON.parse(options!.body as string));
    expect(answers[0].submit_key).toBe(answers[1].submit_key);
    expect(answers[1].audio_storage_key).toBe(uploaded.audio_storage_key);
    expect(trackStop).toHaveBeenCalled();
  } finally {
    for(const [obj,key,descriptor] of [
      [navigator,"mediaDevices",originalMediaDevices],
      [globalThis,"MediaRecorder",originalRecorder],
      [URL,"createObjectURL",originalCreateObjectURL],
      [URL,"revokeObjectURL",originalRevokeObjectURL],
    ] as const){
      if(descriptor) Object.defineProperty(obj,key,descriptor);
      else Reflect.deleteProperty(obj,key);
    }
  }
});
