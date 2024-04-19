from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    potionTypes = ["RED", "ORANGE", "YELLOW", "GREEN", "BLUE", "PURPLE", "DARK"]
    lst = []

    with db.engine.begin() as connection:
        
        for pt in potionTypes:
            potionData = connection.execute(sqlalchemy.text(f"SELECT * FROM potions WHERE item_sku = {pt}"))
            if potionData.inventory > 0:
                lst.append({
                    "sku": potionData.item_sku,
                    "name": potionData.item_sku + " POTION",
                    "quantity": potionData.inventory,
                    "price": potionData.price,
                    "potion_type": [potionData.red, potionData.green, potionData.blue, potionData.dark],
                })
    
    return lst
