import sys
import MySQLdb as mdb
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from login import Ui_MainWindow as LoginWindow
from products import Ui_MainWindow as ProductsUI
from product_card import Ui_Form
from edit_product import Ui_MainWindow as EditUI

def select(query, params=()):
    con = mdb.connect('localhost', 'root', 'root', 'shop')
    cur = con.cursor()
    cur.execute(query, params)
    data = cur.fetchall()
    con.close()
    return data

def execute(query, params=()):
    con = mdb.connect('localhost', 'root', 'root', 'shop')
    cur = con.cursor()
    cur.execute(query, params)
    con.commit()
    con.close()

class LoginApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = LoginWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Авторизация")
        self.ui.btn_login.clicked.connect(self.login)
        self.ui.btn_guest.clicked.connect(self.open_guest)

    def login(self):
        login = self.ui.line_login.text()
        password = self.ui.line_password.text()
        user = select(
            "SELECT Role, FIO FROM Users WHERE Login=%s AND Password=%s",
            (login, password)
        )

        user = user[0] if user else None
        role, fio = user
        self.open_products(role, fio)

    def open_guest(self):
        self.open_products("guest", "Гость")

    def open_products(self, role, fio):
        self.w = ProductsWindow(role, fio)
        self.w.show()
        self.close()

class ProductsWindow(QMainWindow):
    def __init__(self, role, fio):
        super().__init__()
        self.ui = ProductsUI()
        self.ui.setupUi(self)
        self.setWindowTitle("Товары")
        self.ui.line_search.textChanged.connect(self.search)
        self.ui.combo_supplier.currentIndexChanged.connect(self.search)
        self.ui.combo_sort.currentIndexChanged.connect(self.search)
        self.ui.btn_add.clicked.connect(self.open_add)
        self.ui.btn_edit.clicked.connect(self.open_edit)
        self.ui.btn_delete.clicked.connect(self.delete_product)
        self.ui.btn_logout.clicked.connect(self.logout)

        self.role = role
        self.fio = fio
        self.ui.label_user.setText(self.fio)

        if self.role == "admin":
            pass
        elif self.role == "client":
            self.ui.btn_add.hide()
            self.ui.btn_edit.hide()
            self.ui.btn_delete.hide()
        else:
            self.ui.btn_add.hide()
            self.ui.btn_edit.hide()
            self.ui.btn_delete.hide()
            self.ui.line_search.hide()
            self.ui.combo_supplier.hide()
            self.ui.combo_sort.hide()

        self.search()
        self.load_suppliers()

    def load_products(self, query, params=()):
        products = select(query, params)

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

        self.load_products(query, (f"%{text}%", )*5)

    def get_filter(self):
        supplier_id = self.ui.combo_supplier.currentData()
        if supplier_id and supplier_id != "Все поставщики":
            return f" AND p.SupplierID = {supplier_id}"
        return ""

    def get_sort(self):
        sort = self.ui.combo_sort.currentText()

        if sort == "Количество по возрастанию":
            return " ORDER BY p.StockQuantity ASC"
        elif sort == "Количество по убыванию":
            return " ORDER BY p.StockQuantity DESC"
        return ""

    def load_suppliers(self):
        suppliers = select("SELECT SupplierID, Name FROM Suppliers")
        self.ui.combo_supplier.addItem("Все поставщики", None)
        for sid, name in suppliers:
            self.ui.combo_supplier.addItem(name, sid)

    def create_card(self, product):
        widget = QWidget()
        widget.setMinimumHeight(250)
        ui = Ui_Form()
        ui.setupUi(widget)
        widget.product_id = product[0]
        widget.mousePressEvent = lambda event: setattr(self, 'selected_id', widget.product_id)

        ui.label_name.setText(product[1])
        ui.label_category.setText(product[2])
        ui.label_description_value.setText(product[3])
        ui.label_manufacturer_value.setText(product[4])
        ui.label_supplier_value.setText(product[5])
        ui.label_unit_value.setText(product[7])
        ui.label_quantity_value.setText(str(product[8]))
        ui.label_8.setText(f"Действующая скидка: {product[9]}%" if product[9] > 0 else "Действующей скидки нет")

        p, d = product[6], product[9]
        ui.label_price_value.setText(
            f'<span style="text-decoration: line-through; color: red;">{p:.2f}</span> {p * (100 - d) / 100:.2f}' if d > 0
            else f'{p:.2f}'
        )

        if product[8] == 0:
            widget.setStyleSheet("background-color: lightblue;")
        elif d > 15:
            widget.setStyleSheet("background-color: green;")

        if product[10]:
            ui.label_image.setPixmap(QPixmap(product[10]).scaled(200, 200))
        return widget

    def open_add(self):
        self.form = ProductForm(self)
        self.form.show()

    def open_edit(self):
        self.form = ProductForm(self, self.selected_id)
        self.form.show()

    def delete_product(self):
        execute("DELETE FROM Products WHERE ProductID=%s", (self.selected_id,))
        self.search()

    def logout(self):
        self.login_window = LoginApp()
        self.login_window.show()
        self.close()

class ProductForm(QMainWindow):
    def __init__(self, parent=None, product_id=None):
        super().__init__()
        self.ui = EditUI()
        self.ui.setupUi(self)
        self.parent = parent
        self.product_id = product_id
        self.image_path = None

        self.ui.btn_save.clicked.connect(self.save)
        self.ui.btn_cancel.clicked.connect(self.close)
        self.ui.btn_upload_image.clicked.connect(self.upload_image)
        self.load_categories()
        self.load_manufacturers()
        self.load_suppliers()
        if product_id:
            self.load_data(product_id)

    def load_categories(self):
        con = mdb.connect('localhost', 'root', 'root', 'shop')
        cur = con.cursor()
        cur.execute("SELECT CategoryID, Name FROM Categories")
        data = cur.fetchall()
        con.close()

        for cid, name in data:
            self.ui.combo_category.addItem(name, cid)

    def load_manufacturers(self):
        manufacturers = select("SELECT ManufacturerID, Name FROM Manufacturers")
        for mid, name in manufacturers:
            self.ui.combo_manufacturer.addItem(name, mid)

    def load_suppliers(self):
        suppliers = select("SELECT SupplierID, Name FROM Suppliers")
        for sid, name in suppliers:
            self.ui.combo_supplier.addItem(name, sid)

    def load_data(self, id):
        product = select("SELECT * FROM Products WHERE ProductID=%s", (id,))
        product = product[0] if product else None

        if product:
            self.ui.edit_id.setText(str(product[0]))
            self.ui.edit_name.setText(product[1])
            self.ui.edit_description.setText(product[3])
            index = self.ui.combo_category.findData(product[2])
            if index >= 0:
                self.ui.combo_category.setCurrentIndex(index)
            manuf_index = self.ui.combo_manufacturer.findData(product[4])
            if manuf_index >= 0:
                self.ui.combo_manufacturer.setCurrentIndex(manuf_index)
            supp_index = self.ui.combo_supplier.findData(product[5])
            if supp_index >= 0:
                self.ui.combo_supplier.setCurrentIndex(supp_index)
            self.ui.edit_price.setText(str(product[6]))
            self.ui.edit_unit.setText(product[7])
            self.ui.edit_quantity.setText(str(product[8]))
            self.ui.edit_discount.setText(str(product[9]))

            self.image_path = product[10]

            if self.image_path:
                pixmap = QPixmap(self.image_path)
                self.ui.label_image_edit.setPixmap(pixmap.scaled(150, 150))

    def save(self):
        name = self.ui.edit_name.text()
        category_id = self.ui.combo_category.currentData()
        description = self.ui.edit_description.text()
        manufacturer_id = self.ui.combo_manufacturer.currentData()
        supplier_id = self.ui.combo_supplier.currentData()
        price = self.ui.edit_price.text()
        unit = self.ui.edit_unit.text()
        quantity = self.ui.edit_quantity.text()
        discount = self.ui.edit_discount.text()

        con = mdb.connect('localhost', 'root', 'root', 'shop')
        cur = con.cursor()

        if self.product_id:
            cur.execute("""
                UPDATE Products SET
                Name=%s, CategoryID=%s, Description=%s,ManufacturerID=%s, SupplierID=%s,Price=%s, Unit=%s, StockQuantity=%s, Discount=%s, ImagePath=%s
                WHERE ProductID=%s""",
                (name, category_id, description,manufacturer_id, supplier_id, price, unit, quantity,discount, self.image_path, self.product_id))
        else:
            cur.execute("""
                INSERT INTO Products(Name, CategoryID, Description, ManufacturerID, SupplierID,Price, Unit, StockQuantity, Discount, ImagePath)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (name, category_id, description,manufacturer_id, supplier_id,price, unit, quantity, discount, self.image_path))

        con.commit()
        con.close()
        self.parent.search()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginApp()
    window.show()
    sys.exit(app.exec())
