import os
import cv2
import math
import ffmpeg
import librosa
import subprocess
import numpy as np
from pathlib import Path

"""
============================
    pipeline.py
============================

🧠 ARQUITECTURA:

stream_processing()
 ├─ setup_output()
 ├─ get_video_metadata()
 ├─ init_stream_decoder()
 ├─ init_stream_encoder()
 ├─ analyze_speech_activity()
 ├─ process_frames_loop()
 │     ├─ read_frame()
 │     ├─ select_active_subject()
 │     ├─ get_camera_position()
 │     ├─ reframe_to_vertical()
 │     └─ write_frame()
 └─ close_streams()

 
========================================================================
TODO
(!)Posibilidad de realizar el analisis sobre el video de baja resolucion para
previsualizar en el front y ofrecer micro ajustes y sus resultados ??
(!)Crear una clase de config ??
========================================================================
"""


# output routes and dirs
OUTPUT_DIR = Path("output")
NORMALIZED_VIDEO = OUTPUT_DIR / "normalized"
PROCESSED_VIDEO = OUTPUT_DIR / "processed"
RESULT_VIDEO = OUTPUT_DIR / "result"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
NORMALIZED_VIDEO.mkdir(exist_ok=True)
PROCESSED_VIDEO.mkdir(exist_ok=True)
RESULT_VIDEO.mkdir(exist_ok=True)


# camera direction parameters
SWITCH_DISTANCE_RATIO = 0.25
CANDIDATE_CONFIRMATION_SEC = 0.5
NO_FACE_HOLD_SEC = 1.0
SMOOTHING_FACTOR = 0.15
MIN_HOLD_SEC = 0.8

# audio analysis parameters
AUDIO_SAMPLE_RATE = 16000
SPEECH_PERCENTILE = 65

# output params
TARGET_MAX_W = 1280
TARGET_FPS = 30
OUTPUT_ASPECT = 9 / 16

# loads and validates an OpenCV Haar Cascade classifier for face detection.
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
if face_cascade.empty():
    raise RuntimeError("Failed to load face cascade classifier")
#========================================================================   



def get_video_metadata(video_path):
    """
    Extracts basic metadata from a video file.

    Retrieves video stream properties required for:
    - frame decoding
    - camera logic scaling
    - stream-based processing

    Parameters
    ----------
    video_path : str
        Path to the input video file.

    Returns
    -------
    tuple (int, int, float)
        width  : Frame width in pixels
        height : Frame height in pixels
        fps    : Frames per second (float)

    Notes
    -----
    This function does not modify the video.
    It only inspects stream metadata using ffmpeg probe.
    """
    probe = ffmpeg.probe(video_path)
    vstream = next(s for s in probe["streams"] if s["codec_type"] == "video")
    w = int(vstream["width"])
    h = int(vstream["height"])
    num, den = map(int, vstream["r_frame_rate"].split("/"))
    fps = num / den if den != 0 else 0
    return w, h, fps




def normalize_video_segment(video_path, start_sec, end_sec,
                            target_fps=TARGET_FPS,
                            target_max_width=TARGET_MAX_W):
    """
    Cuts and conditionally normalizes a video segment for stable downstream processing.

    The function analyzes the input video stream and only re-encodes if required.
    Normalization is triggered when at least one of the following conditions is met:

    - Video codec is not H.264
    - Frame rate differs significantly from target_fps (±2 fps tolerance)
    - Width exceeds target_max_width (video will be downscaled preserving aspect ratio)
    - Pixel format is not yuv420p (required for broad compatibility)

    If no normalization is needed, the segment is cut using stream copy
    (no re-encoding, lossless and fast).

    This function ensures the video is in a format suitable for:
    face detection, frame-by-frame decoding, and re-encoding.

    Parameters
    ----------
    video_path : str
        Path to input video file.
    start_sec : float
        Segment start time in seconds.
    end_sec : float
        Segment end time in seconds.
    target_fps : int
        Desired output frames per second.
    target_max_width : int
        Maximum allowed video width.

    Returns
    -------
    str
        Path to normalized (or copied) video segment.
    """
    print("\n🎬 VIDEO NORMALIZATION...", flush=True)

    probe = ffmpeg.probe(video_path)
    vstream = next(s for s in probe["streams"] if s["codec_type"] == "video")

    codec = vstream.get("codec_name")
    width = int(vstream["width"])
    height = int(vstream["height"])
    pix_fmt = vstream.get("pix_fmt", "")
    fps_str = vstream["r_frame_rate"]
    num, den = map(int, fps_str.split("/"))
    fps = num / den if den else 0

    print(f"📂 {video_path}")
    print(f"🎞  Codec: {codec}")
    print(f"📐 Resolución: {width}x{height}")
    print(f"🎨 Pixel format: {pix_fmt}")
    print(f"⏱  FPS: {fps:.2f}\n", flush=True)

    needs_codec = codec not in ("h264", "libx264")
    needs_fps = abs(fps - target_fps) > 2
    needs_scale = width > target_max_width
    needs_pixfmt = pix_fmt != "yuv420p"

    output_path = str(NORMALIZED_VIDEO / Path(video_path).name)
    
    if not any([needs_codec, needs_fps, needs_scale, needs_pixfmt]):

        print("\n⚙️  Video is already normalized. Only cutting segment.\n", flush=True)

        (
            ffmpeg
            .input(video_path)
            .output(
                output_path,
                ss=start_sec,
                to=end_sec,
                vcodec="copy",
                acodec="copy",
                map="0",
                avoid_negative_ts="make_zero"
            )
            .overwrite_output()
            .run()
        )
        return output_path

    print("\n⚙️  Normalization needed:\n", flush=True)
    print(f"   Codec ok? {not needs_codec}")
    print(f"   FPS ok? {not needs_fps}")
    print(f"   Resolution ok? {not needs_scale}")
    print(f"   Pixel format ok? {not needs_pixfmt}\n", flush=True)

    stream = ffmpeg.input(video_path, ss=start_sec, to=end_sec)

    if needs_scale:
        stream = stream.filter("scale", target_max_width, -2)

    stream = (
        stream.output(
            output_path,
            vcodec="libx264",
            pix_fmt="yuv420p",
            r=target_fps,
            acodec="aac",
            audio_bitrate="128k",
            preset="fast",
            crf=23,
            movflags="+faststart"
        )
        .overwrite_output()
    )

    print("🚀 Runnig FFmpeg...\n", flush=True)
    ffmpeg.run(stream)

    print(f"✅ VIDEO NORMALIZED: {output_path}\n", flush=True)

    return output_path




def analyze_speech_activity(video_segment_path):
    """
    Estimate speech activity from a normalized video segment.

    Audio is extracted in-memory via FFmpeg, converted to mono 16 kHz,
    and analyzed using RMS energy.

    Returns a boolean mask aligned with video frames.
    """

    # 🎧 Extraer audio RAW en memoria
    cmd = [
        "ffmpeg",
        "-i", video_segment_path,
        "-ac", "1",          # mono
        "-ar", str(AUDIO_SAMPLE_RATE),      # sample rate
        "-f", "f32le",       # float32 PCM
        "-"
    ]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    audio_bytes = process.stdout.read()
    audio = np.frombuffer(audio_bytes, np.float32)

    sr = AUDIO_SAMPLE_RATE 
    hop = int(sr / TARGET_FPS)

    # 📈 Energía RMS por frame de video
    rms = librosa.feature.rms(y=audio, hop_length=hop)[0]

    # 🧠 Más robusto que percentil fijo
    threshold = np.median(rms) + 0.5 * np.std(rms)

    speech_mask = rms > threshold

    return speech_mask




def estimate_speaker_center(frame, voice_active, prev_center):
    """
    Estimates the most likely speaking person's face center in a frame.

    The function combines:
    - Face detection
    - Mouth region motion (variance)
    - Audio voice activity

    When voice is active, the face with the highest mouth motion is selected.
    When no voice is detected, the previous center is maintained.

    Filters out:
    - Faces too large/small
    - Faces too low in frame
    - Non-human false positives

    Parameters
    ----------
    frame : np.ndarray
        BGR image.
    voice_active : bool
        Whether speech is present at this frame.
    prev_center : tuple[int, int]
        Previously selected face center.

    Returns
    -------
    tuple[int, int]
        Estimated speaker center.
    """

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    faces = face_cascade.detectMultiScale(gray, 1.2, 5)

    best_motion = 0
    best_center = prev_center if prev_center else (w//2, h//2)
    frame_area = w * h

    MIN_FACE_AREA = 0.03
    MAX_FACE_AREA = 0.40

    for (x, y, fw, fh) in faces:
        if fw > w * 0.6:
            continue
        if y > h * 0.5:
            continue

        ratio = (fw * fh) / frame_area
        if ratio < MIN_FACE_AREA or ratio > MAX_FACE_AREA:
            continue

        mouth_y1 = int(y + fh * 0.6)
        mouth_y2 = int(y + fh * 0.85)
        mouth = gray[mouth_y1:mouth_y2, x:x+fw]

        motion = np.var(mouth)

        if motion > best_motion:
            best_motion = motion
            best_center = (x + fw//2, y + fh//2)

    if voice_active:
        return best_center
    else:
        return prev_center
    



#def track_face_center_stable(frame, prev_center):
#    """
#    Detects faces and returns a stable face center based on previous frame.
#
#    If multiple faces are detected, the function selects:
#    - the rightmost face on first detection
#    - the face closest to the previous center on subsequent frames
#
#    This provides basic temporal stability but does NOT handle:
#    - speaker detection
#    - scene logic
#    - camera decisions
#
#    Parameters
#    ----------
#    frame : np.ndarray
#        BGR image frame.
#    prev_center : tuple[int, int] or None
#        Face center from previous frame.
#
#    Returns
#    -------
#    tuple[int, int] or None
#        Selected face center.
#    """
#    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#    faces = face_cascade.detectMultiScale(gray, 1.1, 5)
#
#    if len(faces) == 0:
#        return prev_center
#
#    centers = [(x + w//2, y + h//2) for (x,y,w,h) in faces]
#
#    if prev_center is None:
#        return max(centers, key=lambda c: c[0])  # o por tamaño si querés
#
#    # distancia euclídea al centro anterior
#    return min(
#        centers,
#        key=lambda c: math.hypot(c[0] - prev_center[0], c[1] - prev_center[1])
#    )




def detect_face_centers(frame):
    """
    Detects faces and returns their center coordinates.

    This function performs raw face detection only.
    It does not decide which face to follow.

    Returns
    -------
    list of (x, y)
        Center points of detected faces.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5)

    # devolver centros
    return [(x + w//2, y + h//2) for (x, y, w, h) in faces]




def merge_audio_track(processed_video_path,
                      normalized_video_path):
    """
    Merges the original audio track into a processed video file.

    The function:
    - Extracts the audio segment from the normalized_video_path(!)
    - Copies the processed video stream (no re-encoding)
    - Encodes audio to AAC
    - Produces a final output with synchronized streams

    Parameters
    ----------
    processed_video_path : str
        Path to the processed video (without audio).
    original_video_path : str
        Path to the original source video.

    Returns
    -------
    str
        Path to the final video with audio merged.

    Notes
    -----
    - Video stream is copied (vcodec="copy") to preserve quality.
    - Audio is encoded to AAC for compatibility.
    - The output duration matches the shortest stream.
    """
    output_path = str(RESULT_VIDEO / Path(processed_video_path).name)

    video_in = ffmpeg.input(processed_video_path)
    audio_in = ffmpeg.input(normalized_video_path)

    (
        ffmpeg
        .output(
            video_in.video,   # video del archivo procesado
            audio_in.audio,   # audio del original
            output_path,
            vcodec="copy",
            acodec="aac",
            shortest=None
        )
        .overwrite_output()
        .run()
    )
    print("\n🔊 Audio added\n")
    return output_path




class CameraDirector:
    """
    Cinematic camera direction logic for automated reframing.

    This class acts as the "brain" of the virtual camera. It converts noisy
    detection data (faces, speaker position, motion) into stable, human-like
    camera behavior.

    The director enforces cinematic rules to avoid jitter and unnatural motion.

    Core behaviors implemented
    --------------------------
    • Minimum hold time before camera can move
    • Consensus-based subject switching (prevents false jumps)
    • Smooth transitions with bounded duration
    • Intelligent hard cuts for strong speaker changes
    • Fusion of audio (speech) and visual detection
    • Anti ping-pong logic (prevents rapid back-and-forth)

    Camera States
    -------------
    HOLD        : Camera remains stable
    TRANSITION  : Camera smoothly moves toward a new framing target

    Parameters
    ----------
    frame_width : int
        Width of the input video frame. Used to scale movement thresholds.
    fps : float
        Frame rate of the video. Used to convert timing rules into frame counts.

    Notes
    -----
    This class does NOT:
    - detect faces
    - analyze audio
    - crop frames

    It ONLY decides *where the camera should point*.
    """
    def __init__(self, frame_width, fps):
        self.w = frame_width
        self.fps = fps

        self.current_x = frame_width // 2
        self.target_x = None
        self.mode = "HOLD"

        self.frames_in_state = 0
        self.hold_frames = 0

        self.possible_target = None
        self.possible_counter = 0

        # Parámetros
        self.MOVE_THRESHOLD = int(frame_width * 0.18)
        self.HARD_CUT_THRESHOLD = int(frame_width * 0.35)

        self.HOLD_MIN = int(fps * 0.5)
        self.CONSENSUS = int(fps * 0.25)

        self.TRANSITION_MIN = int(fps * 0.3)
        self.TRANSITION_MAX = int(fps * 0.6)

    def update(self, detected_x, is_voice):
        """
        Updates camera position based on subject detection and speech activity.

        Decision flow
        -------------
        1. Hard cut if:
           - Voice is active
           - Subject jump is very large

        2. Build consensus if subject is drifting away:
           - Candidate must persist for several frames

        3. HOLD state:
           - Enforces minimum time before moving
           - Switches to TRANSITION if consensus is reached

        4. TRANSITION state:
           - Smoothly interpolates camera position
           - Stops when close enough to target

        Parameters
        ----------
        detected_x : int
            X coordinate of detected subject.
        is_voice : bool
            Whether speech is present in this frame.

        Returns
        -------
        int
            Updated camera X position.
        """


        # ================= HARD CUT =================
        if is_voice and abs(detected_x - self.current_x) > self.HARD_CUT_THRESHOLD:
            self.current_x = detected_x
            self.mode = "HOLD"
            self.hold_frames = 0
            self.frames_in_state = 0
            return self.current_x

        # ================= CONSENSO =================
        if abs(detected_x - self.current_x) > self.MOVE_THRESHOLD:
            if self.possible_target is None:
                self.possible_target = detected_x
                self.possible_counter = 1
            else:
                if abs(detected_x - self.possible_target) < self.MOVE_THRESHOLD:
                    self.possible_counter += 1
                else:
                    self.possible_target = detected_x
                    self.possible_counter = 1
        else:
            self.possible_target = None
            self.possible_counter = 0

        # ================= HOLD =================
        if self.mode == "HOLD":

            self.hold_frames += 1

            if (
                self.possible_counter > self.CONSENSUS and
                self.hold_frames > self.HOLD_MIN
            ):
                self.mode = "TRANSITION"
                self.target_x = self.possible_target
                self.frames_in_state = 0
                self.hold_frames = 0

        # ================= TRANSITION =================
        elif self.mode == "TRANSITION":

            self.frames_in_state += 1

            progress = min(
                1.0,
                self.frames_in_state / self.TRANSITION_MAX
            )

            self.current_x = int(
                self.current_x +
                (self.target_x - self.current_x) * progress
            )

            if (
                self.frames_in_state > self.TRANSITION_MIN and
                abs(self.current_x - self.target_x) < 5
            ):
                self.mode = "HOLD"
                self.current_x = self.target_x
                self.target_x = None
                self.frames_in_state = 0

        return self.current_x




def init_stream_decoder(video_path):
    """Opens FFmpeg process that streams raw BGR frames."""
    return (
        ffmpeg
        .input(video_path)
        .output('pipe:', format='rawvideo', pix_fmt='bgr24')
        .run_async(pipe_stdout=True)
    )



def init_stream_encoder(output_path, actual_w, actual_h, fps):
    """Opens FFmpeg encoder process receiving raw frames via stdin."""
    return (
        ffmpeg
        .input('pipe:', format='rawvideo', pix_fmt='bgr24',
               s=f"{actual_w}x{actual_h}", framerate=fps)
        .output(
            output_path,
            vcodec='libx264',
            pix_fmt='yuv420p',
            movflags='+faststart'
        )
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )



def update_active_speaker(faces, active_center, candidate_center,
                          candidate_frames, active_lock_frames,
                          fps, w):
    """
    Determines which detected face should be considered the current main subject.

    This function implements temporal stability so the system does NOT rapidly
    jump between different faces. It keeps tracking the current subject,
    evaluates possible new subjects, and only switches after persistence.

    It does NOT control the camera. It only decides *who* the subject is.

    Parameters
    ----------
    faces : list[tuple[int, int]]
        List of detected face centers in the current frame.
        Each item is (x, y) in pixel coordinates.

    active_center : tuple[int, int] or None
        The center of the subject currently being tracked.
        None means no subject is currently active (scene mode).

    candidate_center : tuple[int, int] or None
        A potential new subject detected but not yet confirmed.
        Used to avoid instant switching when another face appears.

    candidate_frames : int
        Number of consecutive frames the candidate subject has been
        consistently detected near the same position.
        Used to require persistence before switching.

    active_lock_frames : int
        Counter representing how long the current subject has been
        continuously tracked (positive values) or missing (negative values).
        If this drops below -fps, the system abandons the subject.

    fps : float
        Video frames per second.
        Used to convert time-based logic (like 0.5 seconds) into frame counts.

    w : int
        Frame width in pixels.
        Used to compute distance thresholds relative to image size.

    Returns
    -------
    new_active_center : tuple[int, int] or None
        The subject that should now be tracked.

    new_candidate_center : tuple[int, int] or None
        Updated candidate subject (if any).

    new_candidate_frames : int
        Updated persistence counter for the candidate.

    new_active_lock_frames : int
        Updated lock counter for the active subject.

    Behavior Summary
    ----------------
    • Keeps the current subject if still spatially close  
    • Starts evaluating a new subject only if far enough  
    • Requires ~0.5 seconds of persistence before switching  
    • Abandons subject after ~1 second of absence  
    • Prevents rapid “ping-pong” switching between faces
    """
    # ================= NO FACES =================
    if not faces:
        active_lock_frames -= 1

        # Lost subject for too long → no active subject
        if active_lock_frames < -fps:
            return None, None, 0, active_lock_frames

        return active_center, candidate_center, candidate_frames, active_lock_frames

    # ================= FIND NEAREST FACE =================
    if active_center:
        nearest = min(
            faces,
            key=lambda c: math.hypot(c[0]-active_center[0], c[1]-active_center[1])
        )
        dist = math.hypot(nearest[0]-active_center[0], nearest[1]-active_center[1])
    else:
        nearest = max(faces, key=lambda c: c[0])  # heuristic
        dist = 0

    SWITCH_DIST = w * 0.25

    # ================= SAME SUBJECT =================
    if dist < SWITCH_DIST:
        return nearest, None, 0, active_lock_frames + 1

    # ================= CANDIDATE SUBJECT =================
    if candidate_center is None:
        return active_center, nearest, 1, active_lock_frames

    if math.hypot(nearest[0]-candidate_center[0], nearest[1]-candidate_center[1]) < 50:
        candidate_frames += 1
    else:
        return active_center, None, 0, active_lock_frames

    # Switch only if persistent
    if candidate_frames > fps * 0.5:
        return candidate_center, None, 0, active_lock_frames

    return active_center, candidate_center, candidate_frames, active_lock_frames




def reframe_vertical(frame, camera_x, final_w, final_h):
    """Crops frame to vertical 9:16 region centered on camera_x."""
    h, w = frame.shape[:2]

    x1 = max(0, min(w - final_w, camera_x - final_w // 2))
    crop = frame[:, x1:x1 + final_w]

    return crop  # 👈 tamaño fijo




def close_streams(decoder, encoder):
    """Properly closes FFmpeg pipes."""
    decoder.stdout.close()
    encoder.stdin.close()
    decoder.wait()
    encoder.wait()



def stream_processing(video_path):
    """
    Main video processing pipeline.
    Reads video frames via FFmpeg pipe, tracks active speaker,
    directs virtual camera, reframes to vertical, and encodes output.
    Audio is NOT processed here.
    """
    print("\n🎬 PROCESSING STREAM...\n", flush=True)

    output_path = str(PROCESSED_VIDEO / Path(video_path).name)

    w, h, fps = get_video_metadata(video_path)
    # tamaño 9:16 que entra dentro del video original
    crop_w = int(h * OUTPUT_ASPECT)
    crop_w = min(crop_w, w)

    FINAL_W = crop_w
    FINAL_H = h

    director = CameraDirector(w, fps)

    decoder = init_stream_decoder(video_path)
    encoder = init_stream_encoder(output_path, FINAL_W, FINAL_H, fps)

    voice_mask = analyze_speech_activity(video_path)

    frame_size = w * h * 3
    frame_idx = 0

    active_center = None
    candidate_center = None
    candidate_frames = 0
    active_lock_frames = 0

    while True:
        in_bytes = decoder.stdout.read(frame_size)
        if not in_bytes:
            break

        frame = np.frombuffer(in_bytes, np.uint8).reshape([h, w, 3])

        faces = detect_face_centers(frame)

        active_center, candidate_center, candidate_frames, active_lock_frames = update_active_speaker(
            faces, active_center, candidate_center,
            candidate_frames, active_lock_frames,
            fps, w
        )

        detected_x = active_center[0] if active_center else w // 2
        is_voice = frame_idx < len(voice_mask) and voice_mask[frame_idx]

        camera_x = director.update(detected_x, is_voice)

        out_frame = reframe_vertical(frame, camera_x, FINAL_W, FINAL_H)

        encoder.stdin.write(out_frame.tobytes())

        frame_idx += 1
    close_streams(decoder, encoder)

    print(f"\n✅ VIDEO PROCESSED: {output_path}\n", flush=True)
    return output_path




def generate_video(video_path):
    """
    Executes the full visual processing pipeline on a normalized segment
    and merges the original audio track at the end.

    Parameters
    ----------
    normalized_segment_path : str
        Path to the normalized and already-trimmed video segment.

    Returns
    -------
    str
        Final processed video with audio.
    """

    # 1. Reframe / crop / camera logic
    no_audio_out = stream_processing(video_path)

    # 2. Merge original audio track
    result_video = merge_audio_track(no_audio_out, video_path)
    print(f"✅ RESULT VIDEO: {result_video}\n", flush=True)

    return result_video




# ================= PIPELINE MAIN =================
def process(video_path, start, end):
    # check video_path
        # TODO...

    normalized_video_path = normalize_video_segment(video_path, start, end)
    generate_video(normalized_video_path)