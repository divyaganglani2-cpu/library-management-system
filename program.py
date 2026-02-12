import mysql.connector as c
import sys
import datetime as d
from decimal import Decimal
from utils import log_all_methods,log_and_protect,get_configured_logger,logger

#database connection logic
try:
    con=c.connect(host="localhost",user="root",password="",database="library")
    logger.info("connected to database successfully")
except:
    logger.critical("error occured")
    logger.exception("Cannot connect to database")
    sys.exit()
cursor=con.cursor()

#*******************************************
# cursor.execute("""CREATE TABLE admin (
#     admin_id INT PRIMARY KEY AUTO_INCREMENT, 
#     password VARCHAR(255) NOT NULL
# ) """)
#*******************************************

# cursor.execute("""INSERT INTO user (user_id, password, name, books_issued) VALUES
# (101, 'pswd123', 'Alice Johnson', 2),
# (102, 'secure456', 'Bob Smith', 0),
# (103, 'hash789', 'Charlie Brown', 1),
# (104, 'bookworm', 'Diana Prince', 3),
# (105, 'lastpass', 'Eve Harrington', 0);""")
# con.commit()
#*******************************************
# cursor.execute("insert into inventory(book_id,total_copies,issued,available) select book_id,copies_available as total_copies,0 as issued,copies_available as available from books;")
# con.commit()
@log_and_protect
def authentication(profile):
    id=int(input("Enter your id: "))
    password=input("Enter your password: ").strip()
    if profile==1:
        query="""select * from admin;"""
    elif profile==2:
        query="""select * from user;"""

    cursor.execute(query)
    auth_list=cursor.fetchall()
    # print(auth_list)
    for i in auth_list:
        if i[0]==id and i[1]==password:
            logger.info("profile logged in successfully")
            print("Welcome! ")
            return id
        else:
            logger.critical("unauthorized acess")
            sys.exit("wrong password! try again later!")
@log_all_methods
class book:
    def __init__(self,title,author,genre,price,copies_available):
        
        self.title=title
        self.author=author
        self.genre=genre
        self.price=price
        self.copies_available=copies_available
@log_all_methods
class Admin:
    def __init__(self,admin_id):
        self.admin_id=admin_id
    def new_book(self,book):
        cursor.execute("insert into books (title,author,genre,price,copies_available) values (%s,%s,%s,%s,%s)",(book.title,book.author,book.genre,book.price,book.copies_available))
        con.commit()
    def check(self,table_name):
        query=f"select * from {table_name}"
        cursor.execute(query)
        data=cursor.fetchall()
        for i in data:
            print(i)
        return data
        
    def delete_book(self,book_name):
       
        cursor.execute("""delete from books where title=%s""",(book_name,))
        if cursor.rowcount==0:
            raise ValueError(f"{book_name} does not exist in library")
        print(f"{book_name} is deleted")
        con.commit()
        
        
    def update(self,table_name):
        
        cursor.execute("SELECT column_name, data_type FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s AND table_schema ='library' ORDER BY ordinal_position;",(table_name,))
        a=cursor.fetchall()
        print(a)
        #listing columns
        columns_dict={i:value[0] for i,value in enumerate(a[1:],start=1)}
        print(f"available columns are-{columns_dict}")
        column=int(input("Enter the column number you want to update: "))
        row=int(input("Enter the bookid you want to update: "))
        #taking input based on datatype of the column
        if a[column][1]=='int' or a[column][1]=='decimal':
            new=int(input("Enter the new value: "))
        else:
            new=input("Enter the new value: ")
        
        query=f"update {table_name} set {columns_dict[column]}=%s where {a[0][0]}=%s;"
        cursor.execute(query,(new,row))
        if cursor.rowcount==0:
            raise ValueError(f"Either book_id or column provided are wrong in {table_name}")
        con.commit()
        
    
@log_all_methods
class User:
    def __init__(self,id):
        self.id=id
    def book_check(self):
        cursor.execute("select book_id,title,author,genre,price,copies_available from books")
        print("Available books are:")
        for i in cursor.fetchall():
            print(i)
    def issue(self,book_id):
        
        cursor.execute("select available from inventory where book_id=%s",(book_id,))
        is_book=cursor.fetchone()[0]#fetchone returns the one single tuple matching the query here(5) is the tuple if i added more columns all those would be included for the single one row,by writting [0] i mean 5
        
        if is_book>0:
            cursor.execute("select price from books where book_id=%s",(book_id,))
            price=cursor.fetchone()[0]
            print(f"for issuing this book the advance payment is {price}")
            payment=input("Enter Y for payment and N to go back!").strip().lower()
            if payment=='y':
                print(f"payment done-{price}")
                cursor.execute("update inventory set issued=issued+1,available=available-1 where book_id=%s ",(book_id,))
                cursor.execute("update user set books_issued=books_issued+1 where user_id=%s",(self.id,))
                date_issued=d.date.today()
                return_date=date_issued+d.timedelta(days=5)
                cursor.execute("insert into issuer (book_id,user_id,date_issued,return_date,advance_payment) values (%s,%s,%s,%s,%s);",(book_id,self.id,date_issued,return_date,price))
                con.commit()
                print(f"The book is issued to user id- {self.id} on {date_issued} date")
                print(f"The book should be returned to the library by {return_date} ")
                print(f"Advance payment of {price} is deposited with the library")
                print(f"If not submitted on time ,a penalty amount will pe deducted from the deposited amount by the user.")
                return 
            elif payment=='n':
                return
            else:
                print("no valid choice")
                return
        else:
            print("This book is currently unavailable.Kindly try again later!")
            return
    def check_issued(self):
        cursor.execute("""select book_id,title from books where book_id in (select book_id from issuer where user_id=%s);""",(self.id,))
        print(f"books issued by user id {self.id} are-")
        if len(cursor.fetchall())==0:
            print("None")
            return
        for i in cursor.fetchall():
            print(*i)
            return
    def return_book(self,book_id):
        query="""SELECT CASE WHEN EXISTS
        (SELECT 1 FROM issuer WHERE user_id=%s AND book_id=%s AND returned_at IS NULL )
        THEN 'issued'
        ELSE 'not issued'
        END AS 'status checked';
        """
        cursor.execute(query,(self.id,book_id))
        if cursor.fetchone()[0]=='issued':
            query="""SELECT * FROM issuer WHERE user_id=%s AND book_id=%s """
            cursor.execute(query,(self.id,book_id))
            issued=cursor.fetchone()
            print(issued)
            return_date=issued[4]
            returned_at=d.date.today()
            advance=issued[6]
            print(f"The book was issued on {issued[3]}")
            print(f"The due date was {return_date}")
            print(f"The book is returned at {returned_at}")

            if returned_at>return_date:
                delay=(returned_at-return_date).days
                paid=delay*(Decimal(str(0.02)*advance))
                remain=advance-paid
                print(f"The advance deposit was {advance}")
                print(f"The charged amount is {paid}")
                print(f"Here is your remaining amount-{remain}")
            else:
                print(f"No charges! Take your advance deposit-{advance}")
            cursor.execute("""delete from issuer where book_id=%s and user_id=%s""",(book_id,self.id))
            cursor.execute("""update inventory set available=available+1,issued=issued-1 where book_id=%s """,(book_id,))
            cursor.execute("""update user set books_issued=books_issued-1 where user_id=%s""",(self.id,))
            con.commit()

        else:
            print(f"Book with {book_id} book id was not issued to you.kindly check again the book id you entered! ")

def main():
    while True:
    # print(Admin.__dict__.items())
        profile=int(input("enter 1 for Admin ,2 for user"))
        if profile not in(1,2):
            print("please enter a valid profile!")
        id=authentication(profile)
        while True:
            if profile==1:
                admin=Admin(id)
                print("options for admin:")
                print("""Add book-1,delete book-2,update/check a specific table-3""")
                choice=int(input("Enter your choice: " ))

                if choice==1:
                    print("provide the details for the book you want to add-- ")
                    title=input("Book name: ")
                    author=input("Author: ")
                    genre=input("Genre: ")
                    price=input("Price of the book: ")
                    copies_available=int(input("How many copies of this book are being added: "))
                    newBook=book(title,author,genre,price,copies_available)
                    admin.new_book(newBook)
                    print(f"new book-{title}- added")
                elif choice==2:
                    book_name=input("Enter the name of the book to be deleted: ").strip().title()
                    admin.delete_book(book_name)
                elif choice==3:
                    table_dict={1:"books",2:"inventory",3:"issuer",4:"user"}
                    print("Available tables are-")
                    print(table_dict)
                    table=int(input("Enter the table number you want to update/check: "))
                    operation=int(input("Enter 1 for update and 2 for check"))
                    if operation==1:
                        admin.update(table_dict[table])
                    if operation==2:
                        admin.check(table_dict[table])
                
                else:
                    print("please enter a valid choice!")

            elif profile==2:
                user=User(id)
                print("options available for user are: ")
                print("1-inventory check,2-issuing,3-check what issued ,4-return a book")
                choice=int(input("Enter your choice: "))
                if choice==1:
                    user.book_check()
                elif choice==2:
                    book_id=int(input("Enter the book id to be issued: "))
                    user.issue(book_id)
                elif choice==3:
                    user.check_issued()
                elif choice==4:
                    cursor.execute("select 1 from issuer where user_id=%s",(id,))
                    if len(cursor.fetchall())==0:
                        print(f"You have not issued any book yet!")
                        continue
                    book_id=int(input("Enter the book id to be returned: "))
                    user.return_book(book_id)
                else:
                    print("please enter a valid choice!")
            end=input("Enter 'L' to logout 'E' to exit the program and 'C' to continue ").strip().lower()
            if end=='c':
                continue
            elif end=='l':
                    break
            elif end=='e':
                sys.exit("Thankyou for using library management system!Have a good day!")


if __name__=="__main__":
    main()
