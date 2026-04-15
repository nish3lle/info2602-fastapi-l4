from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.database import SessionDep
from app.models import *
from app.auth import AuthDep
from fastapi import status

todo_router = APIRouter(tags=["Todo Management"])


@todo_router.get('/todos', response_model=list[TodoResponse])
def get_todos(db: SessionDep, user: AuthDep):
    return user.todos


@todo_router.get('/todo/{id}', response_model=TodoResponse)
def get_todo_by_id(id: int, db: SessionDep, user: AuthDep):
    todo = db.exec(select(Todo).where(Todo.id == id, Todo.user_id == user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return todo


@todo_router.post('/todos', response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(db: SessionDep, user: AuthDep, todo_data: TodoCreate):
    todo = Todo(text=todo_data.text, user_id=user.id)
    try:
        db.add(todo)
        db.commit()
        db.refresh(todo)
        return todo
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while creating an item",
        )


@todo_router.put('/todo/{id}', response_model=TodoResponse)
def update_todo(id: int, db: SessionDep, user: AuthDep, todo_data: TodoUpdate):
    todo = db.exec(select(Todo).where(Todo.id == id, Todo.user_id == user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    if todo_data.text is not None:
        todo.text = todo_data.text
    if todo_data.done is not None:
        todo.done = todo_data.done
    try:
        db.add(todo)
        db.commit()
        db.refresh(todo)
        return todo
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while updating an item",
        )


@todo_router.delete('/todo/{id}', status_code=status.HTTP_200_OK)
def delete_todo(id: int, db: SessionDep, user: AuthDep):
    todo = db.exec(select(Todo).where(Todo.id == id, Todo.user_id == user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    try:
        db.delete(todo)
        db.commit()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while deleting an item",
        )


# Exercise 2 — Category management

@todo_router.post('/category', response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(db: SessionDep, user: AuthDep, category_data: CategoryCreate):
    category = Category(text=category_data.text, user_id=user.id)
    try:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while creating the category",
        )


@todo_router.post('/todo/{todo_id}/category/{cat_id}', response_model=TodoResponse)
def add_category_to_todo(todo_id: int, cat_id: int, db: SessionDep, user: AuthDep):
    todo = db.exec(select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id)).one_or_none()
    if not todo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    category = db.exec(select(Category).where(Category.id == cat_id, Category.user_id == user.id)).one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    already_linked = db.exec(
        select(TodoCategory).where(TodoCategory.todo_id == todo_id, TodoCategory.category_id == cat_id)
    ).one_or_none()
    if not already_linked:
        db.add(TodoCategory(todo_id=todo_id, category_id=cat_id))
        db.commit()
        db.refresh(todo)

    return todo


@todo_router.delete('/todo/{todo_id}/category/{cat_id}', response_model=TodoResponse)
def remove_category_from_todo(todo_id: int, cat_id: int, db: SessionDep, user: AuthDep):
    todo = db.exec(select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id)).one_or_none()
    if not todo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    link = db.exec(
        select(TodoCategory).where(TodoCategory.todo_id == todo_id, TodoCategory.category_id == cat_id)
    ).one_or_none()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not assigned to this todo")

    db.delete(link)
    db.commit()
    db.refresh(todo)
    return todo


@todo_router.get('/category/{cat_id}/todos', response_model=list[TodoResponse])
def get_todos_for_category(cat_id: int, db: SessionDep, user: AuthDep):
    category = db.exec(select(Category).where(Category.id == cat_id, Category.user_id == user.id)).one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    return [todo for todo in category.todos if todo.user_id == user.id]
