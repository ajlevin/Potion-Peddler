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
        potionTypes = connection.execute(sqlalchemy.text(
            """
            SELECT potion_id, SUM(inventory_change) AS inventory FROM potion_ledger GROUP BY potion_id
            """))
        for potion in potionTypes:
            potionData = connection.execute(sqlalchemy.text("SELECT * from potions WHERE potion_id = :potion_id"),
                                            [{"potion_id": potion.potion_id}]).first()
            if potion.inventory > 0:
                lst.append({
                    "sku": potionData.item_sku,
                    "name": potionData.item_sku + " POTION",
                    "quantity": potion.inventory,
                    "price": potionData.price,
                    "potion_type": [potionData.red_ml, potionData.green_ml, potionData.blue_ml, potionData.dark_ml],
                })
    
    return lst
