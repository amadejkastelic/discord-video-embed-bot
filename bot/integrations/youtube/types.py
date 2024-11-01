import datetime

import pydantic
import pydantic.alias_generators


class Likes(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        alias_generator=pydantic.alias_generators.to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: str
    date_created: datetime.datetime
    likes: int
    raw_dislikes: int
    raw_likes: int
    dislikes: int
    rating: float
    view_count: int
    deleted: bool
