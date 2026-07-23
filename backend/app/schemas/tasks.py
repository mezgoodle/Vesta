from datetime import datetime
from pydantic import BaseModel, Field


class TaskItem(BaseModel):
    """Schema representing a single Google Task."""

    id: str = Field(..., description="Google Task ID")
    title: str = Field(..., description="Task title")
    notes: str | None = Field(None, description="Task notes or description")
    status: str = Field("needsAction", description="Task status: 'needsAction' or 'completed'")
    due: datetime | None = Field(None, description="Due date/time for the task")
    completed: datetime | None = Field(None, description="Completion timestamp if completed")
    updated: datetime | None = Field(None, description="Last update timestamp")


class TaskList(BaseModel):
    """Schema representing a Google Task List."""

    id: str = Field(..., description="Task list ID")
    title: str = Field(..., description="Task list title")
    updated: datetime | None = Field(None, description="Last update timestamp")


class TaskCreate(BaseModel):
    """Schema for creating a new Google Task."""

    title: str = Field(..., description="Task title")
    notes: str | None = Field(None, description="Task notes or description")
    due: datetime | None = Field(None, description="Due date/time for the task")
    tasklist_id: str = Field("@default", description="ID of the target task list")


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""

    title: str | None = Field(None, description="Updated task title")
    notes: str | None = Field(None, description="Updated task notes")
    due: datetime | None = Field(None, description="Updated due date/time")
    status: str | None = Field(None, description="Updated status: 'needsAction' or 'completed'")


class TasksResponse(BaseModel):
    """Schema for returning a list of tasks."""

    tasks: list[TaskItem] = Field(..., description="List of tasks")
    count: int = Field(..., description="Number of tasks returned")
