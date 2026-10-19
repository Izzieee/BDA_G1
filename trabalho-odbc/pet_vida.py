import pyodbc

conn_str = (
    r"Driver={ODBC Driver 17 for SQL Server};"
    r"Server=localhost\SQLEXPRESS;"
    r"Database=PetVida;"
    r"Trusted_Connection=yes;"
    r"TrustServerCertificate=yes;"
)


conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

query = "SELECT * FROM dbo.pet"
cursor.execute(query)

rows = cursor.fetchall()
for row in rows:
    print(row)

cursor.close()
conn.close()