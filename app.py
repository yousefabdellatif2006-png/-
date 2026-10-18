import sqlite3
from pathlib import Path
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

DB = Path(__file__).with_name("pro_store.db")

st.set_page_config(
    page_title="PRO STORE",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"],
[data-testid="stMarkdownContainer"], p, label, span, div {
    font-family: 'Cairo', sans-serif;
}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: #f4f6fa;
    color: #111827;
}
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li, label, .stText, .stCaption,
[data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
    color: #111827 !important;
}
.block-container { padding-top: 1.5rem; max-width: 1500px; }
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #14213d, #203d66);
}
section[data-testid="stSidebar"] * { color: #ffffff !important; }
.hero {
    background: linear-gradient(120deg, #14213d, #2874b8);
    padding: 25px; border-radius: 18px; color: white; margin-bottom: 22px;
}
.hero h1 { color: white !important; margin: 0; font-weight: 800; }
.hero p { color: white !important; margin-bottom: 0; opacity: .95; }
div[data-testid="stMetric"] {
    background: white; padding: 17px; border-radius: 15px;
    border: 1px solid #e3e8f0; box-shadow: 0 4px 14px #14213d0a;
}
h1, h2, h3, h4 { color: #14213d !important; }
.stTextInput input, .stNumberInput input, .stDateInput input,
.stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div,
.stTextArea textarea {
    background: #ffffff !important; color: #111827 !important;
}
[data-testid="stDataFrame"], [data-testid="stTable"] {
    background: #ffffff;
}
.stButton button, .stDownloadButton button, .stFormSubmitButton button {
    border-radius: 9px;
}
</style>
""", unsafe_allow_html=True)


def connect():
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, category TEXT NOT NULL DEFAULT 'General',
            price REAL NOT NULL DEFAULT 0, cost REAL NOT NULL DEFAULT 0,
            stock INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            phone TEXT DEFAULT '', email TEXT DEFAULT '', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            phone TEXT DEFAULT '', company TEXT DEFAULT '', address TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT NOT NULL,
            total REAL NOT NULL, status TEXT NOT NULL DEFAULT 'Completed',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL,
            product_id INTEGER, product_name TEXT NOT NULL, qty INTEGER NOT NULL,
            price REAL NOT NULL, cost REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_name TEXT NOT NULL,
            product_id INTEGER, product_name TEXT NOT NULL, qty INTEGER NOT NULL,
            cost REAL NOT NULL, total REAL NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            category TEXT NOT NULL, amount REAL NOT NULL, created_at TEXT NOT NULL
        );
        """)
        defaults = {"store_name": "PRO STORE", "currency": "EGP", "low_stock": "5"}
        for key, value in defaults.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings(key, value) VALUES(?, ?)",
                (key, value),
            )


def query(sql, params=()):
    with connect() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def execute(sql, params=()):
    with connect() as conn:
        cur = conn.execute(sql, params)
        return cur.lastrowid


def get_setting(key, default=""):
    with connect() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default


def save_setting(key, value):
    with connect() as conn:
        conn.execute("""
            INSERT INTO settings(key, value) VALUES(?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """, (key, str(value)))


def currency():
    return get_setting("currency", "EGP")


def money(value):
    return f"{float(value):,.2f} {currency()}"


def today():
    return date.today().isoformat()


init_db()
store_name = get_setting("store_name", "PRO STORE")

pages = [
    "Dashboard", "Products & Inventory", "Sales & Orders", "Purchases",
    "Customers", "Suppliers", "Expenses", "Reports", "Settings"
]

with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:15px 0;color:white'>
      <div style='font-size:48px'>🛍️</div>
      <div style='font-size:25px;font-weight:800'>PRO STORE</div>
      <div style='font-size:12px'>Store Management System</div>
    </div>
    """, unsafe_allow_html=True)
    page = st.radio("Main Menu", pages)
    st.divider()
    st.caption("Local Version")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

st.markdown(
    f"<div class='hero'><h1>{store_name}</h1>"
    "<p>Manage sales, inventory, and purchases from one place</p></div>",
    unsafe_allow_html=True,
)

if page == "Dashboard":
    products = query("SELECT * FROM products")
    orders = query("SELECT * FROM orders")
    purchases = query("SELECT * FROM purchases")
    expenses = query("SELECT * FROM expenses")
    items = query("SELECT qty, cost FROM order_items")
    revenue = float(orders["total"].sum()) if not orders.empty else 0
    purchase_total = float(purchases["total"].sum()) if not purchases.empty else 0
    expense_total = float(expenses["amount"].sum()) if not expenses.empty else 0
    cost_sold = float((items["qty"] * items["cost"]).sum()) if not items.empty else 0
    profit = revenue - cost_sold - expense_total
    inventory_value = float((products["stock"] * products["cost"]).sum()) if not products.empty else 0
    limit = int(get_setting("low_stock", "5"))
    low_stock = products[products["stock"] <= limit] if not products.empty else pd.DataFrame()

    a, b, c, d = st.columns(4)
    a.metric("💰 Total Sales", money(revenue))
    b.metric("📈 Estimated Net Profit", money(profit))
    c.metric("📦 Number of Products", len(products))
    d.metric("⚠️ Low-Stock Products", len(low_stock))

    left, right = st.columns([1.6, 1])
    with left:
        st.subheader("📊 Daily Sales")
        if not orders.empty:
            chart_data = orders.copy()
            chart_data["Day"] = pd.to_datetime(chart_data["created_at"]).dt.strftime("%Y-%m-%d")
            chart_data = chart_data[
                pd.to_datetime(chart_data["created_at"]) >=
                pd.Timestamp(date.today() - timedelta(days=6))
            ]
            daily = chart_data.groupby("Day", as_index=False)["total"].sum()
            if not daily.empty:
                fig = px.bar(daily, x="Day", y="total", text_auto=".2s",
                             color_discrete_sequence=["#2874b8"])
                fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                                  margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("There have been no sales in the last 7 days.")
        else:
            st.info("Record your first sale to display the chart.")
    with right:
        st.subheader("🧾 Financial Summary")
        st.metric("Total Purchases", money(purchase_total))
        st.metric("Total Expenses", money(expense_total))
        st.metric("Inventory Value", money(inventory_value))

    st.subheader("⚠️ Low-Stock Alerts")
    if low_stock.empty:
        st.success("There are no low-stock products.")
    else:
        st.dataframe(low_stock[["name", "category", "stock", "price"]].rename(columns={
            "name": "Product", "category": "Category", "stock": "Quantity", "price": "Selling Price"
        }), use_container_width=True, hide_index=True)

    st.subheader("🕘 Recent Orders")
    recent = query("SELECT id, customer_name, total, status, created_at FROM orders ORDER BY id DESC LIMIT 10")
    if recent.empty:
        st.info("No orders have been recorded.")
    else:
        st.dataframe(recent.rename(columns={
            "id": "Order ID", "customer_name": "Customer", "total": "Total",
            "status": "Status", "created_at": "Date"
        }), use_container_width=True, hide_index=True)

elif page == "Products & Inventory":
    st.subheader("📦 Products & Inventory")
    tab1, tab2 = st.tabs(["Add Product", "Manage Products"])
    with tab1:
        with st.form("add_product", clear_on_submit=True):
            a, b = st.columns(2)
            name = a.text_input("Product Name *")
            category = b.text_input("Category", value="General")
            c, d, e = st.columns(3)
            price = c.number_input("Selling Price", min_value=0.0, step=10.0)
            cost = d.number_input("Unit Cost", min_value=0.0, step=10.0)
            stock = e.number_input("Opening Stock", min_value=0, step=1)
            submitted = st.form_submit_button("➕ Save Product", use_container_width=True)
            if submitted:
                if not name.strip():
                    st.error("Enter a product name.")
                else:
                    execute("""INSERT INTO products(name, category, price, cost, stock, created_at)
                               VALUES(?,?,?,?,?,?)""",
                            (name.strip(), category.strip() or "General", price, cost, int(stock), today()))
                    st.success("Product added successfully.")
                    st.rerun()
    with tab2:
        products = query("SELECT * FROM products ORDER BY id DESC")
        if products.empty:
            st.info("There are no products yet.")
        else:
            labels = {int(r["id"]): f'{r["name"]} — #{r["id"]}' for _, r in products.iterrows()}
            pid = st.selectbox("Select a product to edit or delete", list(labels), format_func=lambda x: labels[x])
            row = products[products["id"] == pid].iloc[0]
            with st.form("edit_product"):
                a, b = st.columns(2)
                name = a.text_input("Product Name", value=str(row["name"]))
                category = b.text_input("Category", value=str(row["category"]))
                c, d, e = st.columns(3)
                price = c.number_input("Selling Price", min_value=0.0, value=float(row["price"]), step=10.0)
                cost = d.number_input("Unit Cost", min_value=0.0, value=float(row["cost"]), step=10.0)
                stock = e.number_input("Stock", min_value=0, value=int(row["stock"]), step=1)
                save = st.form_submit_button("💾 Save Changes")
                delete = st.form_submit_button("🗑️ Delete Product")
                if save:
                    if not name.strip():
                        st.error("Product name is required.")
                    else:
                        execute("UPDATE products SET name=?, category=?, price=?, cost=?, stock=? WHERE id=?",
                                (name.strip(), category.strip() or "General", price, cost, int(stock), int(pid)))
                        st.success("Product updated.")
                        st.rerun()
                if delete:
                    execute("DELETE FROM products WHERE id=?", (int(pid),))
                    st.success("Product deleted.")
                    st.rerun()
        st.divider()
        products = query("SELECT id, name, category, price, cost, stock FROM products ORDER BY name")
        st.markdown("#### All Products")
        st.dataframe(products.rename(columns={
            "id": "ID", "name": "Product", "category": "Category", "price": "Selling Price",
            "cost": "Unit Cost", "stock": "Stock"
        }), use_container_width=True, hide_index=True)
        if not products.empty:
            st.download_button("⬇️ Download Inventory CSV",
                               products.to_csv(index=False).encode("utf-8-sig"),
                               "inventory.csv", "text/csv")

elif page == "Sales & Orders":
    st.subheader("🛒 Create a Sale")
    products = query("SELECT * FROM products WHERE stock > 0 ORDER BY name")
    customers = query("SELECT * FROM customers ORDER BY name")
    if products.empty:
        st.warning("No products are available for sale. Add a product first.")
    else:
        with st.form("new_order"):
            customer_names = ["Walk-in Customer"] + customers["name"].tolist()
            customer_name = st.selectbox("Customer", customer_names)
            selected = st.multiselect("Select Products", products["id"].astype(int).tolist(),
                format_func=lambda pid: products.loc[products["id"] == pid, "name"].iloc[0])
            quantities = {}
            for pid in selected:
                product = products[products["id"] == pid].iloc[0]
                quantities[int(pid)] = st.number_input(
                    f'{product["name"]} | Available: {int(product["stock"])} | Price: {money(product["price"])}',
                    min_value=1, max_value=int(product["stock"]), value=1, key=f"sale_qty_{pid}")
            preview_total = sum(float(products.loc[products["id"] == pid, "price"].iloc[0]) * int(quantities[pid])
                                for pid in selected)
            st.info(f"Order Total: {money(preview_total)}")
            submitted = st.form_submit_button("✅ Save Sale & Deduct Stock", use_container_width=True)
            if submitted:
                if not selected:
                    st.error("Select at least one product.")
                else:
                    try:
                        with connect() as conn:
                            total = 0.0
                            for pid in selected:
                                product = conn.execute("SELECT * FROM products WHERE id=?", (int(pid),)).fetchone()
                                qty = int(quantities[int(pid)])
                                if product is None or product["stock"] < qty:
                                    raise ValueError("Insufficient stock.")
                                total += product["price"] * qty
                            cur = conn.execute(
                                "INSERT INTO orders(customer_name,total,status,created_at) VALUES(?,?,?,?)",
                                (customer_name, total, "Completed", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            order_id = cur.lastrowid
                            for pid in selected:
                                product = conn.execute("SELECT * FROM products WHERE id=?", (int(pid),)).fetchone()
                                qty = int(quantities[int(pid)])
                                conn.execute("""INSERT INTO order_items(order_id,product_id,product_name,qty,price,cost)
                                                 VALUES(?,?,?,?,?,?)""",
                                             (order_id, int(pid), product["name"], qty, product["price"], product["cost"]))
                                conn.execute("UPDATE products SET stock=stock-? WHERE id=?", (qty, int(pid)))
                        st.success(f"Order #{order_id} saved. Total: {money(total)}.")
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))

    st.divider()
    st.subheader("📋 Order History")
    orders = query("SELECT * FROM orders ORDER BY id DESC")
    if orders.empty:
        st.info("No orders have been recorded.")
    else:
        order_id = st.selectbox("Select Order ID", orders["id"].astype(int).tolist())
        order = orders[orders["id"] == order_id].iloc[0]
        st.write(f'**Customer:** {order["customer_name"]}')
        st.write(f'**Total:** {money(order["total"])}')
        st.write(f'**Date:** {order["created_at"]}')
        details = query("""SELECT product_name, qty, price, cost, qty*price AS total
                           FROM order_items WHERE order_id=?""", (int(order_id),))
        st.dataframe(details.rename(columns={
            "product_name": "Product", "qty": "Quantity", "price": "Unit Price",
            "cost": "Unit Cost", "total": "Line Total"
        }), use_container_width=True, hide_index=True)
        invoice = [get_setting("store_name", "PRO STORE"), f"Invoice No.: {order_id}",
                   f'Customer: {order["customer_name"]}', f'Date: {order["created_at"]}', "-" * 35]
        for _, row in details.iterrows():
            invoice.append(f'{row["product_name"]} | Qty: {row["qty"]} | Unit Price: {row["price"]} | Total: {row["total"]}')
        invoice.extend(["-" * 35, f'Grand Total: {money(order["total"])}', "Thank you for shopping with us!"])
        st.download_button("🧾 Download Invoice (TXT)", "\n".join(invoice),
                           f"invoice_{order_id}.txt", "text/plain")

elif page == "Purchases":
    st.subheader("📥 Record a Purchase")
    products = query("SELECT * FROM products ORDER BY name")
    suppliers = query("SELECT * FROM suppliers ORDER BY name")
    if products.empty:
        st.warning("Add products first.")
    else:
        with st.form("new_purchase"):
            supplier_name = st.selectbox("Supplier", ["Unregistered Supplier"] + suppliers["name"].tolist())
            product_id = st.selectbox("Product", products["id"].astype(int).tolist(),
                format_func=lambda pid: products.loc[products["id"] == pid, "name"].iloc[0])
            product = products[products["id"] == product_id].iloc[0]
            qty = st.number_input("Quantity Purchased", min_value=1, value=1)
            cost = st.number_input("Unit Cost", min_value=0.0, value=float(product["cost"]), step=10.0)
            purchase_date = st.date_input("Purchase Date", value=date.today())
            submitted = st.form_submit_button("💾 Save Purchase & Increase Stock", use_container_width=True)
            if submitted:
                total = int(qty) * cost
                with connect() as conn:
                    conn.execute("""INSERT INTO purchases(supplier_name,product_id,product_name,qty,cost,total,created_at)
                                    VALUES(?,?,?,?,?,?,?)""",
                                 (supplier_name, int(product_id), product["name"], int(qty), cost, total, purchase_date.isoformat()))
                    conn.execute("UPDATE products SET stock=stock+?, cost=? WHERE id=?",
                                 (int(qty), cost, int(product_id)))
                st.success(f"Purchase recorded. Total: {money(total)}.")
                st.rerun()
    st.divider()
    st.subheader("Purchase History")
    purchases = query("SELECT * FROM purchases ORDER BY id DESC")
    if purchases.empty:
        st.info("No purchases have been recorded.")
    else:
        st.dataframe(purchases.rename(columns={
            "id": "ID", "supplier_name": "Supplier", "product_name": "Product", "qty": "Quantity",
            "cost": "Unit Cost", "total": "Total", "created_at": "Date", "product_id": "Product ID"
        }), use_container_width=True, hide_index=True)

elif page == "Customers":
    st.subheader("👥 Customer Management")
    with st.form("add_customer", clear_on_submit=True):
        a, b, c = st.columns(3)
        name = a.text_input("Customer Name *")
        phone = b.text_input("Phone Number")
        email = c.text_input("Email Address")
        submitted = st.form_submit_button("➕ Add Customer", use_container_width=True)
        if submitted:
            if not name.strip():
                st.error("Customer name is required.")
            else:
                execute("INSERT INTO customers(name,phone,email,created_at) VALUES(?,?,?,?)",
                        (name.strip(), phone.strip(), email.strip(), today()))
                st.success("Customer added.")
                st.rerun()
    customers = query("SELECT * FROM customers ORDER BY id DESC")
    if customers.empty:
        st.info("There are no registered customers.")
    else:
        st.dataframe(customers.rename(columns={
            "id": "ID", "name": "Name", "phone": "Phone", "email": "Email", "created_at": "Date Added"
        }), use_container_width=True, hide_index=True)
        customer_id = st.selectbox("Select a customer to delete", customers["id"].astype(int).tolist(),
            format_func=lambda cid: customers.loc[customers["id"] == cid, "name"].iloc[0])
        if st.button("🗑️ Delete Customer"):
            execute("DELETE FROM customers WHERE id=?", (int(customer_id),))
            st.success("Customer deleted.")
            st.rerun()

elif page == "Suppliers":
    st.subheader("🚚 Supplier Management")
    with st.form("add_supplier", clear_on_submit=True):
        a, b = st.columns(2)
        name = a.text_input("Supplier Name *")
        company = b.text_input("Company Name")
        c, d = st.columns(2)
        phone = c.text_input("Phone Number")
        address = d.text_input("Address")
        submitted = st.form_submit_button("➕ Add Supplier", use_container_width=True)
        if submitted:
            if not name.strip():
                st.error("Supplier name is required.")
            else:
                execute("INSERT INTO suppliers(name,phone,company,address,created_at) VALUES(?,?,?,?,?)",
                        (name.strip(), phone.strip(), company.strip(), address.strip(), today()))
                st.success("Supplier added.")
                st.rerun()
    suppliers = query("SELECT * FROM suppliers ORDER BY id DESC")
    if suppliers.empty:
        st.info("There are no registered suppliers.")
    else:
        st.dataframe(suppliers.rename(columns={
            "id": "ID", "name": "Supplier", "phone": "Phone", "company": "Company",
            "address": "Address", "created_at": "Date Added"
        }), use_container_width=True, hide_index=True)
        supplier_id = st.selectbox("Select a supplier to delete", suppliers["id"].astype(int).tolist(),
            format_func=lambda sid: suppliers.loc[suppliers["id"] == sid, "name"].iloc[0])
        if st.button("🗑️ Delete Supplier"):
            execute("DELETE FROM suppliers WHERE id=?", (int(supplier_id),))
            st.success("Supplier deleted.")
            st.rerun()

elif page == "Expenses":
    st.subheader("💸 Expense Management")
    with st.form("add_expense", clear_on_submit=True):
        a, b = st.columns(2)
        name = a.text_input("Expense Name *")
        category = b.selectbox("Category", ["Rent", "Salaries", "Utilities", "Shipping & Delivery",
                                             "Maintenance", "Marketing", "Other"])
        amount = st.number_input("Amount", min_value=0.0, step=50.0)
        expense_date = st.date_input("Date", value=date.today())
        submitted = st.form_submit_button("💾 Save Expense", use_container_width=True)
        if submitted:
            if not name.strip():
                st.error("Enter an expense name.")
            elif amount <= 0:
                st.error("The amount must be greater than zero.")
            else:
                execute("INSERT INTO expenses(name,category,amount,created_at) VALUES(?,?,?,?)",
                        (name.strip(), category, amount, expense_date.isoformat()))
                st.success("Expense saved.")
                st.rerun()
    expenses = query("SELECT * FROM expenses ORDER BY id DESC")
    if expenses.empty:
        st.info("There are no expenses.")
    else:
        st.metric("Total Expenses", money(expenses["amount"].sum()))
        st.dataframe(expenses.rename(columns={
            "id": "ID", "name": "Expense", "category": "Category", "amount": "Amount", "created_at": "Date"
        }), use_container_width=True, hide_index=True)
        expense_id = st.selectbox("Select an expense to delete", expenses["id"].astype(int).tolist(),
            format_func=lambda eid: expenses.loc[expenses["id"] == eid, "name"].iloc[0])
        if st.button("🗑️ Delete Expense"):
            execute("DELETE FROM expenses WHERE id=?", (int(expense_id),))
            st.success("Expense deleted.")
            st.rerun()

elif page == "Reports":
    st.subheader("📈 Reports & Analytics")
    a, b = st.columns(2)
    start_date = a.date_input("Start Date", value=date.today() - timedelta(days=30))
    end_date = b.date_input("End Date", value=date.today())
    if start_date > end_date:
        st.error("The start date must be on or before the end date.")
    else:
        params = (start_date.isoformat(), end_date.isoformat())
        orders = query("SELECT * FROM orders WHERE date(created_at) BETWEEN ? AND ? ORDER BY created_at DESC", params)
        purchases = query("SELECT * FROM purchases WHERE date(created_at) BETWEEN ? AND ?", params)
        expenses = query("SELECT * FROM expenses WHERE date(created_at) BETWEEN ? AND ?", params)
        items = query("""SELECT oi.qty, oi.cost FROM order_items oi JOIN orders o ON o.id=oi.order_id
                         WHERE date(o.created_at) BETWEEN ? AND ?""", params)
        revenue = float(orders["total"].sum()) if not orders.empty else 0
        purchase_total = float(purchases["total"].sum()) if not purchases.empty else 0
        expense_total = float(expenses["amount"].sum()) if not expenses.empty else 0
        cost_sold = float((items["qty"] * items["cost"]).sum()) if not items.empty else 0
        a, b, c, d = st.columns(4)
        a.metric("Sales Revenue", money(revenue))
        b.metric("Cost of Goods Sold", money(cost_sold))
        c.metric("Purchases", money(purchase_total))
        d.metric("Expenses", money(expense_total))
        st.metric("Estimated Net Profit", money(revenue - cost_sold - expense_total))
        if not orders.empty:
            chart_orders = orders.copy()
            chart_orders["Date"] = pd.to_datetime(chart_orders["created_at"]).dt.strftime("%Y-%m-%d")
            daily = chart_orders.groupby("Date", as_index=False)["total"].sum()
            fig = px.line(daily, x="Date", y="total", markers=True, title="Daily Sales",
                          labels={"Date": "Date", "total": "Sales"})
            st.plotly_chart(fig, use_container_width=True)
            top = query("""SELECT product_name AS Product, SUM(qty) AS Quantity,
                           SUM(qty*price) AS Sales FROM order_items oi
                           JOIN orders o ON o.id=oi.order_id
                           WHERE date(o.created_at) BETWEEN ? AND ?
                           GROUP BY product_name ORDER BY Quantity DESC LIMIT 10""", params)
            if not top.empty:
                fig = px.bar(top, x="Product", y="Quantity", color="Sales", title="Best-Selling Products")
                st.plotly_chart(fig, use_container_width=True)
            st.dataframe(orders.rename(columns={
                "id": "Order ID", "customer_name": "Customer", "total": "Total",
                "status": "Status", "created_at": "Date"
            }), use_container_width=True, hide_index=True)
        else:
            st.info("There are no sales in the selected date range.")
        st.download_button("⬇️ Download Sales Report (CSV)",
                           orders.to_csv(index=False).encode("utf-8-sig"),
                           "sales_report.csv", "text/csv")

elif page == "Settings":
    st.subheader("⚙️ Store Settings")
    with st.form("settings"):
        name = st.text_input("Store Name", value=get_setting("store_name", "PRO STORE"))
        currencies = ["EGP", "SAR", "AED", "USD"]
        current_currency = get_setting("currency", "EGP")
        currency_index = currencies.index(current_currency) if current_currency in currencies else 0
        selected_currency = st.selectbox("Currency", currencies, index=currency_index)
        low_stock = st.number_input("Low-Stock Alert Threshold", min_value=0,
                                    value=int(get_setting("low_stock", "5")), step=1)
        submitted = st.form_submit_button("💾 Save Settings", use_container_width=True)
        if submitted:
            save_setting("store_name", name.strip() or "PRO STORE")
            save_setting("currency", selected_currency)
            save_setting("low_stock", int(low_stock))
            st.success("Settings saved.")
            st.rerun()
    st.divider()
    st.subheader("💾 Database Backup")
    st.write("The database is stored locally in the `pro_store.db` file inside the project folder.")
    if DB.exists():
        st.download_button("⬇️ Download Database Backup", DB.read_bytes(),
                           f"pro_store_backup_{today()}.db", "application/octet-stream")
    st.warning("Keep a backup of your database. This version stores data locally on this computer.")

st.divider()
st.caption("PRO STORE | Store Management System")
