# Brief: Streaming synthesis into live playback

- **Project:** ReadOut
- **Status:** Implemented behind a config flag (default off), unit-tested; real-audio proof pending
- **Source revision:** see git log for `feat: streaming synthesis into live playback`
- **Evidence date:** 2026-10-26
- **Owner:** Dave Robertson

## User problem

`tts_engine.speak()` runs the whole Kokoro generator, concatenates every chunk,
and only then calls `sounddevice.play`. For a long selection (up to the
20,000-character cap) the user hears nothing until the entire text has been
synthesised, and the control panel shows "Synthesizing…" for that whole time.
Stop only takes effect once synthesis has finished.

## Expected outcome

Audio begins after the first sentence is synthesised. Later sentences are
synthesised while earlier ones play. Stop halts playback and discards
unsynthesised text at once. Saving still produces one complete WAV.

## Flow

1. `/speak` (or `/preview`) arrives with `streaming_playback: true` in config.
2. The engine synthesises the first chunk synchronously so an empty or failing
   generator still returns an error with no audio started.
3. A `StreamPlayer` opens a `sounddevice.OutputStream` (24 kHz mono float32)
   and starts playing the first chunk from a bounded queue.
4. A producer thread drains the rest of the generator into the queue.
5. The stream callback zero-fills on underrun and stops itself when the
   producer is done and the queue is empty.
6. `/speak` returns `{"status": "playing", "streaming": true}` as soon as
   playback starts. If a save was requested, the call waits for synthesis to
   finish (playback is already audible) so `saved_to` stays in the response.

## Smallest useful slice (this change)

- `streaming_playback` config key, default `false`, patchable via
  `PATCH /config` and a switch on the control panel Settings tab.
- `StreamPlayer` in `tts_engine.py` with push, finish, stop, state.
- Sentence-aware `split_pattern` in streaming mode only
  (`(?<=[.!?])\s+|\n+`); batch mode keeps `\n+` for parity.
- `stop_audio()` and `play_audio()` (cloud engines) stop any live stream.
- `/status` gains `streaming_playback` and `playback` (state, chunks queued,
  chunks played, underruns).
- Unit tests with fake sounddevice stream and fake numpy.

## Exclusions

- Pause, resume, seek and position (item 2 of the upgrade assessment).
- Server-sent events (item 3); the panel still polls.
- Job queue and cancellation tokens (item 4); a new request still replaces
  the current one.
- Cloud engines keep buffered playback; OpenAI and ElevenLabs streaming is
  item 19.
- Loudness normalisation and crossfades at chunk seams (item 7).

## Rule, data, save and API effects

- Config: new key `streaming_playback` (bool).
- API: `/speak` and `/preview` responses may include `streaming: true`;
  `/status` adds `streaming_playback` and `playback`. No endpoint removed.
- Save: unchanged file format and location; in streaming mode the response
  waits for synthesis to finish before returning `saved_to`.
- History: unchanged.
- Security: no new network surface; the flag is only reachable through the
  existing origin-guarded `PATCH /config`.

## Dependencies

- `sounddevice` (already required) provides `OutputStream`.
- Kokoro yields chunks per `split_pattern`; chunk audio is a CPU tensor or
  array and is converted with `numpy.asarray`.

## Risks

- PortAudio underruns on slow CPUs if a sentence takes longer to synthesise
  than the previous one takes to play. Mitigation: zero-fill, underrun counter
  in `/status`, flag off by default until measured.
- A producer error after the first chunk leaves the response already sent as
  `playing`. Mitigation: the player records the error and `/status.playback`
  exposes it.
- Sentence splitting changes chunk boundaries versus batch mode. Mitigation:
  streaming only; batch mode unchanged.

## Observable acceptance

- Unit: `python -m pytest tests/test_streaming_playback.py` passes; existing
  suites unchanged.
- Manual (docs/QA.md section 2b): with the flag on, `qa_probe.py speak` on a
  ten-paragraph text starts audibly within about one second on an M-series
  Mac; `stop` silences within one sentence; `--save` produces a WAV of the
  full text; `/status.playback.underruns` stays at 0 on an idle machine.
- Decision SP-1 answered before the default flips.

## Decisions for Dave (NEXT-5)

- **SP-1 Default state.** (A) Keep off until the real-audio harness
  (assessment item 22) measures underruns on each target machine.
  (B) Flip on now for macOS only. (C) Flip on everywhere.
  Recommended: A. Unlocks: safe default change with evidence.
- **SP-2 Save semantics in streaming mode.** (A) Wait for synthesis so
  `saved_to` stays in the response (implemented). (B) Return at once and
  surface the path later via `/status`. Recommended: A until SSE (item 3)
  exists. Unlocks: whether the control panel needs a second poll for the path.
