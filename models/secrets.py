from pydantic import BaseModel

from database.models import AccessStatus


class ChangeStatusRequest(BaseModel):
    request_id: int
    new_status: AccessStatus
    response_message: str = None