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
