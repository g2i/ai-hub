import os
from pydantic import BaseModel, EmailStr, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic.root_model import RootModel

class Link(BaseModel):
    href: HttpUrl


class Links(BaseModel):
    candidate: Link
    assessment: Link
    invitation: Link


class EventPayloadItem(BaseModel):
    candidateId: str
    candidateExternalId: str
    assessmentId: str
    candidateEmail: EmailStr
    examId: str
    testId: str
    examName: str
    event: str
    _links: Links


class EventPayload(RootModel[List[EventPayloadItem]]):
    pass


class Score(BaseModel):
    scoredPoints: Optional[int] = None
    maxPoints: int
    percentage: Optional[float] = None


class TestInfo(BaseModel):
    id: str
    name: str
    _links: Dict[str, Link]


class AssessmentLinks(BaseModel):
    candidateAccess: Link
    onlineReport: Link
    pdfReport: Link
    candidateUrl: Link
    self: Link


class Comment(BaseModel):
    filename: str
    rating: str
    startLine: int
    endLine: int
    text: str


class AnswerValue(BaseModel):
    choices: List[Any] = []
    text: Optional[str] = None
    gaps: List[Any] = []
    comments: Optional[List[Comment]] = None


class Answer(BaseModel):
    answerId: str
    taskId: Optional[str] = None
    title: str
    type: Optional[str] = None
    score: Optional[Score] = None
    difficulty: Optional[str] = None
    gitUrl: Optional[str] = None
    value: AnswerValue


class Section(BaseModel):
    timeTakenInSeconds: int
    timeLimitInSeconds: int
    score: Score
    answers: List[Answer]


class Assessment(BaseModel):
    id: str
    status: str
    timeTakenInSeconds: int
    timeLimitInSeconds: int
    score: Score
    skills: List[Any] = []
    sections: List[Section]
    token: str
    creationDate: datetime
    startDate: datetime
    finishDate: datetime
    expirationDate: Optional[datetime] = None
    _embedded: Dict[str, Any]
    _links: AssessmentLinks


class DevSkillerResponse(BaseModel):
    payload: EventPayload
    assessment: Assessment