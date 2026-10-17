# Rendering
Milestone 1 uses `backend/app/services/render.py`: Pillow draws each slide (title, math lines revealed step by step, burned-in subtitles) and FFmpeg joins slides + narration into MP4 (16:9 = 1280x720, 9:16 = 720x1280).
Math is shown as plain Unicode text (x², √), not typeset LaTeX.
`templates/` is reserved for Manim scene templates (next milestone). The Pillow path stays as the fallback when Manim is unavailable.

## Manim (optional)
Template: `backend/app/templates/steps_scene.py` (title, step-by-step math lines, timed subtitles, driven by a JSON spec). Pick 'Manim animation' in Video Generator. If Manim is missing or a scene fails, that scene silently falls back to the simple renderer.
Enable in Docker: build with `--build-arg WITH_MANIM=1` (bigger image, slower builds and renders; may not fit free tiers). Math is Unicode text; LaTeX typesetting (MathTex) is not enabled.

### Visual templates
`backend/app/templates/visual_scenes.py`: PlotScene (graph: functions, ranges, points), NumberLineScene (intervals, points), GeometryScene (points, segments, circles). Set per scene in Script Editor (Visual + JSON). Example graph: `{"functions":["x^2-4"],"x_range":[-5,5],"y_range":[-6,6],"points":[[2,0]]}`. Needs the Manim engine; with the simple engine those scenes show text only. Axis numbers are drawn as Text (no LaTeX needed).
