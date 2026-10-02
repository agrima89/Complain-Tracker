import sqlite3

c = sqlite3.connect('database.db')
c.execute("UPDATE complaints SET department = 'Wi-Fi / Internet' WHERE category = 'Wi-Fi/Internet'")
c.commit()
c.close()
