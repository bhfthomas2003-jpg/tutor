"""Simple, dependency-light renderer: Pillow slides + captions -> FFmpeg. (Manim templates come next.)"""
import json, os, shutil, subprocess, textwrap, uuid, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from ..config import S
from . import voice

BG, FG, ACC, CAP = (14, 22, 45), (240, 244, 255), (255, 193, 7), (0, 0, 0)

def _font(sz, bold=False):
    n = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for d in ("", "/usr/share/fonts/truetype/dejavu/"):
        try: return ImageFont.truetype(d + n, sz)
        except OSError: pass
    return ImageFont.load_default()

def _wrap(d, text, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else: lines.append(cur); cur = w
    return lines + ([cur] if cur else [])

def _slide(W, H, title, sub, math_lines, caption, path):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    u = W / 1280 if W > H else W / 720
    m = int(W * 0.07); y = int(H * 0.08)
    for t in _wrap(d, title, _font(int(46*u), True), W - 2*m):
        d.text((m, y), t, font=_font(int(46*u), True), fill=ACC); y += int(60*u)
    if sub:
        for t in _wrap(d, sub, _font(int(26*u)), W - 2*m):
            d.text((m, y), t, font=_font(int(26*u)), fill=FG); y += int(36*u)
    y += int(20*u); f = _font(int(36*u))
    for ml in math_lines:
        for t in _wrap(d, ml, f, W - 2*m):
            d.text((m, y), t, font=f, fill=FG); y += int(50*u)
        y += int(10*u)
    if caption:
        cf = _font(int(28*u)); cl = _wrap(d, caption, cf, W - 2*m)
        h = len(cl) * int(38*u) + int(24*u); top = H - h - int(H*0.05)
        d.rectangle([0, top, W, top + h], fill=CAP)
        for i, t in enumerate(cl):
            d.text((m, top + int(12*u) + i*int(38*u)), t, font=cf, fill=(255, 255, 255))
    im.save(path)

def _dur(p):
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    return float(o.stdout.strip())

def _ff(*a):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *a], capture_output=True, text=True)
    if r.returncode: raise RuntimeError("FFmpeg failed: " + r.stderr[-300:])

def _segment(work, idx, W, H, title, sub, math_lines, narration, audio, fixed=None):
    d = _dur(audio) if audio else fixed
    words = narration.split() if narration else []
    chunks = [" ".join(words[i:i+10]) for i in range(0, len(words), 10)] or [""]
    n, lst = len(chunks), []
    for i, c in enumerate(chunks):
        show = math_lines[:max(1, math.ceil((i+1) / n * len(math_lines)))] if math_lines else []
        p = work / f"s{idx}_{i}.png"; _slide(W, H, title, sub, show, c, p)
        lst += [f"file '{p.name}'", f"duration {d * max(len(c.split()), 1) / max(len(words), 1) if words else d:.3f}"]
    lst.append(lst[-2])
    (work / f"l{idx}.txt").write_text("\n".join(lst))
    out = work / f"seg{idx}.mp4"
    ain = ["-i", str(audio)] if audio else ["-f", "lavfi", "-t", f"{d}", "-i", "anullsrc=r=44100:cl=stereo"]
    _ff("-f", "concat", "-safe", "0", "-i", str(work / f"l{idx}.txt"), *ain, "-vf", "fps=15,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-c:a", "aac", "-ar", "44100", "-ac", "2", "-shortest", str(out))
    return out

TPL = Path(__file__).resolve().parents[1] / "templates" / "steps_scene.py"

def manim_ok():
    return bool(shutil.which("manim"))

TPLV = TPL.with_name("visual_scenes.py")
CLS = {"graph": "PlotScene", "numberline": "NumberLineScene", "geometry": "GeometryScene"}

def _manim_segment(work, idx, W, H, title, math_lines, narration, audio, kind="steps", visual=None):
    """Animated scene via Manim, then muxed with narration. Raises on any failure (caller falls back)."""
    d = _dur(audio); words = narration.split()
    spec = {"title": title, "math": math_lines, "duration": d, "chunks": [" ".join(words[i:i+10]) for i in range(0, len(words), 10)], "visual": visual or {}}
    sp = work / f"spec{idx}.json"; sp.write_text(json.dumps(spec))
    r = subprocess.run(["manim", "-ql", "-r", f"{W},{H}", "--fps", "15", "--disable_caching", "--media_dir", str(work / f"m{idx}"),
                        "-o", f"a{idx}.mp4", str(TPLV if kind in CLS else TPL), CLS.get(kind, "StepsScene")], capture_output=True, text=True,
                       env={**os.environ, "MANIM_SPEC": str(sp)}, timeout=600)
    found = list((work / f"m{idx}").rglob(f"a{idx}.mp4"))
    if r.returncode or not found: raise RuntimeError("Manim failed: " + r.stderr[-200:])
    out = work / f"seg{idx}.mp4"
    _ff("-i", str(found[0]), "-i", str(audio), "-map", "0:v", "-map", "1:a", "-vf", f"fps=15,scale={W}:{H},format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-c:a", "aac", "-ar", "44100", "-ac", "2", "-shortest", str(out))
    return out

def run(job_id, req, set_status):
    try:
        W, H = (1280, 720) if req.orientation == "landscape" else (720, 1280)
        work = S.data / "jobs" / job_id; work.mkdir(exist_ok=True)
        total = len(req.scenes) + (2 if req.intro.enabled else 1); done = 0; segs = []
        def step(msg):
            nonlocal done; done += 1; set_status("running", f"{msg} ({done}/{total})", done / total)
        if req.intro.enabled:
            a = voice.tts(req.intro.script, req.voice)  # cached when unchanged
            segs.append(_segment(work, 0, W, H, req.intro.name, req.intro.title, [], req.intro.script, a)); step("Introduction")
        segs.append(_segment(work, 1, W, H, req.title, "", [], "", None, fixed=2.5)); step("Title card")
        for i, s in enumerate(req.scenes):
            a = voice.tts(s.narration, req.voice)
            seg = None
            if req.engine == "manim" and manim_ok():
                try: seg = _manim_segment(work, 10 + i, W, H, s.title, s.math, s.narration, a, s.kind, s.visual)
                except Exception: seg = None  # automatic fallback to the simple renderer
            segs.append(seg or _segment(work, 10 + i, W, H, s.title, "", s.math, s.narration, a)); step(f"Scene {i+1}")
        lst = work / "all.txt"; lst.write_text("\n".join(f"file '{p.name}'" for p in segs))
        out = S.data / "videos" / f"{job_id}.mp4"
        _ff("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out))
        set_status("done", "Finished", 1.0)
    except Exception as e:
        msg = getattr(e, "detail", None) or str(e)
        set_status("error", str(msg)[:300], 0)
