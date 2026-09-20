from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.shared.dtos.page_params_dto import PageParams

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PageParamsDep = Annotated[PageParams, Depends()]
