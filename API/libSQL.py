"""Librerias."""
import os
import json
import oracledb
from dotenv import load_dotenv
load_dotenv()


class Table:
    """
    Clase utilizada para construir consultas SQL a partir de datos en formato JSON o una cadena de texto.

    Args:
        jsonData (dict | str): Un diccionario JSON o una cadena de texto.
        table (str, optional): Nombre de la tabla. Defaults to "".
        query (str, optional): Consulta SQL. Defaults to "".

    Attributes:
        table (str | list): Nombre de la tabla o lista de nombres de tablas.
        alias (list): Lista de alias de las tablas.
        columns (list): Lista de nombres de columnas.
        values (list): Lista de valores.
        where (str): Condición WHERE de la consulta SQL.
        query (str): Consulta SQL.

    Methods:
        __init__(self, jsonData: dict | str, table: str = "", query: str = ""):
            Constructor de la clase. Recibe un diccionario JSON o una cadena de texto como entrada y construye la consulta SQL correspondiente.

        construct(self, jsonData: dict):
            Método interno utilizado por el constructor para construir la consulta SQL a partir del diccionario JSON.

        toUpper(self):
            Convierte los nombres de las tablas y columnas a mayúsculas.

        strValues(self):
            Retorna la representación en cadena de los valores.
    """

    def __init__(self, jsonData: dict | str, table: str = "", query: str = ""):
        self.table: str | list = table
        self.alias: list = []
        self.columns: list = []
        self.values: list = []
        self.where: str = ""
        self.query: str = query
        if not query:
            if isinstance(jsonData, str):
                self.query = jsonData
            else:
                self.construct(jsonData)

    def construct(self, jsonData: dict):
        """
        Método interno utilizado por el constructor para construir la consulta SQL a partir del diccionario JSON.

        Args:
            jsonData (dict): Un diccionario JSON.
        """
        for column, value in jsonData.items():
            if column == "alias":
                self.alias = value
            elif column == "where":
                campo: str = value.split("=")[0].strip()
                cond: str = value.split("=")[1].strip()
                self.where = f"{campo}='{cond}'"
            elif column == "query":
                table = Table(self.table, value)
            else:
                if column == "null":
                    self.columns.append(None)
                else:
                    self.columns.append(column)
                self.values.append(value)

    def toUpper(self):
        """
        Convierte los nombres de las tablas y columnas a mayúsculas.
        """
        self.table = [table.upper() for table in self.table] if isinstance(
            self.table, list) else self.table.upper()
        self.columns = [column.upper() for column in self.columns] if isinstance(
            self.columns, list) else self.columns.upper()

    def strValues(self) -> str:
        """
        Retorna la representación en cadena de los valores.

        Returns:
            str: Representación en cadena de los valores.
        """
        return ", ".join(self.values)


class DB:
    """
    Clase para interactuar con una base de datos Oracle.

    Attributes:
        allTables (list): Lista de tablas de la base de datos.
        connection (oracledb.Connection): Conexión con la base de datos.
        cursor (oracledb.Cursor): Cursor de la conexión.

    Methods:
        __init__():
            Constructor de la clase que establece una conexión con la base de datos y obtiene todas las tablas.
        connect():
            Establece una conexión con la base de datos.
        getAllTables():
            Obtiene todas las tablas de la base de datos.
        existColumn(table, column):
            Verifica si una columna existe en una tabla específica.
    """

    def __init__(self):
        self.allTables = []
        self.connection: oracledb.Connection = None
        self.cursor: oracledb.Cursor = None

        try:
            self.connect()
            self.getAllTables()
        except Exception as e:
            raise e

    def connect(self) -> bool | Exception:
        """
        Establece una conexión con la base de datos utilizando las credenciales proporcionadas en variables de entorno.

        Returns:
            bool | Exception : `True` si la conexión es exitosa de lo contrario lanza una excepción.
        """
        if self.connection is not None:
            print("\t -> ¡Ya está conectado!")
            return False

        print("Conectando a SQL...", end=" ")
        ip = os.getenv("DB_IP")
        pwd = os.getenv("DB_PASSWORD")
        userDB = os.getenv("DB_USER")

        try:
            self.connection: oracledb.Connection = oracledb.connect(
                user=str(userDB),
                password=str(pwd),
                dsn=f"{ip}/xepdb1")
            print("¡Conexión exitosa!")
            self.cursor = self.connection.cursor()
            return True
        except (oracledb.DatabaseError, oracledb.OperationalError) as e:
            print(f"¡Falló la conexión! -> \t {e}")
            raise e

    def getAllTables(self):
        """
        Ejecuta consultas SQL para obtener todas las tablas y vistas de la base de datos.
        Almacena los resultados en la variable `allTables`.
        """
        self.cursor.execute(
            "SELECT TABLE_NAME FROM all_tables WHERE OWNER = 'SOFIDBA_02'")
        self.allTables = [
            table[0] for table in self.cursor.fetchall()
        ]
        self.cursor.execute(
            "SELECT VIEW_NAME FROM ALL_VIEWS WHERE OWNER = 'SOFIDBA_02'")
        for table in self.cursor.fetchall():
            self.allTables.append(table[0])

    def existColumn(self, table: str, column: str) -> bool:
        """
        Verifica si una columna existe en una tabla específica.

        Args:
            table (str): Nombre de la tabla.
            column (str): Nombre de la columna.

        Returns:
            bool: Resultado de la verificación.
        """
        try:
            self.cursor.execute(
                f"SELECT {column} FROM {table} WHERE 1=2")
            return True
        except oracledb.DatabaseError:
            return False


class Operation:
    """
    Clase responsable de ejecutar las operaciones CRUD en la base de datos.

    Args:
        `dbDest` (DB): Base de datos de destino.
        `crud` (str): Tipo de operación CRUD.
        `data` (dict): Datos a utilizar en la operación.

    Attributes:
        db (DB): Base de datos de destino.
        crud (str): Tipo de operación CRUD.
        data (dict): Datos a utilizar en la operación.
        tablesWaiting (list): Lista de tablas a utilizar en la operación.
        tablesObj (list): Lista de objetos `Table` a utilizar en la operación.
        response (list | dict): Respuesta de la operación.

    Methods:
        __init__(self, dbDest: DB, crud: str, data: dict):
            Constructor de la clase. Recibe una base de datos, el tipo de operación CRUD y los datos a utilizar en la operación.
        checkObligatory(self):
            Verifica que los datos obligatorios estén presentes en los datos proporcionados.
        parseJSON(self, data):
            Convierte los datos en formato JSON a un diccionario.
        getTables(self):
            Obtiene las tablas de la base de datos a partir de los datos proporcionados.
        orderTables(self, table: str):
            Ordena las tablas de acuerdo a las dependencias entre ellas.
        execute(self):
            Ejecuta la operación CRUD.
        checkValidation(self, tableClass: Table):
            Verifica que las tablas y columnas proporcionadas existan en la base de datos.
        getIDChild(self, nameColumn: str):
            Obtiene el ID de la tabla hija.
        insert(self, table: Table):
            Ejecuta la operación INSERT.
        update(self, table: Table):
            Ejecuta la operación UPDATE.
        delete(self, table: Table):
            Ejecuta la operación DELETE.
    """

    def __init__(self, dbDest: DB, crud: str, data: dict):
        self.db = dbDest
        self.crud = crud
        self.data = data
        self.tablesWaiting: list = []
        self.tablesObj: list = []
        self.response: list | dict = []

        try:
            self.getTables()
            if miss := self.checkObligatory():
                raise ValueError(
                    f"Missing {', '.join(miss)} in {', '.join(miss.keys())}!")
            self.execute()
        except Exception as e:
            raise e

    def checkObligatory(self):
        """
        Verifica que los datos obligatorios estén presentes en los datos proporcionados.
        """

        miss = {}
        if self.crud == "SELECT":
            return False

        if self.crud == "INSERT":
            need = ["table", "values"]
        elif self.crud == "UPDATE":
            need = ["table", "columns", "values", "where"]
        elif self.crud == "DELETE":
            need = ["table", "where"]
        else:
            raise ValueError("CRUD not found!")

        for table in self.tablesObj:
            miss.update({table: []})
            for field in need:
                if not field in vars(table) and (field is None or field == ""):
                    miss[table].append(field)
        return False if len(miss) > 0 else miss

    # ! Not used
    def parseJSON(self, data) -> dict:
        """
        Convierte los datos en formato JSON a un diccionario.

        Args:
            data (dict | str): Datos a convertir.

        Returns:
            dict: Diccionario con los datos.
        """
        if isinstance(data, str) and self.crud == "SELECT":
            return json.loads(data)
        if isinstance(data, dict):
            return data
        raise ValueError("Data is not valid!")

    def getTables(self):
        """
        Obtiene las tablas de la base de datos a partir de los datos proporcionados.
        """
        if isinstance(self.data, str):
            return

        for table, data in self.data.items():
            self.tablesWaiting.append(table.upper())
            self.tablesObj.append(Table(data, table.upper()))

    def orderTables(self, table: str):
        """
        Ordena las tablas de acuerdo a las dependencias entre ellas.

        Args:
            table (str): Nombre de la tabla.

        Raises:
            `ValueError`: Si una tabla o columna no existe en la base de datos.
        """

        order = False
        tableObject: Table = self.tablesObj[self.tablesWaiting.index(table)]
        for column in tableObject.columns:
            if column.find("CVE_") != -1:
                # and column.find("TIPO") == -1
                childName = column.split("_")[1]
                indexColumn = tableObject.columns.index(column)
                if tableObject.values[indexColumn] is not None:
                    continue

                if childName in self.tablesWaiting:
                    indexPos = self.tablesWaiting.index(table)
                    if self.tablesWaiting.index(childName) < indexPos:
                        continue
                    self.tablesWaiting.remove(childName)
                    self.tablesWaiting.insert(indexPos, childName)
                    order = True
                else:
                    raise ValueError(
                        f"Table {childName} not found in data to insert!")
        if order:
            newOrder = []
            for order in self.tablesWaiting:
                for i, obj in enumerate(self.tablesObj):
                    if obj.table == order:
                        newOrder.append(self.tablesObj[i])
                        self.tablesObj.pop(i)
                        break
            self.tablesObj = newOrder

    def execute(self):
        """	
        Ejecuta la operación CRUD.

        Raises:
            `oracledb.DatabaseError`: Error al ejecutar la operación en la base de datos.
            `ValueError`: Si una tabla o columna no existe en la base de datos.
        """

        responses = {}
        try:
            if self.crud == "SELECT" and isinstance(self.data, str):
                self.db.cursor.execute(self.data)
                self.response = self.db.cursor.fetchall()
                return

            for table in self.tablesWaiting:
                self.checkValidation(
                    self.tablesObj[self.tablesWaiting.index(table)])

            for table in self.tablesWaiting.copy():
                self.orderTables(table)

            for table in self.tablesObj:
                resp = getattr(self, self.crud.lower())(table)
                responses.update({table.table: resp})
            self.db.connection.commit()
            self.response = responses
        except (oracledb.DatabaseError, ValueError) as e:
            self.db.connection.rollback()
            raise e

    def checkValidation(self, tableClass: Table):
        """
        Verifica que las tablas y columnas proporcionadas existan en la base de datos.

        Args:
            tableClass (Table): Objeto `Table`.

        Raises:
            `ValueError`: Si una tabla o columna no existe en la base de datos.
        """

        tableClass.toUpper()
        tables = tableClass.table
        columns = tableClass.columns

        if isinstance(tables, str) and not tables in self.db.allTables:
            raise ValueError(f"Table {tables} not exist!")

        if isinstance(tableClass.table, list):
            for tableName in tables:
                if not tableName in self.db.allTables:
                    raise ValueError(f"Table {tableName} not exist!")

        if isinstance(tables, str) and isinstance(columns, str) and not self.db.existColumn(tables, columns):
            raise ValueError(
                f"Column {columns} not exist in table {tables}!")

        if isinstance(tableClass.table, list):
            for tableName in tables:
                for columnName in columns:
                    if not self.db.existColumn(tableName, columnName):
                        raise ValueError(
                            f"Column {columnName} not exist in table {tableName}!")

    def getIDChild(self, nameColumn: str) -> int | None:
        """
        Obtiene el ID de la tabla hija.

        Args:
            nameColumn (str): Nombre de la columna.

        Returns:
            int | None: ID de la tabla hija.

        Raises:
            `oracledb.DatabaseError`: Error al ejecutar la operación.
        """

        if nameColumn.find("CVE_") == -1:
            return None

        nameColumn = nameColumn.split("_")[1]
        query = f"SELECT MAX(ID_{nameColumn}) FROM  SOFIDBA_02.{nameColumn}"
        try:
            self.db.cursor.execute(query)
            ID = self.db.cursor.fetchone()[0]
            return ID
        except oracledb.DatabaseError as e:
            raise e

    def insert(self, table: Table):
        """
        Ejecuta la operación INSERT.

        Args:
            table (Table): Objeto `Table`.

        Raises:
            `oracledb.DatabaseError`: Error al ejecutar la operación en la base de datos.
        """
        query = f"INSERT INTO SOFIDBA_02.{table.table}("
        valuesQuery = " VALUES("
        for column, values in zip(table.columns, table.values):
            query += f"{column}, "
            if isinstance(values, str):
                valuesQuery += f"'{values}', "
            elif isinstance(values, int):
                valuesQuery += f"{values}, "
            else:
                ID = self.getIDChild(column)
                if ID is None:
                    valuesQuery += "NULL, "
                else:
                    valuesQuery += f"{ID}, "
        valuesQuery = valuesQuery[:-2] + ")"
        query = query[:-2] + ")" + valuesQuery
        try:
            print("Inserting...", end=" ")
            self.db.cursor.execute(query)
            print("OK!")
        except oracledb.DatabaseError as e:
            e.args[0].message = f"{
                e.args[0].message} en tabla {table.table}"
            raise e

    def update(self, table: Table):
        """
        Ejecuta la operación UPDATE.

        Args:
            table (Table): Objeto `Table`.

        Returns:
            int | str: Número de filas modificadas o mensaje de no modificación.

        Raises:
            `oracledb.DatabaseError`: Error al ejecutar la operación en la base de datos.
        """
        query = f"UPDATE SOFIDBA_02.{table.table} SET "
        for column, values in zip(table.columns, table.values):
            if isinstance(values, str):
                query += f"{column}='{values}', "
            elif isinstance(values, int):
                query += f"{column}={values}, "
        query = query[:-2]
        query += f" WHERE {table.where}"
        try:
            print("Updating...", end=" ")
            self.db.cursor.execute(query)
            print("OK!")
            return self.db.cursor.rowcount if self.db.cursor.rowcount > 0 else "Not modified!"
        except oracledb.DatabaseError as e:
            e.args[0].message = f"{
                e.args[0].message} en tabla {table.table}"
            raise e

    def delete(self, table: Table):
        """
        Ejecuta la operación DELETE.

        Args:
            table (Table): Objeto `Table`.

        Raises:
            `oracledb.DatabaseError`: Error al ejecutar la operación en la base de datos.
        """
        query = f"DELETE FROM SOFIDBA_02.{table.table} WHERE {table.where}"
        try:
            print("Deleting...", end=" ")
            self.db.cursor.execute(query)
            print("OK!")
        except oracledb.DatabaseError as e:
            e.args[0].message = f"{
                e.args[0].message} en tabla {table.table}"
            raise e
