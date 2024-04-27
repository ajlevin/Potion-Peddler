from fastapi import APIRouter, Depends, Request
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("TRUNCATE TABLE global_ledger"))
        connection.execute(sqlalchemy.text("TRUNCATE TABLE cart_items"))
        connection.execute(sqlalchemy.text("TRUNCATE TABLE carts"))
        connection.execute(sqlalchemy.text("TRUNCATE TABLE potion_ledger"))
        
        connection.execute(sqlalchemy.text(
            "INSERT INTO global_ledger (gold_difference, order_type) VALUES (:totalCost, :order_type)"), 
            [{"totalCost": 100,
              "order_type": "reset"}])


    return "OK"
