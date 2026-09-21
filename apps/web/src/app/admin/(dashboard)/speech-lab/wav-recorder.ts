const TARGET_SAMPLE_RATE = 16_000;

export function resampleMono(input: Float32Array, sourceRate: number, targetRate = TARGET_SAMPLE_RATE) {
  if (!Number.isFinite(sourceRate) || sourceRate <= 0) throw new Error("Invalid source sample rate");
  if (!Number.isFinite(targetRate) || targetRate <= 0) throw new Error("Invalid target sample rate");
  if (input.length === 0 || sourceRate === targetRate) return new Float32Array(input);

  const outputLength = Math.max(1, Math.round(input.length * targetRate / sourceRate));
  const output = new Float32Array(outputLength);
  const ratio = sourceRate / targetRate;

  for (let index = 0; index < outputLength; index += 1) {
    const position = index * ratio;
    const left = Math.floor(position);
    const right = Math.min(left + 1, input.length - 1);
    const fraction = position - left;
    output[index] = input[left] * (1 - fraction) + input[right] * fraction;
  }
  return output;
}

export function encodePcm16Wav(samples: Float32Array, sampleRate = TARGET_SAMPLE_RATE) {
  const bytesPerSample = 2;
  const dataLength = samples.length * bytesPerSample;
  const buffer = new ArrayBuffer(44 + dataLength);
  const view = new DataView(buffer);

  const writeAscii = (offset: number, value: string) => {
    for (let index = 0; index < value.length; index += 1) {
      view.setUint8(offset + index, value.charCodeAt(index));
    }
  };

  writeAscii(0, "RIFF");
  view.setUint32(4, 36 + dataLength, true);
  writeAscii(8, "WAVE");
  writeAscii(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * bytesPerSample, true);
  view.setUint16(32, bytesPerSample, true);
  view.setUint16(34, 16, true);
  writeAscii(36, "data");
  view.setUint32(40, dataLength, true);

  let offset = 44;
  for (const sample of samples) {
    const clamped = Math.max(-1, Math.min(1, sample));
    const pcm = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff;
    view.setInt16(offset, Math.round(pcm), true);
    offset += bytesPerSample;
  }
  return buffer;
}

function mergeChunks(chunks: Float32Array[]) {
  const totalLength = chunks.reduce((total, chunk) => total + chunk.length, 0);
  const merged = new Float32Array(totalLength);
  let offset = 0;
  for (const chunk of chunks) {
    merged.set(chunk, offset);
    offset += chunk.length;
  }
  return merged;
}

export class PcmWavRecorder {
  private stream: MediaStream | null = null;
  private context: AudioContext | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private processor: ScriptProcessorNode | null = null;
  private chunks: Float32Array[] = [];
  private sampleRate = TARGET_SAMPLE_RATE;

  async start() {
    if (this.stream) throw new Error("Recorder is already running");

    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: false,
        noiseSuppression: false,
        autoGainControl: false,
      },
    });
    const context = new AudioContext();
    await context.resume();
    const source = context.createMediaStreamSource(stream);
    const processor = context.createScriptProcessor(4096, 1, 1);

    this.chunks = [];
    this.stream = stream;
    this.context = context;
    this.source = source;
    this.processor = processor;
    this.sampleRate = context.sampleRate;

    processor.onaudioprocess = (event) => {
      const channel = event.inputBuffer.getChannelData(0);
      this.chunks.push(new Float32Array(channel));
    };

    source.connect(processor);
    processor.connect(context.destination);
  }

  async stop() {
    const stream = this.stream;
    const context = this.context;
    const processor = this.processor;
    const source = this.source;

    if (!stream || !context || !processor || !source) throw new Error("Recorder is not running");

    processor.onaudioprocess = null;
    source.disconnect();
    processor.disconnect();
    stream.getTracks().forEach((track) => track.stop());

    this.stream = null;
    this.context = null;
    this.processor = null;
    this.source = null;

    await context.close();

    const merged = mergeChunks(this.chunks);
    this.chunks = [];
    if (merged.length === 0) throw new Error("No audio samples were captured");

    const resampled = resampleMono(merged, this.sampleRate, TARGET_SAMPLE_RATE);
    const wav = encodePcm16Wav(resampled, TARGET_SAMPLE_RATE);
    return new Blob([wav], { type: "audio/wav" });
  }

  cancel() {
    this.processor?.disconnect();
    this.source?.disconnect();
    this.stream?.getTracks().forEach((track) => track.stop());
    void this.context?.close();
    this.stream = null;
    this.context = null;
    this.processor = null;
    this.source = null;
    this.chunks = [];
  }
}
