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
