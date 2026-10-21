import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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
    expect(screen.getByText("أكملت الشرح")).toBeInTheDocument();
  });

  it("shows recoverable buffering and media error states", async () => {
    render(<VideoPlayer src="/fixture.mp4" onCheckpoint={jest.fn()} onEnded={jest.fn()} />);
    const video = screen.getByText("متصفحك لا يدعم تشغيل الفيديو.").closest("video") as HTMLVideoElement;
    fireEvent.waiting(video);
    expect(screen.getByText("الاتصال بطيء قليلًا")).toBeInTheDocument();
    fireEvent.error(video);
    expect(screen.getByRole("alert")).toHaveTextContent("تعذر تشغيل الفيديو");
    fireEvent.click(screen.getByRole("button", { name: "إعادة المحاولة" }));
    await waitFor(() => expect(HTMLMediaElement.prototype.load).toHaveBeenCalled());
  });
});
