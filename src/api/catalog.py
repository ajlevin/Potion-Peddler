from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    lst = []

    with db.engine.begin() as connection:
        
            potionsData = connection.execute(sqlalchemy.text(f"SELECT * FROM potions"))
            for potion in potionsData
                if potion.inventory > 0:
                    lst.append({
                        "sku": potion.item_sku,
                        "name": potion.item_sku + " POTION",
                        "quantity": potion.inventory,
                        "price": potion.price,
                        "potion_type": [potion.red, potion.green, potion.blue, potion.dark],
                    })
    
    return lst
