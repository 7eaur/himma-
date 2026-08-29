import { encodePcm16Wav, resampleMono } from "./wav-recorder";

describe("Speech Lab PCM WAV recorder helpers", () => {
  test("resamples mono audio to 16 kHz deterministically", () => {
    const source = new Float32Array(48_000);
    for (let index = 0; index < source.length; index += 1) source[index] = index / source.length;

    const output = resampleMono(source, 48_000, 16_000);

    expect(output).toHaveLength(16_000);
    expect(output[0]).toBeCloseTo(0);
    expect(output[8_000]).toBeCloseTo(0.5, 3);
  });

  test("encodes a valid mono 16-bit 16 kHz PCM WAV header", () => {
    const buffer = encodePcm16Wav(new Float32Array([0, 1, -1]), 16_000);
    const bytes = new Uint8Array(buffer);
    const view = new DataView(buffer);
    const ascii = (start: number, length: number) => String.fromCharCode(...bytes.slice(start, start + length));

    expect(ascii(0, 4)).toBe("RIFF");
    expect(ascii(8, 4)).toBe("WAVE");
    expect(ascii(12, 4)).toBe("fmt ");
    expect(ascii(36, 4)).toBe("data");
    expect(view.getUint16(20, true)).toBe(1);
    expect(view.getUint16(22, true)).toBe(1);
    expect(view.getUint32(24, true)).toBe(16_000);
    expect(view.getUint16(34, true)).toBe(16);
    expect(view.getUint32(40, true)).toBe(6);
  });

  test("clamps samples before PCM conversion", () => {
    const buffer = encodePcm16Wav(new Float32Array([2, -2]), 16_000);
    const view = new DataView(buffer);

    expect(view.getInt16(44, true)).toBe(32_767);
    expect(view.getInt16(46, true)).toBe(-32_768);
  });
});
