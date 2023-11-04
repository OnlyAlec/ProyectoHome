import oracledb
import os
from dotenv import load_dotenv

load_dotenv()


class DB:
    def __init__(self):
        self.allTables = []
        self.connection: oracledb.Connection = None
        self.cursor: oracledb.Cursor = None
        self.connect()
        self.getAllTables()

    def connect(self):
        if self.connection is not None:
            print("\t -> Already Connect!")
            return False

        print("Connecting to SQL...", end=" ")
        ip = os.getenv("DB_IP")
        pwd: str = os.getenv("DB_PASSWORD")
        userDB: str = os.getenv("DB_USER")

        try:
            self.connection: oracledb.Connection = oracledb.connect(
                user=userDB,
                password=pwd,
                dsn=f"{ip}/xepdb1")
            print("OK!")
            self.cursor = self.connection.cursor()
            return True
        except oracledb.DatabaseError as e:
            print(f"Failed! -> \t {e}")
            return False

    def getAllTables(self):
        self.cursor.execute("SELECT table_name FROM user_tables")
        self.allTables = [
            table[0] for table in self.cursor.fetchall()
        ]

    def columnsUpper(self, data: dict):
        for table in data.copy():
            data[table.upper()] = data.pop(table)

    def respondError(self, e):
        return {
            "status": "error",
            "message": e
        }


class Operation:
    def __init__(self, dbDest: DB, crud, data: dict):
        self.db = dbDest
        self.crud = crud
        self.tables = data
        self.order = {}
        self.execute()

    def execute(self):
        e = self.validation(self.tables)
        if e is not True:
            return self.db.respondError(e)
        getattr(self, self.crud.lower())()

    def validation(self, data: dict):
        self.db.columnsUpper(data)
        # Valida si existen las tablas y columnas
        for table in data:
            if not table in self.db.allTables:
                e = f"Table {table} not exist!"
                return e

            for column in data[table]:
                if not self.existColumn(table, column):
                    e = f"Column {column} not exist!"
                    return e
        # Ordena las tablas para insertar primero en las tablas hijas
        self.orderTables(self.tables)
        # Verifica si los datos recibidos sirven para insertar o existen en la db
        lastTableInsert = ""
        for table in self.order.items():
            if lastTableInsert == table[0]:
                continue
            for child in table[1]:
                if self.tables[table[0]][child] is None:
                    if child.split("_")[1].upper() not in self.tables:
                        print(f"Data for table {child} is required!")
                        return False
                    childName = child.split("_")[1].upper()
                    dictData = {childName: self.tables[childName]}
                    try:
                        Operation(self.db, self.crud, dictData)
                        self.tables[table[0]][child] = self.recoverLastID(
                            childName)
                        self.tables.pop(childName)
                        lastTableInsert = childName
                    except oracledb.DatabaseError as e:
                        print(e)
                        return e
        return True

    def existColumn(self, table: str, column: str):
        try:
            self.db.cursor.execute(
                f"SELECT {column} FROM {table} WHERE 1=2")
            return True
        except oracledb.DatabaseError:
            return False

    def orderTables(self, data: dict):
        for table in data.keys():
            tablesChild = []
            for column in data[table]:
                if column.find("cve_") != -1 and column.find("tipo") == -1:
                    tablesChild.append(column)
            self.order[table] = tablesChild

    def recoverLastID(self, table: str):
        self.db.cursor.execute(
            f"SELECT MAX(ID_{table}) FROM {table}")
        return self.db.cursor.fetchone()[0]

    def insert(self):
        for table in self.tables:
            query = f"INSERT INTO {table} VALUES ("
            for values in self.tables[table].values():
                if isinstance(values, str):
                    query += f"'{values}', "
                elif isinstance(values, int):
                    query += f"{values}, "
            query = query[:-2] + ")"
            try:
                print("Inserting...", end=" ")
                self.db.cursor.execute(query)
                self.db.connection.commit()
                print("OK!")
            except oracledb.DatabaseError as e:
                raise e

#   def update(self):

#   def delete(self):

#   def select(self):


# def getData(request: flask.Request):
#   data = request.get_json()
#   if

if __name__ == "__main__":
    dbSQL = DB()
    entry = {
        "Persona": {
            "edad": 20,
            "correo": "linbeck@outlook.es",
            "ID_persona": 1,
            "cve_nombre": None,
            "cve_rol": 1,
            "cve_casa": 1,
        },
        "Nombre": {
            "nombre": "Alexis",
            "apellido_paterno": "Chacon",
            "apellido_materno": "Trujillo",
            "ID_Nombre": 1
        }
    }
    statusOperation = Operation(dbSQL, "INSERT", entry)
