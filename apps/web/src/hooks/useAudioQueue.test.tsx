import { act, renderHook, waitFor } from "@testing-library/react";
import { useAudioQueue } from "./useAudioQueue";

type Deferred = {
  promise: Promise<void>;
  resolve: () => void;
  reject: (reason?: unknown) => void;
};

function deferred(): Deferred {
  let resolve!: () => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<void>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

class FakeAudio {
  static instances: FakeAudio[] = [];
  static deferredPlayback = false;

  src: string;
  onended: (() => void) | null = null;
  onerror: (() => void) | null = null;
  pause = jest.fn();
  currentPlay = deferred();
  play = jest.fn(() => {
    if (FakeAudio.deferredPlayback) return this.currentPlay.promise;
    return Promise.resolve();
  });

  constructor(src = "") {
    this.src = src;
    FakeAudio.instances.push(this);
  }
}

beforeEach(() => {
  jest.clearAllMocks();
  FakeAudio.instances = [];
  FakeAudio.deferredPlayback = false;
  Object.defineProperty(globalThis, "Audio", {
    configurable: true,
    writable: true,
    value: FakeAudio,
  });
});

describe("useAudioQueue", () => {
  it("fires completion only after the final queued asset ends naturally", async () => {
    const completed = jest.fn();
    const { result } = renderHook(() => useAudioQueue(undefined, completed));

    act(() => result.current.toggle(["/first.mp3", "/second.mp3"]));

    await waitFor(() => expect(result.current.state).toBe("playing"));
    expect(FakeAudio.instances).toHaveLength(1);
    expect(FakeAudio.instances[0].src).toBe("/first.mp3");
    expect(completed).not.toHaveBeenCalled();

    act(() => FakeAudio.instances[0].onended?.());

    await waitFor(() => expect(FakeAudio.instances).toHaveLength(2));
    await waitFor(() => expect(result.current.state).toBe("playing"));
    expect(FakeAudio.instances[1].src).toBe("/second.mp3");
    expect(completed).not.toHaveBeenCalled();

    act(() => FakeAudio.instances[1].onended?.());

    await waitFor(() => expect(result.current.state).toBe("idle"));
    expect(completed).toHaveBeenCalledTimes(1);
  });

  it("does not treat manual stop as natural completion", async () => {
    const completed = jest.fn();
    const { result } = renderHook(() => useAudioQueue(undefined, completed));

    act(() => result.current.toggle(["/story.mp3"]));
    await waitFor(() => expect(result.current.state).toBe("playing"));

    act(() => result.current.stop());

    expect(result.current.state).toBe("idle");
    expect(completed).not.toHaveBeenCalled();
    expect(FakeAudio.instances[0].pause).toHaveBeenCalled();
  });

  it("does not treat a playback error as completion", async () => {
    const completed = jest.fn();
    const failed = jest.fn();
    const { result } = renderHook(() => useAudioQueue(failed, completed));

    act(() => result.current.toggle(["/broken.mp3"]));
    await waitFor(() => expect(result.current.state).toBe("playing"));

    act(() => FakeAudio.instances[0].onerror?.());

    await waitFor(() => expect(result.current.state).toBe("idle"));
    expect(completed).not.toHaveBeenCalled();
    expect(failed).toHaveBeenCalledWith("تعذر تشغيل الصوت. حاول مرة أخرى.");
  });

  it("ignores repeated taps while the same browser play request is pending", () => {
    FakeAudio.deferredPlayback = true;
    const { result } = renderHook(() => useAudioQueue());

    act(() => result.current.toggle(["/one.mp3"]));
    act(() => result.current.toggle(["/one.mp3"]));
    act(() => result.current.toggle(["/one.mp3"]));

    expect(FakeAudio.instances).toHaveLength(1);
    expect(FakeAudio.instances[0].play).toHaveBeenCalledTimes(1);
  });

  it("ignores a stale rejected promise after the student switches to a new sound", async () => {
    FakeAudio.deferredPlayback = true;
    const failed = jest.fn();
    const { result } = renderHook(() => useAudioQueue(failed));

    act(() => result.current.toggle(["/old.mp3"]));
    const oldAudio = FakeAudio.instances[0];

    act(() => result.current.toggle(["/new.mp3"]));
    const newAudio = FakeAudio.instances[1];

    await act(async () => {
      oldAudio.currentPlay.reject(new Error("interrupted by a newer request"));
      await Promise.resolve();
      newAudio.currentPlay.resolve();
      await Promise.resolve();
    });

    expect(result.current.state).toBe("playing");
    expect(newAudio.pause).not.toHaveBeenCalled();
    expect(failed).not.toHaveBeenCalledWith("تعذر تشغيل الصوت. حاول مرة أخرى.");
  });
});
