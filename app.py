
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
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Cairo', sans-serif;
}
.stApp {
    background: #f4f6fa;
}
.block-container {
    padding-top: 1.5rem;
    max-width: 1500px;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #14213d, #203d66);
}
section[data-testid="stSidebar"] * {
    color: white !important;
}
.hero {
    background: linear-gradient(120deg, #14213d, #2874b8);
    padding: 25px;
    border-radius: 18px;
    color: white;
    margin-bottom: 22px;
}
.hero h1 {
    color: white;
    margin: 0;
    font-weight: 800;
}
.hero p {
    margin-bottom: 0;
    opacity: .9;
}
div[data-testid="stMetric"] {
    background: white;
    padding: 17px;
    border-radius: 15px;
    border: 1px solid #e3e8f0;
    box-shadow: 0 4px 14px #14213d0a;
}
h2, h3 {
    color: #14213d;
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
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'عام',
            price REAL NOT NULL DEFAULT 0,
            cost REAL NOT NULL DEFAULT 0,
            stock INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            company TEXT DEFAULT '',
            address TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'مكتمل',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            qty INTEGER NOT NULL,
            price REAL NOT NULL,
            cost REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name TEXT NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            qty INTEGER NOT NULL,
            cost REAL NOT NULL,
            total REAL NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT NOT NULL
        );
        """)

        defaults = {
            "store_name": "PRO STORE",
            "currency": "ج.م",
            "low_stock": "5"
        }

        for key, value in defaults.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",
                (key, value)
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
        row = conn.execute(
            "SELECT value FROM settings WHERE key=?",
            (key,)
        ).fetchone()
        return row["value"] if row else default


def save_setting(key, value):
    with connect() as conn:
        conn.execute("""
            INSERT INTO settings(key,value) VALUES(?,?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """, (key, str(value)))


def currency():
    return get_setting("currency", "ج.م")


def money(value):
    return f"{float(value):,.2f} {currency()}"


def today():
    return date.today().isoformat()


init_db()

store_name = get_setting("store_name", "PRO STORE")

with st.sidebar:
    st.markdown(
        "<div style='text-align:center;padding:15px 0'>"
        "<div style='font-size:48px'>🛍️</div>"
        "<div style='font-size:25px;font-weight:800'>PRO STORE</div>"
        "<div style='font-size:12px'>نظام إدارة المتجر</div></div>",
        unsafe_allow_html=True
    )

    page = st.radio("القائمة الرئيسية", [
        "لوحة التحكم",
        "المنتجات والمخزون",
        "المبيعات والطلبات",
        "المشتريات",
        "العملاء",
        "الموردون",
        "المصروفات",
        "التقارير",
        "الإعدادات"
    ])

    st.divider()
    st.caption("الإصدار المحلي")
    if st.button("🔄 تحديث البيانات", use_container_width=True):
        st.rerun()


st.markdown(
    f"<div class='hero'><h1>{store_name}</h1>"
    "<p>إدارة المبيعات والمخزون والمشتريات من مكان واحد</p></div>",
    unsafe_allow_html=True
)


if page == "لوحة التحكم":

    products = query("SELECT * FROM products")
    orders = query("SELECT * FROM orders")
    purchases = query("SELECT * FROM purchases")
    expenses = query("SELECT * FROM expenses")
    items = query("SELECT qty,cost FROM order_items")

    revenue = float(orders["total"].sum()) if not orders.empty else 0
    purchase_total = float(purchases["total"].sum()) if not purchases.empty else 0
    expense_total = float(expenses["amount"].sum()) if not expenses.empty else 0
    cost_sold = float((items["qty"] * items["cost"]).sum()) if not items.empty else 0
    profit = revenue - cost_sold - expense_total
    inventory_value = float((products["stock"] * products["cost"]).sum()) if not products.empty else 0

    limit = int(get_setting("low_stock", "5"))
    low_stock = products[products["stock"] <= limit] if not products.empty else pd.DataFrame()

    a, b, c, d = st.columns(4)
    a.metric("💰 إجمالي المبيعات", money(revenue))
    b.metric("📈 صافي الربح التقديري", money(profit))
    c.metric("📦 عدد المنتجات", len(products))
    d.metric("⚠️ مخزون منخفض", len(low_stock))

    left, right = st.columns([1.6, 1])

    with left:
        st.subheader("📊 المبيعات اليومية")

        if not orders.empty:
            chart_data = orders.copy()
            chart_data["اليوم"] = pd.to_datetime(
                chart_data["created_at"]
            ).dt.strftime("%Y-%m-%d")

            chart_data = chart_data[
                pd.to_datetime(chart_data["created_at"]) >=
                pd.Timestamp(date.today() - timedelta(days=6))
            ]

            daily = chart_data.groupby(
                "اليوم", as_index=False
            )["total"].sum()

            if not daily.empty:
                fig = px.bar(
                    daily,
                    x="اليوم",
                    y="total",
                    text_auto=".2s",
                    color_discrete_sequence=["#2874b8"]
                )
                fig.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    margin=dict(l=10, r=10, t=20, b=10)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("لا توجد مبيعات خلال آخر 7 أيام.")
        else:
            st.info("سجّل أول عملية بيع لعرض الرسم البياني.")

    with right:
        st.subheader("🧾 الملخص المالي")
        st.metric("إجمالي المشتريات", money(purchase_total))
        st.metric("إجمالي المصروفات", money(expense_total))
        st.metric("قيمة المخزون", money(inventory_value))

    st.subheader("⚠️ تنبيهات المخزون")

    if low_stock.empty:
        st.success("لا توجد منتجات منخفضة المخزون.")
    else:
        st.dataframe(
            low_stock[["name", "category", "stock", "price"]].rename(
                columns={
                    "name": "المنتج",
                    "category": "التصنيف",
                    "stock": "الكمية",
                    "price": "سعر البيع"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

    st.subheader("🕘 أحدث الطلبات")
    recent = query("""
        SELECT id,customer_name,total,status,created_at
        FROM orders ORDER BY id DESC LIMIT 10
    """)

    if recent.empty:
        st.info("لا توجد طلبات مسجلة.")
    else:
        st.dataframe(
            recent.rename(columns={
                "id": "رقم الطلب",
                "customer_name": "العميل",
                "total": "الإجمالي",
                "status": "الحالة",
                "created_at": "التاريخ"
            }),
            use_container_width=True,
            hide_index=True
        )


elif page == "المنتجات والمخزون":

    st.subheader("📦 المنتجات والمخزون")
    tab1, tab2 = st.tabs(["إضافة منتج", "إدارة المنتجات"])

    with tab1:
        with st.form("add_product", clear_on_submit=True):
            a, b = st.columns(2)
            name = a.text_input("اسم المنتج *")
            category = b.text_input("التصنيف", value="عام")

            c, d, e = st.columns(3)
            price = c.number_input("سعر البيع", min_value=0.0, step=10.0)
            cost = d.number_input("سعر التكلفة", min_value=0.0, step=10.0)
            stock = e.number_input("الكمية الافتتاحية", min_value=0, step=1)

            submitted = st.form_submit_button(
                "➕ حفظ المنتج",
                use_container_width=True
            )

            if submitted:
                if not name.strip():
                    st.error("اكتب اسم المنتج.")
                else:
                    execute("""
                        INSERT INTO products(name,category,price,cost,stock,created_at)
                        VALUES(?,?,?,?,?,?)
                    """, (
                        name.strip(),
                        category.strip() or "عام",
                        price,
                        cost,
                        int(stock),
                        today()
                    ))
                    st.success("تمت إضافة المنتج.")
                    st.rerun()

    with tab2:
        products = query("SELECT * FROM products ORDER BY id DESC")

        if products.empty:
            st.info("لا توجد منتجات.")
        else:
            labels = {
                int(r["id"]): f'{r["name"]} — #{r["id"]}'
                for _, r in products.iterrows()
            }

            pid = st.selectbox(
                "اختر المنتج للتعديل أو الحذف",
                list(labels.keys()),
                format_func=lambda x: labels[x]
            )

            row = products[products["id"] == pid].iloc[0]

            with st.form("edit_product"):
                a, b = st.columns(2)
                name = a.text_input("اسم المنتج", value=str(row["name"]))
                category = b.text_input("التصنيف", value=str(row["category"]))

                c, d, e = st.columns(3)
                price = c.number_input(
                    "سعر البيع",
                    min_value=0.0,
                    value=float(row["price"]),
                    step=10.0
                )
                cost = d.number_input(
                    "التكلفة",
                    min_value=0.0,
                    value=float(row["cost"]),
                    step=10.0
                )
                stock = e.number_input(
                    "المخزون",
                    min_value=0,
                    value=int(row["stock"]),
                    step=1
                )

                save = st.form_submit_button("💾 حفظ التعديلات")
                delete = st.form_submit_button("🗑️ حذف المنتج")

                if save:
                    if not name.strip():
                        st.error("اسم المنتج مطلوب.")
                    else:
                        execute("""
                            UPDATE products
                            SET name=?,category=?,price=?,cost=?,stock=?
                            WHERE id=?
                        """, (
                            name.strip(),
                            category.strip() or "عام",
                            price,
                            cost,
                            int(stock),
                            int(pid)
                        ))
                        st.success("تم تحديث المنتج.")
                        st.rerun()

                if delete:
                    execute("DELETE FROM products WHERE id=?", (int(pid),))
                    st.success("تم حذف المنتج.")
                    st.rerun()

        st.divider()
        products = query("""
            SELECT id,name,category,price,cost,stock
            FROM products ORDER BY name
        """)

        st.markdown("#### جميع المنتجات")
        st.dataframe(
            products.rename(columns={
                "id": "رقم",
                "name": "المنتج",
                "category": "التصنيف",
                "price": "سعر البيع",
                "cost": "التكلفة",
                "stock": "المخزون"
            }),
            use_container_width=True,
            hide_index=True
        )

        if not products.empty:
            st.download_button(
                "⬇️ تنزيل المخزون CSV",
                products.to_csv(index=False).encode("utf-8-sig"),
                "inventory.csv",
                "text/csv"
            )


elif page == "المبيعات والطلبات":

    st.subheader("🛒 إنشاء عملية بيع")
    products = query("SELECT * FROM products WHERE stock > 0 ORDER BY name")
    customers = query("SELECT * FROM customers ORDER BY name")

    if products.empty:
        st.warning("لا توجد منتجات متاحة للبيع. أضف منتجًا أولًا.")
    else:
        with st.form("new_order"):
            customer_names = ["عميل نقدي"] + customers["name"].tolist()
            customer_name = st.selectbox("العميل", customer_names)

            selected = st.multiselect(
                "اختر المنتجات",
                products["id"].astype(int).tolist(),
                format_func=lambda pid: products.loc[
                    products["id"] == pid, "name"
                ].iloc[0]
            )

            quantities = {}

            for pid in selected:
                product = products[products["id"] == pid].iloc[0]
                quantities[int(pid)] = st.number_input(
                    f'{product["name"]} | المتاح {int(product["stock"])} | السعر {money(product["price"])}',
                    min_value=1,
                    max_value=int(product["stock"]),
                    value=1,
                    key=f"sale_qty_{pid}"
                )

            preview_total = sum(
                float(products.loc[products["id"] == pid, "price"].iloc[0])
                * int(quantities[pid])
                for pid in selected
            )

            st.info(f"إجمالي الطلب: {money(preview_total)}")

            submitted = st.form_submit_button(
                "✅ حفظ البيع وخصم المخزون",
                use_container_width=True
            )

            if submitted:
                if not selected:
                    st.error("اختر منتجًا واحدًا على الأقل.")
                else:
                    try:
                        with connect() as conn:
                            total = 0.0

                            for pid in selected:
                                product = conn.execute(
                                    "SELECT * FROM products WHERE id=?",
                                    (int(pid),)
                                ).fetchone()

                                qty = int(quantities[int(pid)])

                                if product is None or product["stock"] < qty:
                                    raise ValueError("الكمية المتاحة غير كافية.")

                                total += product["price"] * qty

                            cur = conn.execute("""
                                INSERT INTO orders(customer_name,total,status,created_at)
                                VALUES(?,?,?,?)
                            """, (
                                customer_name,
                                total,
                                "مكتمل",
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ))

                            order_id = cur.lastrowid

                            for pid in selected:
                                product = conn.execute(
                                    "SELECT * FROM products WHERE id=?",
                                    (int(pid),)
                                ).fetchone()

                                qty = int(quantities[int(pid)])

                                conn.execute("""
                                    INSERT INTO order_items
                                    (order_id,product_id,product_name,qty,price,cost)
                                    VALUES(?,?,?,?,?,?)
                                """, (
                                    order_id,
                                    int(pid),
                                    product["name"],
                                    qty,
                                    product["price"],
                                    product["cost"]
                                ))

                                conn.execute(
                                    "UPDATE products SET stock=stock-? WHERE id=?",
                                    (qty, int(pid))
                                )

                        st.success(
                            f"تم حفظ الطلب رقم #{order_id} بإجمالي {money(total)}."
                        )
                        st.rerun()

                    except ValueError as error:
                        st.error(str(error))

    st.divider()
    st.subheader("📋 سجل الطلبات")

    orders = query("SELECT * FROM orders ORDER BY id DESC")

    if orders.empty:
        st.info("لا توجد طلبات حتى الآن.")
    else:
        order_id = st.selectbox(
            "اختر رقم الطلب",
            orders["id"].astype(int).tolist()
        )

        order = orders[orders["id"] == order_id].iloc[0]

        st.write(f'**العميل:** {order["customer_name"]}')
        st.write(f'**الإجمالي:** {money(order["total"])}')
        st.write(f'**التاريخ:** {order["created_at"]}')

        details = query("""
            SELECT product_name,qty,price,cost,qty*price AS total
            FROM order_items WHERE order_id=?
        """, (int(order_id),))

        st.dataframe(
            details.rename(columns={
                "product_name": "المنتج",
                "qty": "الكمية",
                "price": "سعر الوحدة",
                "cost": "التكلفة",
                "total": "الإجمالي"
            }),
            use_container_width=True,
            hide_index=True
        )

        invoice = [
            get_setting("store_name", "PRO STORE"),
            f"فاتورة رقم: {order_id}",
            f'العميل: {order["customer_name"]}',
            f'التاريخ: {order["created_at"]}',
            "-" * 35
        ]

        for _, row in details.iterrows():
            invoice.append(
                f'{row["product_name"]} | الكمية: {row["qty"]} | '
                f'السعر: {row["price"]} | الإجمالي: {row["total"]}'
            )

        invoice.extend([
            "-" * 35,
            f'الإجمالي النهائي: {money(order["total"])}',
            "شكرًا لتعاملكم معنا"
        ])

        st.download_button(
            "🧾 تنزيل الفاتورة TXT",
            "\n".join(invoice),
            f"invoice_{order_id}.txt",
            "text/plain"
        )


elif page == "المشتريات":

    st.subheader("📥 تسجيل المشتريات")
    products = query("SELECT * FROM products ORDER BY name")
    suppliers = query("SELECT * FROM suppliers ORDER BY name")

    if products.empty:
        st.warning("أضف المنتجات أولًا.")
    else:
        with st.form("new_purchase"):
            supplier_names = ["مورد غير مسجل"] + suppliers["name"].tolist()
            supplier_name = st.selectbox("المورد", supplier_names)

            product_id = st.selectbox(
                "المنتج",
                products["id"].astype(int).tolist(),
                format_func=lambda pid: products.loc[
                    products["id"] == pid, "name"
                ].iloc[0]
            )

            product = products[products["id"] == product_id].iloc[0]

            qty = st.number_input("الكمية المشتراة", min_value=1, value=1)
            cost = st.number_input(
                "تكلفة الوحدة",
                min_value=0.0,
                value=float(product["cost"]),
                step=10.0
            )
            purchase_date = st.date_input("تاريخ الشراء", value=date.today())

            submitted = st.form_submit_button(
                "💾 حفظ المشتريات وزيادة المخزون",
                use_container_width=True
            )

            if submitted:
                total = int(qty) * cost

                with connect() as conn:
                    conn.execute("""
                        INSERT INTO purchases
                        (supplier_name,product_id,product_name,qty,cost,total,created_at)
                        VALUES(?,?,?,?,?,?,?)
                    """, (
                        supplier_name,
                        int(product_id),
                        product["name"],
                        int(qty),
                        cost,
                        total,
                        purchase_date.isoformat()
                    ))

                    conn.execute("""
                        UPDATE products
                        SET stock=stock+?,cost=?
                        WHERE id=?
                    """, (int(qty), cost, int(product_id)))

                st.success(f"تم تسجيل المشتريات بقيمة {money(total)}.")
                st.rerun()

    st.divider()
    st.subheader("سجل المشتريات")

    purchases = query("SELECT * FROM purchases ORDER BY id DESC")

    if purchases.empty:
        st.info("لا توجد مشتريات مسجلة.")
    else:
        st.dataframe(
            purchases.rename(columns={
                "id": "رقم",
                "supplier_name": "المورد",
                "product_name": "المنتج",
                "qty": "الكمية",
                "cost": "تكلفة الوحدة",
                "total": "الإجمالي",
                "created_at": "التاريخ",
                "product_id": "رقم المنتج"
            }),
            use_container_width=True,
            hide_index=True
        )


elif page == "العملاء":

    st.subheader("👥 إدارة العملاء")

    with st.form("add_customer", clear_on_submit=True):
        a, b, c = st.columns(3)
        name = a.text_input("اسم العميل *")
        phone = b.text_input("رقم الهاتف")
        email = c.text_input("البريد الإلكتروني")

        submitted = st.form_submit_button(
            "➕ إضافة العميل",
            use_container_width=True
        )

        if submitted:
            if not name.strip():
                st.error("اسم العميل مطلوب.")
            else:
                execute("""
                    INSERT INTO customers(name,phone,email,created_at)
                    VALUES(?,?,?,?)
                """, (name.strip(), phone.strip(), email.strip(), today()))

                st.success("تمت إضافة العميل.")
                st.rerun()

    customers = query("SELECT * FROM customers ORDER BY id DESC")

    if customers.empty:
        st.info("لا يوجد عملاء مسجلون.")
    else:
        st.dataframe(
            customers.rename(columns={
                "id": "رقم",
                "name": "الاسم",
                "phone": "الهاتف",
                "email": "البريد الإلكتروني",
                "created_at": "تاريخ الإضافة"
            }),
            use_container_width=True,
            hide_index=True
        )

        customer_id = st.selectbox(
            "اختر عميلًا للحذف",
            customers["id"].astype(int).tolist(),
            format_func=lambda cid: customers.loc[
                customers["id"] == cid, "name"
            ].iloc[0]
        )

        if st.button("🗑️ حذف العميل"):
            execute("DELETE FROM customers WHERE id=?", (int(customer_id),))
            st.success("تم حذف العميل.")
            st.rerun()


elif page == "الموردون":

    st.subheader("🚚 إدارة الموردين")

    with st.form("add_supplier", clear_on_submit=True):
        a, b = st.columns(2)
        name = a.text_input("اسم المورد *")
        company = b.text_input("اسم الشركة")

        c, d = st.columns(2)
        phone = c.text_input("رقم الهاتف")
        address = d.text_input("العنوان")

        submitted = st.form_submit_button(
            "➕ إضافة المورد",
            use_container_width=True
        )

        if submitted:
            if not name.strip():
                st.error("اسم المورد مطلوب.")
            else:
                execute("""
                    INSERT INTO suppliers(name,phone,company,address,created_at)
                    VALUES(?,?,?,?,?)
                """, (
                    name.strip(),
                    phone.strip(),
                    company.strip(),
                    address.strip(),
                    today()
                ))

                st.success("تمت إضافة المورد.")
                st.rerun()

    suppliers = query("SELECT * FROM suppliers ORDER BY id DESC")

    if suppliers.empty:
        st.info("لا يوجد موردون مسجلون.")
    else:
        st.dataframe(
            suppliers.rename(columns={
                "id": "رقم",
                "name": "المورد",
                "phone": "الهاتف",
                "company": "الشركة",
                "address": "العنوان",
                "created_at": "تاريخ الإضافة"
            }),
            use_container_width=True,
            hide_index=True
        )

        supplier_id = st.selectbox(
            "اختر موردًا للحذف",
            suppliers["id"].astype(int).tolist(),
            format_func=lambda sid: suppliers.loc[
                suppliers["id"] == sid, "name"
            ].iloc[0]
        )

        if st.button("🗑️ حذف المورد"):
            execute("DELETE FROM suppliers WHERE id=?", (int(supplier_id),))
            st.success("تم حذف المورد.")
            st.rerun()


elif page == "المصروفات":

    st.subheader("💸 إدارة المصروفات")

    with st.form("add_expense", clear_on_submit=True):
        a, b = st.columns(2)
        name = a.text_input("اسم المصروف *")
        category = b.selectbox(
            "التصنيف",
            ["إيجار", "رواتب", "كهرباء ومياه", "شحن وتوصيل", "صيانة", "تسويق", "أخرى"]
        )

        amount = st.number_input("المبلغ", min_value=0.0, step=50.0)
        expense_date = st.date_input("التاريخ", value=date.today())

        submitted = st.form_submit_button(
            "💾 حفظ المصروف",
            use_container_width=True
        )

        if submitted:
            if not name.strip():
                st.error("اكتب اسم المصروف.")
            elif amount <= 0:
                st.error("المبلغ يجب أن يكون أكبر من صفر.")
            else:
                execute("""
                    INSERT INTO expenses(name,category,amount,created_at)
                    VALUES(?,?,?,?)
                """, (
                    name.strip(),
                    category,
                    amount,
                    expense_date.isoformat()
                ))

                st.success("تم حفظ المصروف.")
                st.rerun()

    expenses = query("SELECT * FROM expenses ORDER BY id DESC")

    if expenses.empty:
        st.info("لا توجد مصروفات.")
    else:
        st.metric("إجمالي المصروفات", money(expenses["amount"].sum()))

        st.dataframe(
            expenses.rename(columns={
                "id": "رقم",
                "name": "المصروف",
                "category": "التصنيف",
                "amount": "المبلغ",
                "created_at": "التاريخ"
            }),
            use_container_width=True,
            hide_index=True
        )

        expense_id = st.selectbox(
            "اختر مصروفًا للحذف",
            expenses["id"].astype(int).tolist(),
            format_func=lambda eid: expenses.loc[
                expenses["id"] == eid, "name"
            ].iloc[0]
        )

        if st.button("🗑️ حذف المصروف"):
            execute("DELETE FROM expenses WHERE id=?", (int(expense_id),))
            st.success("تم حذف المصروف.")
            st.rerun()


elif page == "التقارير":

    st.subheader("📈 التقارير والتحليلات")

    a, b = st.columns(2)
    start_date = a.date_input(
        "من تاريخ",
        value=date.today() - timedelta(days=30)
    )
    end_date = b.date_input("إلى تاريخ", value=date.today())

    if start_date > end_date:
        st.error("تاريخ البداية يجب أن يسبق تاريخ النهاية.")
    else:
        orders = query("""
            SELECT * FROM orders
            WHERE date(created_at) BETWEEN ? AND ?
            ORDER BY created_at DESC
        """, (start_date.isoformat(), end_date.isoformat()))

        purchases = query("""
            SELECT * FROM purchases
            WHERE date(created_at) BETWEEN ? AND ?
        """, (start_date.isoformat(), end_date.isoformat()))

        expenses = query("""
            SELECT * FROM expenses
            WHERE date(created_at) BETWEEN ? AND ?
        """, (start_date.isoformat(), end_date.isoformat()))

        items = query("""
            SELECT oi.qty,oi.cost
            FROM order_items oi
            JOIN orders o ON o.id=oi.order_id
            WHERE date(o.created_at) BETWEEN ? AND ?
        """, (start_date.isoformat(), end_date.isoformat()))

        revenue = float(orders["total"].sum()) if not orders.empty else 0
        purchase_total = float(purchases["total"].sum()) if not purchases.empty else 0
        expense_total = float(expenses["amount"].sum()) if not expenses.empty else 0
        cost_sold = float((items["qty"] * items["cost"]).sum()) if not items.empty else 0

        a, b, c, d = st.columns(4)
        a.metric("المبيعات", money(revenue))
        b.metric("تكلفة البضاعة المباعة", money(cost_sold))
        c.metric("المشتريات", money(purchase_total))
        d.metric("المصروفات", money(expense_total))

        st.metric(
            "صافي الربح التقديري",
            money(revenue - cost_sold - expense_total)
        )

        if not orders.empty:
            chart_orders = orders.copy()
            chart_orders["اليوم"] = pd.to_datetime(
                chart_orders["created_at"]
            ).dt.strftime("%Y-%m-%d")

            daily = chart_orders.groupby(
                "اليوم", as_index=False
            )["total"].sum()

            fig = px.line(
                daily,
                x="اليوم",
                y="total",
                markers=True,
                title="المبيعات اليومية",
                labels={"اليوم": "التاريخ", "total": "المبيعات"}
            )

            st.plotly_chart(fig, use_container_width=True)

            top = query("""
                SELECT product_name AS المنتج,
                       SUM(qty) AS الكمية,
                       SUM(qty*price) AS المبيعات
                FROM order_items oi
                JOIN orders o ON o.id=oi.order_id
                WHERE date(o.created_at) BETWEEN ? AND ?
                GROUP BY product_name
                ORDER BY الكمية DESC
                LIMIT 10
            """, (start_date.isoformat(), end_date.isoformat()))

            if not top.empty:
                fig = px.bar(
                    top,
                    x="المنتج",
                    y="الكمية",
                    color="المبيعات",
                    title="أكثر المنتجات مبيعًا"
                )
                st.plotly_chart(fig, use_container_width=True)

            st.dataframe(
                orders.rename(columns={
                    "id": "رقم الطلب",
                    "customer_name": "العميل",
                    "total": "الإجمالي",
                    "status": "الحالة",
                    "created_at": "التاريخ"
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("لا توجد مبيعات في الفترة المحددة.")

        st.download_button(
            "⬇️ تنزيل تقرير المبيعات CSV",
            orders.to_csv(index=False).encode("utf-8-sig"),
            "sales_report.csv",
            "text/csv"
        )


elif page == "الإعدادات":

    st.subheader("⚙️ إعدادات المتجر")

    with st.form("settings"):
        name = st.text_input(
            "اسم المتجر",
            value=get_setting("store_name", "PRO STORE")
        )

        currencies = ["ج.م", "SAR", "AED", "USD"]
        current_currency = get_setting("currency", "ج.م")

        currency_index = (
            currencies.index(current_currency)
            if current_currency in currencies else 0
        )

        selected_currency = st.selectbox(
            "العملة",
            currencies,
            index=currency_index
        )

        low_stock = st.number_input(
            "حد تنبيه المخزون المنخفض",
            min_value=0,
            value=int(get_setting("low_stock", "5")),
            step=1
        )

        submitted = st.form_submit_button(
            "💾 حفظ الإعدادات",
            use_container_width=True
        )

        if submitted:
            save_setting("store_name", name.strip() or "PRO STORE")
            save_setting("currency", selected_currency)
            save_setting("low_stock", int(low_stock))
            st.success("تم حفظ الإعدادات.")
            st.rerun()

    st.divider()
    st.subheader("💾 النسخ الاحتياطي")

    st.write("تُحفظ قاعدة البيانات في الملف `pro_store.db` داخل مجلد المشروع.")

    if DB.exists():
        st.download_button(
            "⬇️ تنزيل نسخة احتياطية",
            DB.read_bytes(),
            f"pro_store_backup_{today()}.db",
            "application/octet-stream"
        )

    st.warning(
        "احتفظ بنسخة احتياطية من قاعدة البيانات. "
        "هذه النسخة تحفظ البيانات محليًا على جهازك."
    )


st.divider()
st.caption("PRO STORE | نظام إدارة المتجر")

