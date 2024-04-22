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
        potionsData = connection.execute(sqlalchemy.text("SELECT * FROM potions"))
        for potion in potionsData:
            numTotalPotions += potion.inventory
        
        numRml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).first()[0]
        numGml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).first()[0]
        numBml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).first()[0]
        numGold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first()[0]

    numTotalml = numRml + numGml + numBml

    return {"number_of_potions": numTotalPotions, "ml_in_barrels": numTotalml, "gold": numGold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        curGold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first()[0]
        
        mlData = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        totalmlCount = mlData.num_red_ml + mlData.num_green_ml + mlData.num_blue_ml + mlData.num_dark_ml
        
        totalPotionCount = 0
        potionsData = connection.execute(sqlalchemy.text("SELECT * FROM potions"))
        for potion in potionsData:
            totalPotionCount += potion.inventory

        availableGold = min(curGold - 800, 0)
        pCap = 0
        mlCap = 0
        while availableGold >= 1000:
            if totalPotionCount >= 40:
                pCap += 1
                availableGold -= 1000
            
            if availableGold < 1000:
                break

            if totalmlCount >= 9000:
                mlCap += 1
                availableGold -= 1000
            
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
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET potion_capacity = potion_capacity + {capacity_purchase.potion_capacity * 50}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET ml_capacity = ml_capacity + {capacity_purchase.ml_capacity * 10000}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {goldSpent}"))
    
    return "OK"
