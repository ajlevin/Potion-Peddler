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
    red_ml_spent = 0
    green_ml_spent = 0
    blue_ml_spent = 0
    dark_ml_spent = 0

    with db.engine.begin() as connection:
        for potion in potions_delivered:
            red_ml_spent += potion.potion_type[0] * potion.quantity
            green_ml_spent += potion.potion_type[1] * potion.quantity
            blue_ml_spent += potion.potion_type[2] * potion.quantity
            dark_ml_spent += potion.potion_type[3] * potion.quantity
            connection.execute(sqlalchemy.text(
                "UPDATE potions SET inventory = inventory + :potion_quantity \
                WHERE red_ml = :red_ml and green_ml = :green_ml and blue_ml = :blue_ml and dark_ml = :dark_ml"),
                [{"potion_quantity": potion.quantity, 
                  "red_ml": potion.potion_type[0], 
                  "green_ml": potion.potion_type[1],
                  "red_ml": potion.potion_type[2], 
                  "green_ml": potion.potion_type[3]}])
        
        print(f"red_ml: {red_ml_spent} green_ml: {green_ml_spent} blue _ml: {blue_ml_spent} dark_ml: {dark_ml_spent}")        
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET 
                num_red_ml = num_red_ml - :red_ml, 
                num_green_ml = num_green_ml - :green_ml, 
                num_blue_ml = num_blue_ml - :blue_ml, 
                num_dark_ml = num_dark_ml - :dark_ml, 
                """), 
            [{"red_ml": red_ml_spent, 
                "green_ml": green_ml_spent, 
                "blue_ml": blue_ml_spent, 
                "dark_ml": dark_ml_spent}])
    
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
        curRml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).first()[0]
        curGml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).first()[0]
        curBml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).first()[0]
        curDml = connection.execute(sqlalchemy.text("SELECT num_dark_ml FROM global_inventory")).first()[0]
        potionsData = connection.execute(sqlalchemy.text("SELECT * FROM potions"))

        availableRml = curRml
        availableGml = curGml
        availableBml = curBml
        availableDml = curDml
        for potion in potionsData:
            if potion.inventory <= 2:
                if potion.red_ml <= availableRml and potion.green_ml <= availableGml \
                and potion.blue_ml <= availableBml and potion.dark_ml <= availableDml:
                    brewQuantity = calculatePotionQuantity(potion, availableRml, availableGml, availableBml, availableDml)
                    lst.append({
                        "potion_type": [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml],
                        "quantity": brewQuantity,
                    })
                    availableRml = potion.red_ml * brewQuantity
                    availableGml = potion.green_ml * brewQuantity
                    availableBml = potion.blue_ml * brewQuantity
                    availableDml = potion.dark_ml * brewQuantity
                    
    
    return lst

def calculatePotionQuantity(potion, availableRml, availableGml, availableBml, availableDml):
    redUsed = 999999999999
    greenUsed = 999999999999
    blueUsed = 999999999999
    darkUsed = 999999999999

    if potion.red_ml > 0:
        redUsed = int((availableRml / 2) / potion.red_ml)
    if potion.green_ml > 0:
        greenUsed = int((availableGml / 2) / potion.green_ml)
    if potion.blue_ml > 0:
        blueUsed = int((availableBml / 2) / potion.blue_ml)
    if potion.dark_ml > 0:
        darkUsed = int((availableDml / 2) / potion.dark_ml)
    
    return min(redUsed, greenUsed, blueUsed, darkUsed)

if __name__ == "__main__":
    print(get_bottle_plan())
