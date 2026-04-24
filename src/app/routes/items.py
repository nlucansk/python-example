from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/items", tags=["items"])


class Item(BaseModel):
    name: str
    description: str = ""


class ItemResponse(Item):
    id: str


# In-memory store for demo purposes
_store: dict[str, ItemResponse] = {}
_counter: int = 0


@router.get("", response_model=list[ItemResponse])
async def list_items():
    return list(_store.values())


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: Item):
    global _counter
    _counter += 1
    item_id = str(_counter)
    record = ItemResponse(id=item_id, **item.model_dump())
    _store[item_id] = record
    return record


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    if item_id not in _store:
        raise HTTPException(status_code=404, detail="Item not found")
    return _store[item_id]


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: str):
    if item_id not in _store:
        raise HTTPException(status_code=404, detail="Item not found")
    del _store[item_id]
