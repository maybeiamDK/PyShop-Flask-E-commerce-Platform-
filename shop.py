#Імпорт необхідних бібліотек та модулів
from flask import Flask, render_template, url_for, request, redirect, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
from collections import defaultdict
from cloudipsp import Api, Checkout
import os

#Шлях до папки для збереження зображень товарів та дозволені розширення файлів
UPLOAD_FOLDER = 'static/uploads/images'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

#Ініціалізація додатку
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SECRET_KEY'] = 'e9b1c9a8d9f4b8e6f6a5d8e7c1b2a3d4'
db = SQLAlchemy(app)
app.app_context().push()

#Конфігурація поштового сервера
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'daniilkolesnichenko01@gmail.com'
app.config['MAIL_PASSWORD'] = 'tlyt yigw eplt xwzn'
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'

mail = Mail(app)

#Модель користувача, таблиця User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.id

#Модель товару, таблиця Item
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=False)
    sub_category = db.Column(db.String(100), nullable=True)
    size = db.Column(db.String(50), nullable=True)
    amount = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'<Item {self.name} ({self.brand})>'

#Модель замовлення, таблиця Order
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Pending")  #Статус: Pending, Shipped, Delivered

    items = db.relationship('OrderItem', backref='order', lazy=True)

    def __repr__(self):
        return f'<Order {self.id} - {self.status}>'

#Модель товару в замовленні, таблиця OrderItem
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_at_purchase = db.Column(db.Float, nullable=False)

    item = db.relationship('Item', backref='order_items')

    def __repr__(self):
        return f'<OrderItem {self.item.name} (x{self.quantity})>'


#Головна сторінка
@app.route('/')
@app.route('/home')
def index():
    user = None

    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    return render_template('index.html', user = user)

#Сторінка з товарами категорії взуття
@app.route('/shoes')
def shoes():
    user = None

    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    sub_category = request.args.get('sub_category')
    size = request.args.get('size')

    query = Item.query.filter_by(category = 'shoes')
    
    #Фільтрація за підкатегорією та розміром
    if sub_category:
        query = query.filter_by(sub_category = sub_category)
    if size:
        query = query.filter_by(size = size)

    items = query.all()

    #Групування товарів для уникнення дублікатів з різними розмірами
    grouped = {}
    grouped_items = defaultdict(lambda: {'item': None, 'sizes': []})
    for item in items:
        key = (item.name, item.brand)
        if key not in grouped:
            grouped[key] = {
                'item': item,
                'sizes': [item.size]
            }
        else:
            grouped[key]['sizes'].append(item.size)

    #Перетворення словника на список для передачі у шаблон
    items = list(grouped.values())

    #Варіанти підкатегорій та розмірів
    sub_categories = ["sneakers", "boots", "open shoes"]
    sizes = ["32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46"]

    return render_template('shoes.html', user = user, items = items, sub_categories = sub_categories, sizes = sizes, selected_sub = sub_category, selected_size = size)

#Сторінка з товарами категорії одягу
@app.route('/clothing')
def clothing():
    user = None

    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    sub_category = request.args.get('sub_category')
    size = request.args.get('size')

    query = Item.query.filter_by(category = 'clothing')

    #Фільтрація за підкатегорією та розміром
    if sub_category:
        query = query.filter_by(sub_category = sub_category)
    if size:
        query = query.filter_by(size = size)

    items = query.all()

    #Групування товарів для уникнення дублікатів з різними розмірами
    grouped = {}
    grouped_items = defaultdict(lambda: {'item': None, 'sizes': []})
    for item in items:
        key = (item.name, item.brand)
        if key not in grouped:
            grouped[key] = {
                'item': item,
                'sizes': [item.size]
            }
        else:
            grouped[key]['sizes'].append(item.size)

    #Перетворення словника на список для передачі у шаблон
    items = list(grouped.values())

    #Варіанти підкатегорій та розмірів
    sub_categories = ["outerwear", "sweatshirts", "sweater", "denim", "trousers", "t-shirts", "shorts"]
    sizes = ["XS", "S", "M", "L", "XL", "XXL"]

    return render_template('clothing.html', user = user, items=items, sub_categories=sub_categories, sizes=sizes, selected_sub=sub_category, selected_size=size)

#Сторінка з товарами категорії аксесуарів
@app.route('/accessories') 
def accessories():
    user = None

    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    sub_category = request.args.get('sub_category')
    size = request.args.get('size')

    query = Item.query.filter_by(category = 'accessories')

    #Фільтрація за підкатегорією та розміром
    if sub_category:
        query = query.filter_by(sub_category = sub_category)
    if size:
        query = query.filter_by(size = size)

    items = query.all()

    #Групування товарів для уникнення дублікатів з різними розмірами
    grouped = {}
    grouped_items = defaultdict(lambda: {'item': None, 'sizes': []})
    for item in items:
        key = (item.name, item.brand)
        if key not in grouped:
            grouped[key] = {
                'item': item,
                'sizes': [item.size]
            }
        else:
            grouped[key]['sizes'].append(item.size)

    #Перетворення словника на список для передачі у шаблон
    items = list(grouped.values())

    #Варіанти підкатегорій та розмірів
    sub_categories = ["hats", "skarves", "glasses", "rings", "bags", "wallet", "socks", "keychain"]
    sizes = ["XS", "S", "M", "L", "XL", "XXL", "one_size"]
    
    return render_template('accessories.html', user = user, items = items, sub_categories = sub_categories, sizes = sizes, selected_sub = sub_category, selected_size = size)


#Обробка маршруту для додавання товарів до бази даних
@app.route('/add_items', methods=['GET', 'POST'])
def add_items():
    if request.method == 'POST':
        try:
            #Отримання даних з форми
            brand = request.form['brand']
            name = request.form['name']
            price = float(request.form['price'])
            description = request.form['description']
            category = request.form['category']
            sub_category = request.form['sub-category']
            size = request.form.get('item_size', None)
            amount = int(request.form['amount'])

            #Обробка завантаженого зображення
            image_file = request.files['image']
            if image_file:
                #Створення папки для завантажень, якщо її ще не існує
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])

                #Збереження файлу
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
                image_file.save(image_path)
            else:
                image_path = ''

            #Створення об'єкта нового товару та обробка помилок
            new_item = Item(brand=brand, name=name, price=price, image=image_path,
                            description=description, category=category, 
                            sub_category=sub_category, size=size, amount=amount)
            db.session.add(new_item)
            db.session.commit()
            print("Товар успішно додано в базу даних!", flush=True)
        except Exception as e:
            db.session.rollback()
            print(f"Помилка при додаванні товару: {e}", flush=True)
        
        #Перенаправлення на особисту сторінку
        return redirect('/personal_page')

    return render_template('add_items.html')


#Обробка додавання товару до кошика
@app.route('/add_to_cart/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
    #Перевірка чи користувач авторизований
    if 'user_id' not in session:
        flash('Увійдіть у свій обліковий запис, щоб додавати товари.', 'warning')
        return redirect(url_for('login'))
    
    item = Item.query.get_or_404(item_id)
    user_id = session['user_id']

    #Пошук поточного замовлення яке має статус "Pending"
    order = Order.query.filter_by(user_id=user_id, status='Pending').first()

    #Створення нового замовлення, якщо його немає
    if not order:
        order = Order(user_id=user_id)
        db.session.add(order)
        db.session.commit()

    #Перевірка на наявність товару в замовленні, та збільшення кількості, якщо товар вже є
    order_item = OrderItem.query.filter_by(order_id=order.id, item_id=item.id).first()

    if order_item:
        order_item.quantity += 1
    else:
        #Створення нового рядка у таблиці замовлень
        order_item = OrderItem(
            order_id=order.id,
            item_id=item.id,
            quantity=1,
            price_at_purchase=item.price
        )
        db.session.add(order_item)

    db.session.commit()

    #Відправка підтвердження електронною поштою
    user = User.query.get(user_id)
    if user and user.email:
        msg = Message('Нове замовлення', recipients=[user.email])
        msg.html = f"""
        <h2>Підтвердження замовлення</h2>
        <p>Дякуюємо що замовили товар завдяки нашому сервісу! Ось деталі вашого замовлення:</p>
        <p>{item.brand} {item.name}</p>
        <p>Ціна: {item.price}$</p>
        <p>Кількість: {order_item.quantity}</p>
        <p>Дата: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <img src="{url_for('static', filename=item.image.split('static/')[-1], _external=True)}" width="200">
        <p>Для оплати товару перейдіть до особистої сторінки</p>
        """
        try:
            mail.send(msg)
        except Exception as e:
            print("Помилка при надсиланні email:", e)

    flash("Товар додано до кошика!", "success")
    return redirect(url_for('item_detail', item_id=item.id))


#Обробка конкретного товару
@app.route('/item/<int:item_id>')
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)

    #Пошук всіх копій товару з однаковими параметрами для вибору розміру
    copy_items = Item.query.filter_by(
        name=item.name,
        brand=item.brand,
        image=item.image,
        sub_category=item.sub_category,
        category=item.category,
        price=item.price
    ).all()

    #Отримання доступних розмірів
    available_sizes = sorted(set([i.size for i in copy_items]))

    #Обробка розміру
    selected_size = request.args.get('size')
    if selected_size:
        #Пошук товару з однаковими значеннями але іншим розміром
        selected_item = next((i for i in copy_items if i.size == selected_size), item)
    else:
        selected_item = item

    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    return render_template('item_detail.html', item=selected_item, user=user, available_sizes=available_sizes)


#Обробка авторизації користувача
@app.route('/login', methods=['GET', 'POST'])
def login():
    #Обробка даних форми авторизації якщо користувач надіслав POST запит
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        #Пошук користувача за email у базі даних
        user = User.query.filter_by(email=email).first()

        #Перевірка на коректність введених даних користувача
        if user and user.password == password:
            #Зберігаємо ID користувача в сесії
            session['user_id'] = user.id

            #Відправка листа підтвердження входу
            mail_message = Message("Login to your personal account", recipients=[user.email])
            mail_message.html = '''
            <p>You have entered your personal account. We are glad to see you again in our store.</p>
            <p><a href="http://127.0.0.1:5000/home" target="_blank">Click here to visit our store</a></p>'''
            mail.send(mail_message)

            #Перенаправлення користувача на персональну сторінку
            return redirect('/personal_page')
        else:
            return redirect('/login')
        
    else:
        #Показуємо форму входу якщо користувач не надіслав POST запит
        return render_template('login.html')


#Сторінка особистого кабінету користувача
@app.route('/personal_page')
def personal_page():
    if 'user_id' not in session:
        return redirect('/login')
    
    #Отримуємо дані користувача та його замовлення з бази даних
    user = User.query.get(session['user_id'])
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()

    return render_template('personal_page.html', user = user, orders = orders)



#Сторінка зі списком всіх замовлень
@app.route('/order_list')
def order_list():
    #Отримання всіх замовленнь відсортованих за датою створення
    orders = Order.query.order_by(Order.created_at.desc()).all()

    return render_template('order_list.html', orders = orders)


#Обробка зміни статусу замовлення
@app.route('/change_order_status/<int:order_id>', methods=['POST'])
def change_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    user = User.query.get(session['user_id'])
    print(f"[DEBUG] Отримано POST для замовлення #{order_id}")

    #Доступня значення статусів
    new_status = request.form.get('new_status')
    print(f"[DEBUG] Новий статус: {new_status}")
    valid_statuses = ["Pending", "Paid", "Shipped", "Delivered"]

    #Перевірка статусу
    if new_status not in valid_statuses:
        print(f"[DEBUG] Недійсний статус!")
        flash("Недійсний статус!", "danger")
        return redirect(url_for('personal_page'))
    
    #Збереження нового статусу в базі даних
    order.status = new_status
    db.session.commit()
    print(f"[DEBUG] Статус замовлення №{order.id} змінено на {new_status}")

    print(f"Статус замовлення №{order.id} змінено на {new_status}.", "success")

    return redirect(url_for('personal_page'))


#Обробка видалення замовлення
@app.route('/delte_order/<int:order_id>', methods = ['POST'])
def delete_order(order_id):
    user = User.query.get(session['user_id'])
    order = Order.query.get_or_404(order_id)

    for item in order.items:
        db.session.delete(item)

    #Видалення замовлення
    db.session.delete(order)
    db.session.commit()
    flash(f"Замовлення №{order.id} було видалено.", "success")

    #Якщо видаляв користувач залишення на сторінці зі списком всіх замовлень, якщо користувач - на особисту сторінку
    if user.first_name.lower() == "admin":
        return redirect(url_for('order_list'))
    else:
        return redirect(url_for('personal_page'))


#Обробка оплати замовлення
@app.route('/pay_order/<int:order_id>', methods=['POST'])
def pay_order(order_id):
    if 'user_id' not in session:
        flash("Увійдіть у свій обліковий запис.", "warning")
        return redirect(url_for('login'))

    order = Order.query.get_or_404(order_id)

    #Перевірка чи замовлення належить поточному користувачеві
    if order.user_id != session['user_id']:
        flash("Це не ваше замовлення!", "danger")
        return redirect(url_for('personal_page'))
    
    #Повідомка користувача якщо замовлення вже оплачено  
    if order.status != "Pending":
        flash("Це замовлення вже оплачено.", "info")
    else:
        order.status = "Paid"

        #Обчислення загальної суми замовлення
        total = sum(item.item.price * item.quantity for item in order.items)
        total_cents = int(total * 100)

        #Ініціалізація API Fondy
        api = Api(merchant_id=1396424, secret_key='test')
        checkout = Checkout(api=api)
        
        #Генерація URL для переходу на сторінку оплати
        checkout_url = checkout.url({
            "currency": "USD",
            "amount": total_cents,
            "order_id": f"order_{order.id}_{int(datetime.utcnow().timestamp())}",
            "response_url": url_for('fondy_confirm_and_pay', order_id=order.id, user_id=session['user_id'], _external=True),
        }).get('checkout_url')

    #Перенаправлення на сторінку оплати
    return redirect(checkout_url)


# Маршрут який викликається після підтвердження оплати з Fondy
@app.route('/fondy_confirm_and_pay/<int:order_id>', methods=['GET', 'POST'])
def fondy_confirm_and_pay(order_id):
    #Отримання user_id з параметрів URL
    user_id = request.args.get('user_id')

    #Оновлення сесії якщо передано user_id
    if user_id:
        session['user_id'] = int(user_id)

    order = Order.query.get_or_404(order_id)

    if order.status != "Paid":
        order.status = "Paid"

        total = 0
        items_html = ""

        #Обробка кожного товару в замовленні та зменшення залишку товарів в базі даних
        for order_item in order.items:
            item = Item.query.get(order_item.item_id)
            if item:
                item.amount -= order_item.quantity
                if item.amount < 0:
                    item.amount = 0  #Що б не було від’ємного залишку
                total += item.price * order_item.quantity
                items_html += f"<li>{item.name} ({item.brand}) – {order_item.quantity} шт. × {item.price}$</li>"

        #Збереження змін в базі даних
        db.session.commit()
        flash("Дякуємо за оплату!", "success")

        #Відправка електронного листа з підтвердженням
        user = User.query.get(order.user_id)
        if user and user.email:
            mail_message = Message("Дякуємо за ваше замовлення!", recipients=[user.email])
            mail_message.html = f'''
            <h3>Підтвердження оплати</h3>
            <p>Дата замовлення: {order.created_at.strftime('%d.%m.%Y %H:%M')}</p>
            <p>Замовлення №{order.id}</p>
            <p><strong>Товари:</strong></p>
            <ul>{items_html}</ul>
            <p><strong>Загальна сума:</strong> {total}$</p>
            <p>Ваше замовлення було успішно оплачено.<br>З повагою, команда магазину.</p>
            '''
            mail.send(mail_message)

    #Перенаправлення на особисту сторінку користувача
    return redirect(url_for('personal_page'))


#Обробка відображення списку товарів
@app.route('/item_list')
def item_list():
    items = Item.query.all()
    return render_template('item_list.html', items = items)


#Обробка копіювання товару з новим розміром
@app.route('/copy_item/<int:item_id>', methods=['POST'])
def copy_item(item_id):
    #Пошук товару та отримання даних з тіла запиту в форматі JSON
    item = Item.query.get_or_404(item_id)
    data = request.get_json()
    new_size = data.get('size')

    if not new_size:
        return jsonify({'error': 'Розмір не вказано'}), 400

    #Створення нового товару на основі існуючого але з новим розміром
    new_item = Item(
        brand=item.brand,
        name=item.name,
        price=item.price,
        image=item.image,
        description=item.description,
        category=item.category,
        sub_category=item.sub_category,
        size=new_size,
        amount=item.amount
    )

    #Додавання нового товару до бази даних
    db.session.add(new_item)
    db.session.commit()

    return jsonify({'message': f'Товар з розміром {new_size} створено успішно!'}), 200


#API для отримання списку всіх товарів
@app.route('/api/items', methods=['GET'])
def get_items():
    items = Item.query.all()
    #Формування списку словників з усіма полями товару
    items_data = [{'id': i.id,
                'brand': i.brand, 
                'name': i.name, 
                'price': i.price, 
                'image': i.image, 
                'description': i.description, 
                'category': i.category, 
                'sub_category': i.sub_category, 
                'size': i.size, 
                'amount': i.amount} for i in items]
    return jsonify(items_data)


#API для видалення товару за ID
@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_items(item_id):
    #Пошук товару за ID
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    #Видалення товару з бази даних
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted successfully'}), 200


#API для отримання списку всіх користувачів
@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    #Формування списку словників з потрібними полями для кожного користувача
    users_data = [{'id': u.id, 
                   'first_name': u.first_name, 
                   'last_name': u.last_name, 
                   'email': u.email, 
                   'phone_number': u.phone_number} for u in users]
    return jsonify(users_data)


#API для видалення користувача за ID
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Пошук користувача в базі даних за ID
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    #Видалення користувача з бази даних
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200


#Обробка регістрації нового користувача
@app.route('/registration', methods=['GET', 'POST'])
def registration():
    #Отримання даних з форми реєстрації
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        phone_number = request.form['phone_number']

        #Створення нового користувача на основі введених даних
        user = User(first_name = first_name, last_name = last_name, email = email, password = password, phone_number = phone_number)

        try:
            #Додавання користувача до бази даних
            db.session.add(user)
            db.session.commit()

            #Відправка електронного листа
            mail_message = Message("Successful registration", recipients=[user.email])
            mail_message.html = '''
            <p>Welcome to our store and thank you for trusting our services.</p>
            <p><a href="http://127.0.0.1:5000/home" target="_blank">Click here to visit our store</a></p>'''
            mail.send(mail_message)

            #Перенаправлення на сторінку входу після успішної реєстрації
            return redirect('/login')
        except:
            return "error"
        
    else:
        return render_template('registration.html')


#Обробка сторінки помилки 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


#Обробка виходу з облікового запису
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')


#Обробка запиту до кошика користувача
@app.route('/cart_items')
def cart_items():
    if 'user_id' not in session:
        return jsonify({'items': []})

    user_id = session['user_id']
    order = Order.query.filter_by(user_id=user_id, status='Pending').first()

    if not order or not order.items:
        return jsonify({'items': []})

    #Формування списку товарів у кошику
    items_data = []
    for order_item in order.items:
        items_data.append({
            'name': order_item.item.name,
            'brand': order_item.item.brand,
            'quantity': order_item.quantity,
            'price': order_item.price_at_purchase
        })

    return jsonify({'items': items_data})


#Запуск додатку
if __name__ == "__main__":
    app.run(debug=True)

