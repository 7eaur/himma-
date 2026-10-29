import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ComponentProps } from "react";

import V2ReviewedAudioPlayer from "./V2ReviewedAudioPlayer";

const fetchMock = jest.fn();

beforeEach(() => {
  fetchMock.mockReset();
  global.fetch = fetchMock;
});

function player(overrides: Partial<ComponentProps<typeof V2ReviewedAudioPlayer>> = {}) {
  return {
    id: "student-audio", src: "/api/private-audio", audioSubmissionId: 17,
    completionUrl: "/api/audio-completed", initiallyCompleted: false,
    onCompletionChange: jest.fn(), ...overrides,
  };
}

it("acknowledges only after playback ends", async () => {
  fetchMock.mockResolvedValue({ ok: true, json: async () => ({ status: "playback_completed" }) });
  const props = player();
  render(<V2ReviewedAudioPlayer {...props} />);
  expect(fetchMock).not.toHaveBeenCalled();
  fireEvent.ended(screen.getByLabelText("استمع للتسجيل كاملًا قبل التقييم"));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(
    "/api/audio-completed",
    expect.objectContaining({ method: "POST", body: JSON.stringify({ audio_submission_id: 17 }) }),
  ));
  expect(await screen.findByText("اكتمل الاستماع. يمكنك الآن اعتماد القراءة.")).toBeInTheDocument();
  expect(props.onCompletionChange).toHaveBeenLastCalledWith(true);
});

it("keeps the review locked when the acknowledgement fails", async () => {
  fetchMock.mockResolvedValue({ ok: false, json: async () => ({ detail: "انتهت صلاحية المراجعة" }) });
  const props = player();
  render(<V2ReviewedAudioPlayer {...props} />);
  fireEvent.ended(screen.getByLabelText("استمع للتسجيل كاملًا قبل التقييم"));
  expect(await screen.findByRole("alert")).toHaveTextContent("انتهت صلاحية المراجعة");
  expect(props.onCompletionChange).toHaveBeenLastCalledWith(false);
});

it("restores a server acknowledgement and resets for a new audio revision", () => {
  const first = player({ initiallyCompleted: true });
  const { rerender } = render(<V2ReviewedAudioPlayer key={first.audioSubmissionId} {...first} />);
  expect(screen.getByText("اكتمل الاستماع. يمكنك الآن اعتماد القراءة.")).toBeInTheDocument();
  const second = player({ audioSubmissionId: 18, src: "/api/new-private-audio" });
  rerender(<V2ReviewedAudioPlayer key={second.audioSubmissionId} {...second} />);
  expect(screen.queryByText("اكتمل الاستماع. يمكنك الآن اعتماد القراءة.")).not.toBeInTheDocument();
});

it("retries a failed ACK without replaying audio and holds the decision until success", async () => {
  let finish: (value: unknown) => void = () => { throw new Error("pending ACK not created"); };
  fetchMock.mockResolvedValueOnce({ ok: false, json: async () => ({ detail: "تعذر الاتصال" }) })
    .mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  const props = player();
  render(<V2ReviewedAudioPlayer {...props} />);
  expect(screen.queryByRole("button")).not.toBeInTheDocument();
  const audio = screen.getByLabelText("استمع للتسجيل كاملًا قبل التقييم");
  fireEvent.ended(audio);
  const retry = await screen.findByRole("button", { name: "إعادة تأكيد اكتمال الاستماع" });
  expect(props.onCompletionChange).toHaveBeenLastCalledWith(false);
  fireEvent.click(retry);
  fireEvent.ended(audio);
  expect(fetchMock).toHaveBeenCalledTimes(2);
  expect(props.onCompletionChange).not.toHaveBeenCalledWith(true);
  expect(retry).toBeDisabled();
  finish({ ok: true, json: async () => ({ status: "playback_completed" }) });
  expect(await screen.findByText("اكتمل الاستماع. يمكنك الآن اعتماد القراءة.")).toBeInTheDocument();
  expect(props.onCompletionChange).toHaveBeenLastCalledWith(true);
  expect(fetchMock.mock.calls[1]).toEqual(fetchMock.mock.calls[0]);
  expect(screen.queryByRole("button")).not.toBeInTheDocument();
});

it("discards completion and late ACKs when the recording revision changes", async () => {
  let finish: (value: unknown) => void = () => { throw new Error("pending ACK not created"); };
  fetchMock.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  const first = player();
  const { rerender } = render(<V2ReviewedAudioPlayer {...first} />);
  fireEvent.ended(screen.getByLabelText("استمع للتسجيل كاملًا قبل التقييم"));
  const second = player({ audioSubmissionId: 18, src: "/api/new-private-audio" });
  rerender(<V2ReviewedAudioPlayer {...second} />);
  finish({ ok: true, json: async () => ({ status: "playback_completed" }) });
  await waitFor(() => expect(screen.queryByText("جارٍ تسجيل اكتمال التشغيل...")).not.toBeInTheDocument());
  expect(first.onCompletionChange).not.toHaveBeenCalled();
  expect(second.onCompletionChange).not.toHaveBeenCalled();
  expect(screen.queryByText("اكتمل الاستماع. يمكنك الآن اعتماد القراءة.")).not.toBeInTheDocument();
  expect(screen.queryByRole("button")).not.toBeInTheDocument();
});
