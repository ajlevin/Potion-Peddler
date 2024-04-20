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
        potionsData = connection.execute(sqlalchemy.text("SELECT * FROM potions"))

        for potion in potionsData:
            if potion.quantity <= 2:
                if potion.red <= curRml and potion.green <= curGml and potion.blue <= curBml and potion.dark <= curDml:
                    lst.append({
                        "potion_type": [potion.red, potion.green, potion.blue, potion.dark],
                        "quantity": calculatePotionQuantity(potion, curRml, curGml, curBml, curDml),
                    })
    
    return lst

def calculatePotionQuantity(potion, curRml, curGml, curBml, curDml):
    redUsed = 999999999999
    greenUsed = 999999999999
    blueUsed = 999999999999
    darkUsed = 999999999999

    if potion.red > 0:
        redUsed = int((curRml / 2) / potion.red)
    if potion.green > 0:
        greenUsed = int((curGml / 2) / potion.green)
    if potion.blue > 0:
        blueUsed = int((curBml / 2) / potion.blue)
    if potion.dark > 0:
        darkUsed = int((curDml / 2) / potion.dark)
    
    return min(redUsed, greenUsed, blueUsed, darkUsed)

if __name__ == "__main__":
    print(get_bottle_plan())
