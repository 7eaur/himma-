import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import VideoPlayer from "./VideoPlayer";

function setMediaTime(video: HTMLVideoElement, currentTime: number, duration = 6) {
  Object.defineProperty(video, "currentTime", { configurable: true, writable: true, value: currentTime });
  Object.defineProperty(video, "duration", { configurable: true, value: duration });
}

describe("VideoPlayer", () => {
  beforeEach(() => {
    Object.defineProperty(HTMLMediaElement.prototype, "play", { configurable: true, value: jest.fn().mockResolvedValue(undefined) });
    Object.defineProperty(HTMLMediaElement.prototype, "load", { configurable: true, value: jest.fn() });
  });

  it("restores a saved position and exposes native controls and Arabic captions", () => {
    render(<VideoPlayer src="/fixture.mp4" captionsSrc="/fixture.vtt" startAt={2.5} testOnly onCheckpoint={jest.fn()} onEnded={jest.fn()} />);
    const video = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    setMediaTime(video, 0);
    fireEvent.loadedMetadata(video);
    fireEvent.canPlay(video);
    expect(video.currentTime).toBe(2.5);
    expect(video).toHaveAttribute("controls");
    expect(video.querySelector("track")).toHaveAttribute("srclang", "ar");
    expect(screen.getByText(/TEST ONLY/)).toBeInTheDocument();
  });

  it("restores a saved position when cached metadata was ready before the listener", () => {
    const props = { src: "/fixture.mp4", startAt: 0, onCheckpoint: jest.fn(), onEnded: jest.fn() };
    const { rerender } = render(<VideoPlayer {...props} />);
    const video = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    setMediaTime(video, 0);
    Object.defineProperty(video, "readyState", { configurable: true, value: HTMLMediaElement.HAVE_METADATA });
    rerender(<VideoPlayer {...props} startAt={2.5} />);
    expect(video.currentTime).toBe(2.5);
  });

  it("saves checkpoints and reports completion without deciding mastery", () => {
    const onCheckpoint = jest.fn();
    const onEnded = jest.fn();
    render(<VideoPlayer src="/fixture.mp4" onCheckpoint={onCheckpoint} onEnded={onEnded} />);
    const video = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    setMediaTime(video, 5.5);
    fireEvent.timeUpdate(video);
    expect(onCheckpoint).toHaveBeenCalledWith(5.5, 6);
    setMediaTime(video, 6);
    fireEvent.ended(video);
    expect(onEnded).toHaveBeenCalledWith(6, 6);
    return waitFor(() => expect(screen.getByText("أكملت الشرح")).toBeInTheDocument());
  });

  it("waits for server confirmation and retries a failed completion without replaying", async () => {
    let rejectFirst: (reason: Error) => void = () => undefined;
    const first = new Promise<void>((_, reject) => { rejectFirst = reject; });
    const onEnded = jest.fn().mockImplementationOnce(() => first).mockResolvedValueOnce(undefined);
    render(<VideoPlayer src="/fixture.mp4" onCheckpoint={jest.fn()} onEnded={onEnded} />);
    const video = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    setMediaTime(video, 6, 6);
    fireEvent.ended(video);
    fireEvent.ended(video);
    expect(onEnded).toHaveBeenCalledTimes(1);
    expect(screen.getByText("جاري حفظ اكتمال الشرح")).toBeInTheDocument();
    expect(screen.queryByText("أكملت الشرح")).not.toBeInTheDocument();
    await act(async () => { rejectFirst(new Error("temporary network failure")); });
    expect(screen.getByRole("alert")).toHaveTextContent("تعذر تأكيد حفظ المشاهدة");
    fireEvent.canPlay(video);
    fireEvent.waiting(video);
    expect(screen.getByRole("alert")).toHaveTextContent("تعذر تأكيد حفظ المشاهدة");
    fireEvent.click(screen.getByRole("button", { name: "إعادة حفظ المشاهدة" }));
    await waitFor(() => expect(screen.getByText("أكملت الشرح")).toBeInTheDocument());
    expect(onEnded).toHaveBeenCalledTimes(2);
    expect(onEnded).toHaveBeenNthCalledWith(2, 6, 6);
  });

  it("shows recoverable buffering and media error states", async () => {
    render(<VideoPlayer src="/fixture.mp4" onCheckpoint={jest.fn()} onEnded={jest.fn()} />);
    const video = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    fireEvent.waiting(video);
    expect(screen.getByText("الاتصال بطيء قليلًا")).toBeInTheDocument();
    fireEvent.error(video);
    expect(screen.getByRole("alert")).toHaveTextContent("تعذر تشغيل الفيديو");
    expect(video).not.toHaveAttribute("controls");
    fireEvent.canPlay(video);
    fireEvent.waiting(video);
    fireEvent.stalled(video);
    fireEvent.playing(video);
    fireEvent.loadedMetadata(video);
    // A spurious native event cannot dismiss the explicit recovery affordance.
    expect(screen.getByRole("alert")).toHaveTextContent("تعذر تشغيل الفيديو");
    fireEvent.click(screen.getByRole("button", { name: "إعادة المحاولة" }));
    await waitFor(() => expect(HTMLMediaElement.prototype.load).toHaveBeenCalledTimes(1));
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(video).not.toHaveAttribute("controls");
    fireEvent.canPlay(video);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(video).toHaveAttribute("controls");
  });

  it("keeps autoplay denial visible until the learner explicitly retries", async () => {
    const play = jest.fn().mockRejectedValueOnce(new Error("autoplay denied")).mockResolvedValueOnce(undefined);
    Object.defineProperty(HTMLMediaElement.prototype, "play", { configurable: true, value: play });
    render(<VideoPlayer src="/fixture.mp4" onCheckpoint={jest.fn()} onEnded={jest.fn().mockResolvedValue(undefined)} />);
    const video = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    setMediaTime(video, 6);
    fireEvent.ended(video);
    await waitFor(() => expect(screen.getByText("أكملت الشرح")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "شاهد مرة أخرى" }));
    await waitFor(() => expect(screen.getByText("اضغط لبدء الفيديو")).toBeInTheDocument());
    fireEvent.canPlay(video);
    fireEvent.waiting(video);
    fireEvent.playing(video);
    fireEvent.loadedMetadata(video);
    expect(screen.getByText("اضغط لبدء الفيديو")).toBeInTheDocument();
    expect(video).not.toHaveAttribute("controls");
    fireEvent.click(screen.getByRole("button", { name: "تشغيل" }));
    await waitFor(() => expect(video).toHaveAttribute("controls"));
    expect(play).toHaveBeenCalledTimes(2);
  });

  it("ignores an older play rejection after a newer attempt succeeds", async () => {
    let rejectOlder: (reason: Error) => void = () => undefined;
    const older = new Promise<void>((_, reject) => { rejectOlder = reject; });
    const play = jest.fn()
      .mockRejectedValueOnce(new Error("autoplay denied"))
      .mockImplementationOnce(() => older)
      .mockResolvedValueOnce(undefined);
    Object.defineProperty(HTMLMediaElement.prototype, "play", { configurable: true, value: play });
    render(<VideoPlayer src="/fixture.mp4" onCheckpoint={jest.fn()} onEnded={jest.fn().mockResolvedValue(undefined)} />);
    const video = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    setMediaTime(video, 6);
    fireEvent.ended(video);
    await waitFor(() => expect(screen.getByText("أكملت الشرح")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "شاهد مرة أخرى" }));
    await waitFor(() => expect(screen.getByText("اضغط لبدء الفيديو")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "تشغيل" }));
    fireEvent.click(screen.getByRole("button", { name: "تشغيل" }));
    await waitFor(() => expect(video).toHaveAttribute("controls"));
    await act(async () => { rejectOlder(new Error("stale rejection")); });
    expect(video).toHaveAttribute("controls");
    expect(screen.queryByText("اضغط لبدء الفيديو")).not.toBeInTheDocument();
    expect(play).toHaveBeenCalledTimes(3);
  });

  it("ignores a stale play rejection after media retry begins", async () => {
    let rejectOldPlay: (reason: Error) => void = () => undefined;
    const pending = new Promise<void>((_, reject) => { rejectOldPlay = reject; });
    Object.defineProperty(HTMLMediaElement.prototype, "play", { configurable: true, value: jest.fn().mockReturnValue(pending) });
    render(<VideoPlayer src="/fixture.mp4" onCheckpoint={jest.fn()} onEnded={jest.fn().mockResolvedValue(undefined)} />);
    const video = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    setMediaTime(video, 6);
    fireEvent.ended(video);
    await waitFor(() => expect(screen.getByText("أكملت الشرح")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "شاهد مرة أخرى" }));
    fireEvent.error(video);
    fireEvent.click(screen.getByRole("button", { name: "إعادة المحاولة" }));
    expect(screen.getByText("جاري تجهيز الفيديو")).toBeInTheDocument();
    await act(async () => { rejectOldPlay(new Error("old playback failed")); });
    expect(screen.getByText("جاري تجهيز الفيديو")).toBeInTheDocument();
    expect(screen.queryByText("اضغط لبدء الفيديو")).not.toBeInTheDocument();
    expect(video).not.toHaveAttribute("controls");
  });

  it("does not dismiss a media error when an earlier play promise resolves late", async () => {
    let resolvePlay: () => void = () => undefined;
    const pendingPlay = new Promise<void>((resolve) => { resolvePlay = resolve; });
    const play = jest.fn().mockImplementationOnce(() => pendingPlay);
    Object.defineProperty(HTMLMediaElement.prototype, "play", { configurable: true, value: play });
    render(<VideoPlayer src="/fixture.mp4" onCheckpoint={jest.fn()} onEnded={jest.fn().mockResolvedValue(undefined)} />);
    const video = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    setMediaTime(video, 6);
    fireEvent.ended(video);
    await waitFor(() => expect(screen.getByText("أكملت الشرح")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "شاهد مرة أخرى" }));
    expect(play).toHaveBeenCalledTimes(1);
    fireEvent.error(video);
    expect(screen.getByRole("alert")).toHaveTextContent("تعذر تشغيل الفيديو");
    await act(async () => { resolvePlay(); });
    expect(screen.getByRole("alert")).toHaveTextContent("تعذر تشغيل الفيديو");
    expect(video).not.toHaveAttribute("controls");
  });

  it("ignores a late completion acknowledgment from the previous video", async () => {
    let resolvePrevious: () => void = () => undefined;
    const pending = new Promise<void>((resolve) => { resolvePrevious = resolve; });
    const onEnded = jest.fn().mockImplementationOnce(() => pending).mockResolvedValueOnce(undefined);
    const { rerender } = render(<VideoPlayer src="/first.mp4" onCheckpoint={jest.fn()} onEnded={onEnded} />);
    const video = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    setMediaTime(video, 6);
    fireEvent.ended(video);
    expect(screen.getByText("جاري حفظ اكتمال الشرح")).toBeInTheDocument();

    rerender(<VideoPlayer src="/second.mp4" onCheckpoint={jest.fn()} onEnded={onEnded} />);
    expect(screen.queryByText("جاري حفظ اكتمال الشرح")).not.toBeInTheDocument();
    await act(async () => { resolvePrevious(); });
    expect(screen.queryByText("أكملت الشرح")).not.toBeInTheDocument();

    const nextVideo = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    expect(nextVideo).not.toBe(video);
    setMediaTime(nextVideo, 6);
    fireEvent.ended(nextVideo);
    await waitFor(() => expect(screen.getByText("أكملت الشرح")).toBeInTheDocument());
    expect(onEnded).toHaveBeenCalledTimes(2);
  });

  it("ignores a delayed play rejection after the video source changes", async () => {
    let rejectPrevious: (error: Error) => void = () => undefined;
    const pending = new Promise<void>((_, reject) => { rejectPrevious = reject; });
    const play = jest.fn().mockImplementationOnce(() => pending);
    Object.defineProperty(HTMLMediaElement.prototype, "play", { configurable: true, value: play });
    const onEnded = jest.fn().mockResolvedValue(undefined);
    const { rerender } = render(<VideoPlayer src="/first.mp4" onCheckpoint={jest.fn()} onEnded={onEnded} />);
    const video = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    setMediaTime(video, 6);
    fireEvent.ended(video);
    await waitFor(() => expect(screen.getByText("أكملت الشرح")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "شاهد مرة أخرى" }));
    expect(play).toHaveBeenCalledTimes(1);

    rerender(<VideoPlayer src="/second.mp4" onCheckpoint={jest.fn()} onEnded={onEnded} />);
    await act(async () => { rejectPrevious(new Error("old video autoplay denied")); });
    expect(screen.queryByText("اضغط لبدء الفيديو")).not.toBeInTheDocument();
    expect(screen.getByText("جاري تجهيز الفيديو")).toBeInTheDocument();
  });

  it("starts checkpoint tracking fresh when a new video replaces the old one", () => {
    const onCheckpoint = jest.fn();
    const props = { onCheckpoint, onEnded: jest.fn() };
    const { rerender } = render(<VideoPlayer src="/first.mp4" {...props} />);
    const video = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    setMediaTime(video, 5.5, 10);
    fireEvent.timeUpdate(video);
    expect(onCheckpoint).toHaveBeenCalledWith(5.5, 10);

    rerender(<VideoPlayer src="/second.mp4" {...props} />);
    const nextVideo = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    expect(nextVideo).not.toBe(video);
    setMediaTime(nextVideo, 5.1, 10);
    fireEvent.timeUpdate(nextVideo);
    expect(onCheckpoint).toHaveBeenCalledWith(5.1, 10);
    expect(onCheckpoint).toHaveBeenCalledTimes(2);
  });

  it("does not silently retry a failed save on a duplicate native ended event", async () => {
    const onEnded = jest.fn().mockRejectedValueOnce(new Error("lost acknowledgment")).mockResolvedValueOnce(undefined);
    render(<VideoPlayer src="/fixture.mp4" onCheckpoint={jest.fn()} onEnded={onEnded} />);
    const video = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    setMediaTime(video, 6);
    fireEvent.ended(video);
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("تعذر تأكيد حفظ المشاهدة"));
    fireEvent.ended(video);
    expect(onEnded).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("button", { name: "إعادة حفظ المشاهدة" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "إعادة حفظ المشاهدة" }));
    await waitFor(() => expect(screen.getByText("أكملت الشرح")).toBeInTheDocument());
    expect(onEnded).toHaveBeenCalledTimes(2);
  });

  it("does not submit completion again after replaying an already confirmed lesson", async () => {
    const onEnded = jest.fn().mockResolvedValue(undefined);
    render(<VideoPlayer src="/fixture.mp4" onCheckpoint={jest.fn()} onEnded={onEnded} />);
    const video = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    setMediaTime(video, 6);
    fireEvent.ended(video);
    await waitFor(() => expect(screen.getByText("أكملت الشرح")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "شاهد مرة أخرى" }));
    fireEvent.ended(video); // Stale native event from the first playback.
    expect(screen.queryByText("أكملت الشرح")).not.toBeInTheDocument();
    expect(onEnded).toHaveBeenCalledTimes(1);
    setMediaTime(video, 6);
    fireEvent.ended(video); // The replay really finished.
    expect(screen.getByText("أكملت الشرح")).toBeInTheDocument();
    expect(onEnded).toHaveBeenCalledTimes(1);
  });

  it("does not submit a premature ended event as a completed video", () => {
    const onEnded = jest.fn().mockResolvedValue(undefined);
    render(<VideoPlayer src="/fixture.mp4" onCheckpoint={jest.fn()} onEnded={onEnded} />);
    const video = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    setMediaTime(video, 2, 6);
    fireEvent.canPlay(video);
    fireEvent.ended(video);
    expect(onEnded).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent("تعذر تشغيل الفيديو");
    expect(screen.queryByText("أكملت الشرح")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "إعادة المحاولة" }));
    expect(HTMLMediaElement.prototype.load).toHaveBeenCalledTimes(1);
  });
});
