from pydantic import BaseModel, Field

class ScriptReq(BaseModel):
    topic: str = Field(min_length=3, max_length=4000)
    level: str = "Grade 10-12"
    objective: str = ""
    minutes: int = Field(5, ge=1, le=20)
    difficulty: str = "medium"
    style: str = "step-by-step"
    language: str = "English"

class Scene(BaseModel):
    title: str = Field(max_length=200)
    math: list[str] = Field(default_factory=list, max_length=12)
    narration: str = Field(max_length=4000)
    checks: list[str] = Field(default_factory=list, max_length=20)
    kind: str = Field("steps", pattern="^(steps|graph|numberline|geometry)$")
    visual: dict = Field(default_factory=dict)

class Intro(BaseModel):
    enabled: bool = True
    name: str = "B. Hallison F. Thomas"
    title: str = "Mathematics Educator | Problem Solver | Mathematics Olympiad Trainer"
    script: str = ""

class VoiceSettings(BaseModel):
    stability: float = Field(0.5, ge=0, le=1)
    similarity: float = Field(0.8, ge=0, le=1)
    speed: float = Field(1.0, ge=0.7, le=1.2)

class RenderReq(BaseModel):
    title: str
    scenes: list[Scene] = Field(max_length=40)
    intro: Intro = Intro()
    voice: VoiceSettings = VoiceSettings()
    orientation: str = Field("landscape", pattern="^(landscape|portrait)$")
    engine: str = Field("simple", pattern="^(simple|manim)$")
    approved: bool = False
