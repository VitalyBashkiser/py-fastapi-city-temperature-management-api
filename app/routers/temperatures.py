import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.dependencies import get_db
from datetime import datetime
import aiohttp

router = APIRouter()

API_KEY = "844066ec80254d2bada71850240207"


@router.post("/update", response_model=List[schemas.Temperature])
async def update_temperatures(
    db: Session = Depends(get_db),
) -> List[schemas.Temperature]:
    cities = crud.get_cities(db)
    temperatures = []
    async with aiohttp.ClientSession() as session:
        for city in cities:
            async with session.get(
                f"http://api.openweathermap.org/data/2.5/weather?q={city.name}"
                f"&appid={API_KEY}"
            ) as response:
                if response.status != 200:
                    logging.error(
                        f"Failed to fetch weather data for city: {city.name},"
                        f" status: {response.status}"
                    )
                    continue
                data = await response.json()
                logging.info(f"Received data for city {city.name}: {data}")

                if "main" not in data:
                    logging.error(
                        f"No 'main' key in response data for city: {city.name}"
                    )
                    continue

                temperature = data["main"]["temp"] - 273.15
                temp_record = schemas.TemperatureCreate(
                    city_id=city.id,
                    date_time=datetime.now(),
                    temperature=temperature,
                )
                temperatures.append(temp_record)
                crud.create_temperature(db=db, temperature=temp_record)

    return temperatures


@router.get("/", response_model=List[schemas.Temperature])
def read_temperatures(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> List[schemas.Temperature]:
    temperatures = crud.get_temperatures(db, skip=skip, limit=limit)
    return temperatures


@router.get("/by_city", response_model=List[schemas.Temperature])
def read_temperatures_by_city(
    city_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[schemas.Temperature]:
    temperatures = crud.get_temperatures_by_city(
        db, city_id=city_id, skip=skip, limit=limit
    )
    return temperatures
