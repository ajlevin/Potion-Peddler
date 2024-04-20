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
    
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            potionData = connection.execute(sqlalchemy.txt(f"SELECT * FROM potions \
                                                WHERE red_ml = {potion.potion_type[0]} \
                                                AND green_ml = {potion.potion_type[1]} \
                                                AND blue_ml = {potion.potion_type[2]} \
                                                AND dark_ml = {potion.potion_type[3]}")).first()
            
            connection.execute(sqlalchemy.txt(f"UPDATE potions SET quantity = quantity + {potion.quantity} WHERE item_sku = {potionData.item_sku}"))
            connection.execute(sqlalchemy.txt(f"UPDATE global_inventory SET gold = gold + {potion.quantity * potionData.price}"))
    
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, green, blue, and
    # dark potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    lst = [] # needs fixing -- only does mono potions

    with db.engine.begin() as connection:
        curRml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).first()[0]
        curGml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).first()[0]
        curBml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).first()[0]
        curDml = connection.execute(sqlalchemy.text("SELECT num_dark_ml FROM global_inventory")).first()[0]

    rPAmount = int(curRml / 100)
    if rPAmount > 0:
        lst.append({
                "potion_type": [100, 0, 0, 0],
                "quantity": rPAmount,
            })
    gPAmount = int(curGml / 100)
    if gPAmount > 0:
        lst.append({
                "potion_type": [0, 100, 0, 0],
                "quantity": gPAmount,
            })
    bPAmount = int(curBml / 100)
    if bPAmount > 0:
        lst.append({
                "potion_type": [0, 0, 100, 0],
                "quantity": bPAmount,
            })
    dPAmount = int(curDml / 100)
    if dPAmount > 0:
        lst.append({
                "potion_type": [0, 0, 0, 100],
                "quantity": dPAmount,
            })

    return lst

if __name__ == "__main__":
    print(get_bottle_plan())
