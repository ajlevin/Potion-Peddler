from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    with db.engine.begin() as connection:
        data = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
    
    return [
            {
                "sku": "GREEN_POTION_1",
                "name": "green potion",
                "quantity": 1,
                "price": 48,
                "potion_type": [0, 100, 0, 0],
            }
        ]
