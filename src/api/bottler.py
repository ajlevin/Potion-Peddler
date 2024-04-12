from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    typemlMap = {[100, 0, 0, 0] : "num_red_ml",
               [0, 100, 0, 0] : "num_green_ml",
               [0, 0, 100, 0] : "num_blue_ml"}
    typePMap = {[100, 0, 0, 0] : "num_red_potions",
               [0, 100, 0, 0] : "num_green_potions",
               [0, 0, 100, 0] : "num_blue_potions"}
    
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            connection.execute(sqlalchemy.text(
                f"UPDATE global_inventory SET {typePMap.get(potion.type)} = {typePMap.get(potion.type)} + ({max(potion.type)} / 100 * {potion.quantity})"))
            connection.execute(sqlalchemy.text(
                f"UPDATE global_inventory SET {typemlMap.get(potion.type)} = {typemlMap.get(potion.type)} - ({max(potion.type)} * {potion.quantity})"))
    
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, green, blue, and
    # dark potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    lst = []

    with db.engine.begin() as connection:
        curRml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).first()[0]
        curGml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).first()[0]
        curBml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).first()[0]

    rPAmount = int(curRml / 100)
    if rPAmount > 0:
        lst.append({
                "potion_type": [100, 0, 0, 0],
                "quantity": rPAmount,
            })
    gPAmount = int(curGml / 100)
    if rPAmount > 0:
        lst.append({
                "potion_type": [0, 100, 0, 0],
                "quantity": gPAmount,
            })
    bPAmount = int(curBml / 100)
    if rPAmount > 0:
        lst.append({
                "potion_type": [0, 0, 100, 0],
                "quantity": bPAmount,
            })

    return lst

if __name__ == "__main__":
    print(get_bottle_plan())
