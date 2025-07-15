from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select


class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: Optional[int] = None


hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
hero_3 = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=48)


print("Writing data to db ... START")
engine_write = create_engine("sqlite:///database.db")
SQLModel.metadata.create_all(engine_write)

with Session(engine_write) as session:
    session.add(hero_1)
    session.add(hero_2)
    session.add(hero_3)
    session.commit()

print("Writing data to db ... COMPLETE")


print("Reading data from db ... START")
engine_read = create_engine("sqlite:///database.db")

with Session(engine_read) as session:
    statement = select(Hero).where(Hero.name == "Spider-Boy")
    hero = session.exec(statement).first()
    print(f"Object is: {hero}")
    print(f"Object dictionary keys are: {list(hero.__dict__.keys())}")
    print(f"Object key type is: {type(hero.secret_name)}")

print("Reading data from db ... COMPLETE")
