from pydantic import BaseModel


class DepartmentResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
