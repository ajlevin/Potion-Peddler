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
        for barrel_delivered in barrels_delivered:
            gold_paid += barrel_delivered.price * barrel_delivered.quantity
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
        
        print(f"gold_paid: {gold_paid} red_ml: {red_ml} blue_ml: {blue_ml} green_ml: {green_ml} dark_ml: {dark_ml}")

        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET 
                num_red_ml = num_red_ml + :red_ml, 
                num_green_ml = num_green_ml + :green_ml, 
                num_blue_ml = num_blue_ml + :blue_ml, 
                num_dark_ml = num_dark_ml + :dark_ml, 
                gold = gold - :gold_paid
                """), 
            [{"red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml, "gold_paid": gold_paid}])
    
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
    

    with db.engine.begin() as connection:
        curGold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first()[0]
        potionsData = connection.execute(sqlalchemy.text("SELECT * FROM potions"))
        for potion in potionsData:
            if potion.inventory == 0:
                mlAsk['red'] += potion.red_ml
                mlAsk['green'] += potion.green_ml
                mlAsk['blue'] += potion.blue_ml
                mlAsk['dark'] += potion.dark_ml
        mlAsk = dict(sorted(mlAsk.items(), key=lambda item: item[1]))

    for bType in mlAsk.keys():
        for sizedBarrel in barrelSplit.values():
            if sizedBarrel[bType] is not None and (int(int(curGold / 4) / sizedBarrel[bType].price) > 0):
                lst.append(
                    {
                        "sku": sizedBarrel[bType].sku,
                        "quantity": min(int(int(curGold / 4) / sizedBarrel[bType].price), sizedBarrel[bType].quantity),
                    }
                )
                break
        
    return lst
