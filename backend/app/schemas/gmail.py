from pydantic import BaseModel, Field


class EmailMessage(BaseModel):
    """Schema representing a single email message."""

    id: str = Field(..., description="The unique ID of the email message")
    sender: str = Field(..., description="The sender's name and/or email address")
    subject: str = Field(..., description="The subject line of the email")
    date: str = Field(..., description="The date/time the email was received")
    snippet: str = Field(
        ..., description="A short snippet/preview of the email content"
    )
    body: str = Field(
        ..., description="The parsed and truncated body text of the email"
    )


class EmailMessageList(BaseModel):
    """Schema representing a list of email messages."""

    emails: list[EmailMessage] = Field(..., description="List of email messages")
    count: int = Field(..., description="Number of emails in the list")
