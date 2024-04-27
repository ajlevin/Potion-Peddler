from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
        red_ml = 0
        green_ml = 0
        blue_ml = 0
        dark_ml = 0
        gold = 0

        for barrel_delivered in barrels_delivered:
            gold -= barrel_delivered.price * barrel_delivered.quantity
            if barrel_delivered.potion_type == [1,0,0,0]:
                red_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
            elif barrel_delivered.potion_type == [0,1,0,0]:
                green_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
            elif barrel_delivered.potion_type == [0,0,1,0]:
                blue_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
            elif barrel_delivered.potion_type == [0,0,0,1]:
                dark_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
            else:
                raise Exception("Invalid potion type")
                
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO global_ledger
                (gold_difference, red_difference, green_difference, blue_difference, dark_difference, order_id, order_type)
                VALUES (:gold, :red_ml, :green_ml, :blue_ml, :dark_ml, :order_id, :order_type)
                """), 
            [{  "gold": gold,
                "red_ml": red_ml, 
                "green_ml": green_ml, 
                "blue_ml": blue_ml, 
                "dark_ml": dark_ml,
                "order_id": order_id,
                "order_type": "barreling"}])
    
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """

    lst = []
    barrelTemp = {
        'red' : None,
        'green' : None,
        'blue' : None,
        'dark' : None}
    barrelSplit = {
        'large' : barrelTemp.copy(),
        'medium' : barrelTemp.copy(),
        'small' : barrelTemp.copy(),
        'mini' : barrelTemp.copy()
    }
    mlAsk = {
        'red' : 0,
        'green' : 0,
        'blue' : 0,
        'dark' : 0
    }
    typeIdxs = list(mlAsk.keys())

    for barrel in wholesale_catalog:
        print(barrel, flush=True)
        if barrel.ml_per_barrel == 10000:
            barrelSplit['large'][typeIdxs[barrel.potion_type.index(max(barrel.potion_type))]] = barrel
        elif barrel.ml_per_barrel == 2500:
            barrelSplit['medium'][typeIdxs[barrel.potion_type.index(max(barrel.potion_type))]] = barrel
        elif barrel.ml_per_barrel == 500:
            barrelSplit['small'][typeIdxs[barrel.potion_type.index(max(barrel.potion_type))]] = barrel
        else:
            barrelSplit['mini'][typeIdxs[barrel.potion_type.index(max(barrel.potion_type))]] = barrel
    
    availableGold = 0
    with db.engine.begin() as connection:
        availableGold = connection.execute(sqlalchemy.text("SELECT SUM(gold_difference) FROM global_ledger")).first()[0]
        potionTypes = connection.execute(sqlalchemy.text(
            """
            SELECT potion_id, SUM(inventory_change) AS inventory FROM potion_ledger GROUP BY potion_id
            """))
        
        for potion in potionTypes:
            if potion.inventory <= 1:
                potionData = connection.execute(sqlalchemy.text("SELECT * from potions WHERE potion_id = :potion_id"),
                                            [{"potion_id": potion.potion_id}]).first()
                mlAsk['red'] += potionData.red_ml
                mlAsk['green'] += potionData.green_ml
                mlAsk['blue'] += potionData.blue_ml
                mlAsk['dark'] += potionData.dark_ml

        mlAsk = dict(sorted(mlAsk.items(), key=lambda item: item[1]))

    for bType in mlAsk.keys():
        for sizedBarrel in barrelSplit.values():
            
            # THIS NO WORK
            if sizedBarrel[bType] is not None and (int(availableGold / sizedBarrel[bType].price) > 0):
                # barrelQuantity = min(int(availableGold / sizedBarrel[bType].price), sizedBarrel[bType].quantity)
                lst.append(
                    {
                        "sku": sizedBarrel[bType].sku,
                        "quantity": 1,
                    }
                )
                availableGold -= sizedBarrel[bType].price
                break
        
    return lst
