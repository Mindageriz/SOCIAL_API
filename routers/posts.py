from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from models import Post, User
from schemas import PostCreate, PostUpdate, PostOut, PostWithOwner
from auth import get_current_user

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=list[PostWithOwner])
async def list_posts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).options(selectinload(Post.owner)).order_by(Post.created_at.desc()))
    return result.scalars().all()


@router.get("/{post_id}", response_model=PostWithOwner)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Post).options(selectinload(Post.owner)).where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    payload: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = Post(title=payload.title, content=payload.content, owner_id=current_user.id)
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


@router.put("/{post_id}", response_model=PostOut)
async def update_post(
    post_id: int,
    payload: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to edit this post")

    if payload.title is not None:
        post.title = payload.title
    if payload.content is not None:
        post.content = payload.content

    await db.commit()
    await db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this post")

    await db.delete(post)
    await db.commit()
