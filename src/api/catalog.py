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
        # amntRPotions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).first()[0]
        amntGPotions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).first()[0]
        # amntBPotions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).first()[0]

    
    return [
            {
                "sku": "GREEN_POTION_1",
                "name": "green potion",
                "quantity": amntGPotions,
                "price": 45,
                "potion_type": [0, 100, 0, 0],
            }
        ]
