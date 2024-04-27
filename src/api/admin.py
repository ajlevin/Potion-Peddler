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
        connection.execute(sqlalchemy.text("TRUNCATE TABLE global_ledger CASCADE"))
        connection.execute(sqlalchemy.text("TRUNCATE TABLE cart_items CASCADE"))
        connection.execute(sqlalchemy.text("TRUNCATE TABLE carts CASCADE"))
        connection.execute(sqlalchemy.text("TRUNCATE TABLE potion_ledger CASCADE"))
        
        connection.execute(sqlalchemy.text(
            """
            INSERT INTO global_ledger (gold_difference, order_type, potion_capacity, ml_capacity) 
            VALUES (:totalCost, :order_type, :potion_capacity, :ml_capacity)
            """), 
            [{"totalCost": 100,
              "order_type": "reset",
              "potion_capacity": 50,
              "ml_capacity": 10000}])


    return "OK"
