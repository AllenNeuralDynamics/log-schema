from pydantic import BaseModel


class LogConfigModel(BaseModel):
    app_name: str = "my_app"
    env: str = "production"
