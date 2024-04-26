from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    numTotalPotions = 0
    with db.engine.begin() as connection:
        potionTypes = connection.execute(sqlalchemy.text(
            """
            SELECT potion_id, SUM(inventory_change) AS inventory FROM potion_ledger GROUP BY potion_id
            """))
        for potion in potionTypes:
            numTotalPotions += potion.inventory
        
        curGold = connection.execute(sqlalchemy.text("SELECT SUM(gold_difference) FROM global_ledger")).first()[0]
        curmls = connection.execute(sqlalchemy.text(
            """
            SELECT 
            SUM(red_difference) as red_ml, 
            SUM(green_difference) as green_ml,
            SUM(blue_difference) as blue_ml,
            SUM(dark_difference) as dark_ml 
            FROM global_ledger
            """)).first()
        
        numTotalml = curmls.red_ml + curmls.green_ml + curmls.blue_ml + curmls.dark_ml

    return {"number_of_potions": numTotalPotions, "ml_in_barrels": numTotalml, "gold": curGold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        curGold = connection.execute(sqlalchemy.text("SELECT SUM(gold_difference) FROM global_ledger")).first()[0]
        
        curmls = connection.execute(sqlalchemy.text(
            """
            SELECT 
            SUM(red_difference) as red_ml, 
            SUM(green_difference) as green_ml,
            SUM(blue_difference) as blue_ml,
            SUM(dark_difference) as dark_ml 
            FROM global_ledger
            """)).first()
        totalmlCount = curmls.red_ml + curmls.green_ml + curmls.blue_ml + curmls.dark_ml
        
        totalPotionCount = 0
        potionTypes = connection.execute(sqlalchemy.text(
            """
            SELECT potion_id, SUM(inventory_change) AS inventory FROM potion_ledger GROUP BY potion_id
            """))
        for potion in potionTypes:
            totalPotionCount += potion.inventory

        availableGold = max(curGold - 3800, 0)
        pCap = 0
        mlCap = 0
        valsToRun = True
        while availableGold >= 1000 and valsToRun:
            valsToRun = False
            if totalPotionCount >= 40:
                pCap += 1
                availableGold -= 1000
                valsToRun = True
            
            if availableGold < 1000:
                break

            if totalmlCount >= 9000:
                mlCap += 1
                availableGold -= 1000
                valsToRun = True
            
    return {
        "potion_capacity": pCap,
        "ml_capacity": mlCap,
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    with db.engine.begin() as connection:
        goldSpent = (capacity_purchase.ml_capacity + capacity_purchase.potion_capacity) * 1000
        connection.execute(sqlalchemy.text(
            """
            INSERT INTO global_ledger (gold_difference, potion_capacity, ml_capacity, order_id, order_type) 
            VALUES (:gold_difference, :potion_capacity, :ml_capacity, :order_id, :order_type)
            """),
            [{"gold_difference": -goldSpent,
              "potion_capacity": capacity_purchase.potion_capacity * 50,
              "ml_capacity": capacity_purchase.ml_capacity * 10000,
              "order_id": order_id,
              "order_type": "capacity delivery"}])
    
    return "OK"
