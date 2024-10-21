#!/usr/bin/python

import json
import sqlite3
import os
from typing import Dict


def item_jsonify(input_item: list) -> dict:
    if not input_item:
        return {}

    item = {
        'Title': input_item[1],
        'Author': input_item[0],
        'ISBN': input_item[2],
        'Price': input_item[3],
        'Count': input_item[4],
        'Publisher': input_item[5]
    }

    return item


class database_interface:
    def __init__(self, _json_file_path):
        self.json_file_path = _json_file_path

    if os.path.exists('books.db'):
        os.remove('books.db')

    def get_db_connection(self):
        db_connection = sqlite3.connect('books.db')
        return db_connection

    def create_db_table(self):
        book_table = """
            CREATE TABLE IF NOT EXISTS books (
                authorName TEXT NOT NULL,
                bookName TEXT NOT NULL,
                ISBN TEXT NOT NULL PRIMARY KEY UNIQUE,
                bookPrice TEXT NOT NULL,
                bookAmount TEXT NOT NULL,
                publisher TEXT NOT NULL
            )
        """
        try:
            # Attempt to get a database connection
            db_connection = self.get_db_connection()
            try:
                db_connection.execute(book_table)
                print("Table created successfully or already exists.")
            except Exception as e:
                print(f"An error occurred while creating the table: {e}")
            finally:
                db_connection.close()
        except Exception as e:
            print(f"An error occurred while connecting to the database: {e}")

    def load_data_to_database(self):
        with open(self.json_file_path, encoding='utf-8-sig') as json_file:
            json_data = json.loads(json_file.read())

            __object = []
            __objects = []
            for _object in json_data["books"]:
                __object.append(_object['Author'])
                __object.append(_object['Title'])
                __object.append(_object['ISBN'])
                __object.append(_object['Price'])
                __object.append(_object['Amount'])
                __object.append(_object['Publisher'])

                __objects.append(tuple(__object))
                __object.clear()

            insert_command = """
                INSERT OR IGNORE INTO books (authorName,
                                             bookName,
                                             ISBN,
                                             bookPrice,
                                             bookAmount,
                                             publisher) VALUES (?, ?, ?, ?, ?, ?)
            """
            db_connection = self.get_db_connection()
            db_connection.executemany(insert_command, __objects)

            db_connection.commit()
            db_connection.close()

    def get_list_of_items(self) -> list:
        try:
            # Establish a database connection
            db_connection = self.get_db_connection()
            db_cursor = db_connection.cursor()

            # Execute the query to fetch all books
            db_cursor.execute("SELECT * FROM books")
            ret_value = db_cursor.fetchall()

        except Exception as e:
            print(f"An error occurred while fetching items: {e}")
            ret_value = []

        finally:
            # Ensure that the cursor and connection are closed properly
            if db_cursor:
                db_cursor.close()
            if db_connection:
                db_connection.close()

        items = []
        for item in ret_value:
            items.append(item_jsonify(item))

        return items

    def delete_data_from_db(self, _id: str):
        try:
            with self.get_db_connection() as db_connection:
                db_connection.execute("DELETE FROM books WHERE ISBN = ?", (_id,))
                db_connection.commit()
                print(f"Deleted book with ISBN: {_id}")
        except Exception as err:
            print(f"Error deleting book with ISBN {_id}: {err}")
            raise

    def reduce_book_amount_by_title(self, _title: str) -> bool:
        try:
            # Get database connection and cursor
            db_connection = self.get_db_connection()
            with db_connection:  # Automatically commits or rolls back
                db_cursor = db_connection.cursor()

                # Fetch current book amount
                db_cursor.execute("SELECT bookAmount FROM books WHERE bookName = ?", (_title,))
                ret_value = db_cursor.fetchone()

                # Check if the book exists and has a positive amount
                if not ret_value or ret_value[0] == '0':
                    return False

                _ret_value = str(int(ret_value[0]) - 1)

                # Update the book amount in the database
                db_cursor.execute("UPDATE books SET bookAmount = ? WHERE bookName = ?", (_ret_value, _title))

                if __debug__:
                    print('Current Amount of Item in DB:', _ret_value)

                return True

        except Exception as e:
            print(f"Error in reducing book amount occurred: {e}")
            return False

    def reduce_book_amount_by_id(self, _id: str) -> bool:
        db_connection = self.get_db_connection()
        db_cursor = db_connection.cursor()

        try:
            # Fetch the current book amount
            db_cursor.execute("SELECT bookAmount FROM books WHERE ISBN = ?", (_id,))
            ret_value = db_cursor.fetchone()

            if ret_value and ret_value[0] == '0':
                return False

            new_amount = str(int(ret_value[0]) - 1)
            db_cursor.execute("UPDATE books SET bookAmount = ? WHERE ISBN = ?", (new_amount, _id))
            db_connection.commit()

            if __debug__:
                print('Current Amount of Item in DB: ', new_amount)

            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False
        finally:
            db_cursor.close()
            db_connection.close()

    def check_book_by_title(self, _title: str) -> dict:
        db_connection = self.get_db_connection()
        db_cursor = db_connection.cursor()

        db_cursor.execute("SELECT * FROM books WHERE bookName = ?", (_title,))

        ret_value = db_cursor.fetchall()

        db_cursor.close()
        db_connection.close()

        status_data: Dict[str, str] = {'status': '', 'count': ''}

        if not ret_value:
            status_data.update({'status': 'item-does-not-exist', 'count': ''})

            return json.dumps(status_data)
        else:
            if ret_value[0][4] == "0":
                status_data.update({'status': 'item-not-available', 'count': '0'})

                return json.dumps(status_data)
            else:
                status_data.update({'status': 'item-does-exist', 'count': ret_value[0][4]})

                return json.dumps(status_data)

    def check_book_by_id(self, _id: str) -> dict:
        db_connection = self.get_db_connection()
        db_cursor = db_connection.cursor()

        db_cursor.execute("SELECT * FROM books WHERE ISBN = ?", (_id,))

        ret_value = db_cursor.fetchall()

        db_cursor.close()
        db_connection.close()

        status_data: Dict[str, str] = {'status': '', 'count': ''}

        if not ret_value:
            status_data.update({'status': 'item-does-not-exist', 'count': ''})

            return json.dumps(status_data)
        else:
            if ret_value[0][4] == "0":
                status_data.update({'status': 'item-not-available', 'count': '0'})

                return json.dumps(status_data)
            else:
                status_data.update({'status': 'item-does-exist', 'count': ret_value[0][4]})

                return json.dumps(status_data)

    def get_book_by_title(self, _title: str) -> dict:
        check_item = json.loads(self.check_book_by_title(_title))
        if check_item.get('status') == 'item-does-exist':
            db_connection = self.get_db_connection()
            db_cursor = db_connection.cursor()

            db_cursor.execute("SELECT * FROM books WHERE bookName = ?", (_title,))

            ret_value = db_cursor.fetchall()

            db_cursor.close()
            db_connection.close()

            _ret_value = item_jsonify(ret_value[0])
            if _ret_value == {}:
                _ret_value.update({'status': 'item-jsonify-failed'})
            else:
                _ret_value.update({'status': 'item-does-exist'})

            # TODO
            # This function not functional - FIX IT
            # TODO
            if self.reduce_book_amount_by_title(_title):
                return json.dumps(_ret_value)
            else:
                _ret_value.update({'status': 'item-does-not-exist'})
                return json.dumps(_ret_value)
        else:
            return json.dumps(check_item)

    def get_book_by_id(self, _id: str) -> dict:
        check_item = json.loads(self.check_book_by_id(_id))
        if check_item.get('status') == 'item-does-exist':
            db_connection = self.get_db_connection()
            db_cursor = db_connection.cursor()

            db_cursor.execute("SELECT * FROM books WHERE ISBN = ?", (_id,))

            ret_value = db_cursor.fetchall()

            db_cursor.close()
            db_connection.close()

            _ret_value = item_jsonify(ret_value[0])
            if _ret_value == {}:
                _ret_value.update({'status': 'item-jsonify-failed'})
            else:
                _ret_value.update({'status': 'item-does-exist'})

            self.reduce_book_amount_by_id(_id)

            return _ret_value
        else:
            return check_item

    def get_book_price_by_title(self, _title: str) -> dict:
        db_connection = self.get_db_connection()
        db_cursor = db_connection.cursor()

        db_cursor.execute("SELECT bookPrice FROM books WHERE bookName = ?", (_title,))

        ret_value = db_cursor.fetchall()

        db_cursor.close()
        db_connection.close()

        status_data: Dict[str, str, str] = {'type': 'retrieve-item-price', 'status': '', 'price': ''}

        if ret_value and ret_value[0]:
            if __debug__:
                print(' --> Book Price: ', ret_value[0][0])

            status_data.update({'status': 'item-does-exist', 'price': ret_value[0][0]})

            return json.dumps(status_data)
        else:
            if __debug__:
                print(' --> Book does not exist')

            status_data.update({'status': 'item-does-not-exist'})

            return json.dumps(status_data)

    def get_book_price_by_id(self, _id: str) -> dict:
        db_connection = self.get_db_connection()
        db_cursor = db_connection.cursor()

        db_cursor.execute("SELECT bookPrice FROM books WHERE ISBN = ?", (_id,))

        ret_value = db_cursor.fetchall()

        db_cursor.close()
        db_connection.close()

        status_data: Dict[str, str, str] = dict(type='retrieve-item-price', status='', price='')

        if ret_value and ret_value[0]:
            if __debug__:
                print(' --> Book Price: ', ret_value[0][0])

            status_data.update({'status': 'item-does-exist', 'price': ret_value[0][0]})

            return status_data
        else:
            if __debug__:
                print(' --> Book does not exist')

            status_data.update({'status': 'item-does-not-exist'})

            return status_data
