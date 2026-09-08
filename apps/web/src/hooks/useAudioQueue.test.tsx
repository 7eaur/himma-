import { act, renderHook, waitFor } from "@testing-library/react";
import { useAudioQueue } from "./useAudioQueue";

class FakeAudio {
  static instances: FakeAudio[] = [];

  src: string;
  onended: (() => void) | null = null;
  onerror: (() => void) | null = null;
  pause = jest.fn();
  play = jest.fn(async () => undefined);

  constructor(src = "") {
    this.src = src;
    FakeAudio.instances.push(this);
  }
}

beforeEach(() => {
  jest.clearAllMocks();
  FakeAudio.instances = [];
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
    expect(failed).toHaveBeenCalledTimes(1);
  });
});
