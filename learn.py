import sys
import MySQLdb as mdb
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from edit_product import Ui_MainWindow as EditProductUI
from edit_order import Ui_MainWindow as EditOrderUI
from login import Ui_MainWindow as LoginUI
from order_card import Ui_Form as OrderCardUI
from orders_window import Ui_MainWindow as OrderWindowUI
from products import Ui_MainWindow as ProductWindowUI
from product_card import Ui_Form as ProductCardUI


def select(query,params=()):
    con = mdb.connect('localhost', 'root', 'root', 'shop')
    cur = con.cursor()
    cur.execute(query,params)
    data = cur.fetchall()
    con.close()
    return data

def execute(query,params=()):
    con = mdb.connect('localhost', 'root', 'root', 'shop')
    cur = con.cursor()
    cur.execute(query,params)
    con.commit()
    con.close()

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = LoginUI()
        self.ui.setupUi(self)
        self.ui.btn_login.clicked.connect(self.login)
        self.ui.btn_guest.clicked.connect(self.open_quest)

    def login(self):
        login = self.ui.line_login.text()
        password = self.ui.line_password.text()

        user = select("select Role, Fio from Users where Login = %s and Password = %s", (login, password))
        user = user[0] if user else None
        role, fio = user
        self.open_products(role,fio)

    def open_guest(self):
        self.open_products("guest", "Гость")

    def open_products(self, role, fio):
        self.w = ProductsWindow(role,fio)
        self.w.show()
        self.close()

class ProductsWindow(QMainWindow):
    def __init__(self, role, fio):
        super().__init__()
        self.ui = ProductWindowUI()
        self.ui.setupUi(self)
        self.ui.line_search.textChanged.connect(self.search)
        self.ui.combo_supplier.currentIndexChanged.connect(self.search)
        self.ui.combo_sort.currentIndexChanged.connect(self.search)
        self.ui.btn_add.clicked.connect(self.open_add)
        self.ui.btn_edit.clicked.connect(self.open_edit)
        self.ui.btn_delete.clicked.connect(self.delete)
        self.ui.btn_orders.clicked.connect(self.open_orders)
        self.ui.btn_logout.clicked.connect(self.logout)
        self.role = role
        self.fio = fio
        self.ui.label_user.setText(self.fio)

        if self.role not in ("admin", "maneger"):
            self.ui.btn_add.hide()
            self.ui.btn_edit.hide()
            self.ui.btn_delete.hide()
            self.ui.btn_orders.hide()
            self.ui.combo_sort.hide()
            self.ui.combo_supplier.hide()
            self.ui.line_search.hide()

        self.search()
        self.load_suppliers()

    def load_products(self,query,params=()):
        products = select(query,params)
        for i in reversed(range(self.ui.verticalLayout.count())):
            item = self.ui.verticalLayout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        for product in products:
            card = self.create_card(product)
            self.ui.verticalLayout.addWidget(card)

        self.ui.verticalLayout.addStretch()

    def search(self):
        text = self.ui.line_search.text()
        query = f"""
             SELECT p.ProductID, p.Name, c.Name, p.Description,
        m.Name, s.Name, p.Price,
        p.Unit, p.StockQuantity,
        p.Discount, p.ImagePath
             FROM Products p
             JOIN Categories c ON p.CategoryID = c.CategoryID
             JOIN Manufacturers m ON p.ManufacturerID = m.ManufacturerID
             JOIN Suppliers s ON p.SupplierID = s.SupplierID
             WHERE (p.Name LIKE %s OR c.Name LIKE %s OR p.Description LIKE %s OR m.Name LIKE %s OR s.Name LIKE %s)
             {self.get_filter()}
             {self.get_sort()}
         """

        self.load_products(query, (f"%{text}%",)*5)

    def get_filter(self):
        supplier_id = self.ui.combo_supplier.currentData()
        if supplier_id and supplier_id != "Все поставщики":
            return f" AND p.SupplierID = {supplier_id}"
        return ""

    def get_sort(self):
        sort = self.ui.combo_sort.currentText()
        if sort == "Количество по возрастанию":
            return "Order by p.StockQuantity ASC"
        elif sort == "Количество по убыванию":
            return "order by p.StockQuantity DESC"
        return""

    def load_suppliers(self):
        suppliers = select("Select SupplierID, Name from Suppliers")
        self.ui.combo_supplier.addItem("Все поставщики", None)
        for sid, name in suppliers:
            self.ui.combo_supplier.addItem(sid,name)

    def create_card(self,product):
        widget = QWidget()
        widget.setMinimumHeight(250)
        ui = ProductCardUI()
        ui.setupUi(widget)
        widget.product_id = product[0]
        widget.mousePreventEvent = lambda event : setattr(self, "selected_id", widget.product_id)

        ui.label_name.setText(product[1])
        ui.label_category.setText(product[2])
        ui.label_description_value.setText(product[3])
        ui.label_manufacturer_value.setText(product[4])
        ui.label_supplier_value.setText(product[5])
        ui.label_unit_value.setText(product[7])
        ui.label_quantity_value.setText(str(product[8]))
        ui.label_8.setText(f"Действующая скидка {product[9]}%" if product[9] > 0 else "Скидки нет")

        p,d = product[6], product[9]
        ui.label_price_value.setText(
            f'<span style = "text-decoration: line-trough; color:red">{p:.2f}</span>{p*(100-d)/100:.2f}' if d > 0
            else f'{p:.2f}'
        )

        if product[8] == 0:
            widget.setStyleSheet("background-color: lightblue;")
        elif d > 15:
            widget.setStyleSheet("background-color: #2E8B57;")

        if product[10]:
            ui.label_image.setPixmap(QPixmap(product[10]).scaled(200,200))
        return widget

    def open_add(self):
        self.form = ProductEdit(self)
        self.form.show()

    def open_edit(self):
        if not hasattr(self, "selected_id"):
            QMessageBox.warning(self,"Ошибка", "Выберите товар")
            return
        self.form=ProductEdit(self, self.selected_id)
        self.form.show()

    def delete(self):
        if not hasattr(self,"selected_id"):
            QMessageBox.warning(self, "Ошибка", "Выберите товар")
            return
        reply = QMessageBox.question(self, "Подтверждение", "Удалить заказ?" , QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            execute("delete from Products where ProductID=%s ", (self.selected_id,))
            self.search()


    def logout(self):
        self.login_window=LoginWindow()
        self.login_window.show()
        self.close()

    def open_orders(self):
        self.order_window = OrderWindow(self.role)
        self.order_window.show()


class OrderWindow(QMainWindow):
    def __init__(self, role):
        super().__init__()
        self.ui = OrderWindowUI()
        self.ui.setupUi(self)
        self.role = role
        self.setWindowTitle("Заказы")

        if role != "admin":
            self.ui.btn_add.hide()
            self.ui.btn_edit.hide()
            self.ui.btn_delete.hide()


        self.ui.btn_delete.clicked.connect(self.delete)
        self.ui.btn_edit.clicked.connect(self.open_edit)
        self.ui.btn_add.clicked.connect(self.open_add)

        self.load_order()

    def load_orders(self):
        orders = select("SELECT OrderID, Status, DeliveryAddress, OrderDate, IssueDate FROM Orders ORDER BY OrderID DESC")

        for i in reversed(range(self.ui.verticalLayout.count())):
            item = self.ui.verticalLayout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        for order in orders:
            card = self.create_order_card(order)
            self.ui.verticalLayout.addWidget(card)

        self.ui.verticalLayout.addStretch()

    def create_order_card(self, order):
        widget = QWidget()
        ui = OrderCardUI()
        ui.setupUi(widget)
        widget.order_id = order[0]

        widget.mousePressEvent = lambda event, oid = order[0]: setattr(self, "selected_order_id", oid)

        ui.article.setText(str(order[0]))
        ui.status.setText(order[1])
        ui.address.setText(order[2])
        ui.date_order.setText(order[3].strftime("%Y-%m-%d") if order[3] else "")
        ui.date_delivery.setText(order[4].strftime("%Y-%m-%d") if order[4] else "")

        widget.setFixedHeight(300)

        return widget

    def open_add(self):
        self.form = OrderEdit(self)
        self.form.show()

    def open_edit(self):
        if hasattr(self, "selected_order_id"):
            QMessageBox.warning(self, "Ошибка", "Выберите заказ")
            return
        self.form = OrderEdit(self,self.selected_order_id)
        self.form.show()

    def delete(self):
        if not hasattr(self, "selected_order_id"):
            QMessageBox.warning(self, "Ошибка", "Выберите заказ")
            return

        reply = QMessageBox.question(self, "Подтверждение", "Удалить заказ?" , QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            execute("delete from OrderItems where OrderID=%s", (self.selected_order_id,))
            execute("delete from Orders where OrderID=%s", (self.selected_order_id,))
            self.load_orders()

class OrderEdit(QMainWindow):
    def __init__(self, parent=None, order_id=None):
        super().__init__()
        self.ui = EditOrderUI()
        self.ui.setupUi(self)
        self.parent=parent
        self.order_id = order_id
        self.ui.btn_save.clicked.connect(self.save)
        self.ui.btn_cancel.clicked.connect(self.close)

        if order_id:
            self.load_data(order_id)


    def load_data(self, order_id):
        data = select("SELECT Status, DeliveryAddress, OrderDate, IssueDate FROM Orders WHERE OrderID=%s", (order_id,))
        if data:
            status,address, order_date, issue_date = data[0]
            self.ui.edit_id.setText(str(order_id[0]))
            self.ui.combo_status.setText(order_id[1])
            self.ui.edit_address.setText(order_id[2])
            if order_date:
                self.ui.edit_date_order.setDate(order_date)
            if issue_date:
                self.ui.edit_delivery.setDate(issue_date)


    def save(self):
        status = self.ui.combo_status.currentText()
        address = self.ui.edit_address.text()
        order_date = self.ui.edit_date_order.date().ToPyDate()
        delivery_date = self.ui.edit_delivery.date().ToPyDate()

        if self.order_id:
            execute("""UPDATE Orders SET Status=%s, DeliveryAddress=%s, OrderDate=%s, IssueDate=%s
                       WHERE OrderID=%s""",
                    (status, address, order_date, delivery_date, self.order_id))
        else:
            execute("""INSERT INTO Orders (Status, DeliveryAddress, OrderDate, IssueDate)
                       VALUES (%s, %s, %s, %s)""",
                    (status, address, order_date, delivery_date))

        self.parent.load_orders()
        self.close()

class ProductEdit(QMainWindow):
    def __init__(self, parent=None, product_id=None):
        super().__init__()
        self.ui = EditProductUI()
        self.ui.setupUi(self)
        self.parent = parent
        self.product_id = product_id
        self.image_path = None

        self.ui.btn_save.clicked.connect(self.save)
        self.ui.btn_cancel.clicked.connect(self.close)
        self.ui.btn_upload_image.clicked.connect(self.upload_image)
        self.load_categories()
        self.load_suppliers()
        self.load_manufacturers()

        if product_id:
            self.load_data(product_id)

    def upload_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "Выбрать фото", "Image (*.png,*.jpg)")

        if file:
            self.image_path = file
            pixmap = QPixmap(file)
            self.ui.btn_upload_image.setPixmap(pixmap.scaled(150,150))

    def load_categories(self):
        con = mdb.connect('localhost', 'root', 'root', 'shop')
        cur = con.cursor()
        cur.execute("select CategoryID, Name from Categories")
        data = cur.fetchall()
        con.close()

        for cid, name in data:
            self.ui.combo_category.addItem(name,cid)

    def load_manufacturers(self):
        manufacturers = select("select ManufacturerID ,Name from Manufacturers")
        for mid, name in manufacturers:
            self.ui.combo_manufacturer.addItem(name,mid)

    def load_suppliers(self):
        suppliers = select("select SupplierID, Name from Suppliers")
        for sid, name in suppliers:
            self.ui.combo_supplier.addItem(name,sid)


    def load_data(self,id):








