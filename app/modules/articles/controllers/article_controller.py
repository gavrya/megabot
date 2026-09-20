from uuid import UUID

from fastapi import APIRouter, status

from app.modules.articles.dependencies import ArticleServiceDep
from app.modules.articles.dtos.article_create_dto import ArticleCreateDTO
from app.modules.articles.dtos.article_response_dto import ArticleResponseDTO
from app.modules.articles.dtos.article_update_dto import ArticleUpdateDTO
from app.shared.dependencies import PageParamsDep
from app.shared.dtos.page_dto import Page

router = APIRouter()


@router.get("", response_model=Page[ArticleResponseDTO])
async def list_articles(service: ArticleServiceDep, params: PageParamsDep) -> Page:
    return await service.list(params)


@router.get("/{article_id}", response_model=ArticleResponseDTO)
async def get_article(article_id: UUID, service: ArticleServiceDep) -> ArticleResponseDTO:
    return await service.get(article_id)


@router.post("", response_model=ArticleResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_article(
    payload: ArticleCreateDTO, service: ArticleServiceDep
) -> ArticleResponseDTO:
    return await service.create(payload)


@router.put("/{article_id}", response_model=ArticleResponseDTO)
async def update_article(
    article_id: UUID, payload: ArticleUpdateDTO, service: ArticleServiceDep
) -> ArticleResponseDTO:
    return await service.update(article_id, payload)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(article_id: UUID, service: ArticleServiceDep) -> None:
    await service.delete(article_id)
