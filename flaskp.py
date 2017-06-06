
@app.route('/add_d', methods=['GET'])
def addd():
    db.create_all()
    return 'hellllo'


@app.route('/add_5', methods=['GET'])
def add_5():
    c = Category()
    g = Gift()
    c.category_title = category5_fa
    c.category_specification = 'Category Specification 5'
    g.gift_title = 'Gift 11'
    g.gift_specification = 'Gift Specification 11'
    g.gift_price = '260$'
    g.gift_image = 'img.jpg'
    g2 = Gift()
    g2.gift_title = 'Gift 56'
    g2.gift_specification = 'Gift Specification 56'
    g2.gift_price = '420$'
    g2.gift_image = 'img2.jpg'
    g3 = Gift()
    g3.gift_title = 'Gift 31'
    g3.gift_specification = 'Gift Specification 31'
    g3.gift_price = '310$'
    g3.gift_image = 'img3.jpg'
    g4 = Gift()
    g4.gift_title = 'Gift 48'
    g4.gift_specification = 'Gift Specification 48'
    g4.gift_price = '100$'
    g4.gift_image = 'img4.jpg'
    g5 = Gift()
    g5.gift_title = 'Gift 48'
    g5.gift_specification = 'Gift Specification 48'
    g5.gift_price = '200$'
    g5.gift_image = 'img4.jpg'
    c.gifts.append(g)
    c.gifts.append(g2)
    c.gifts.append(g3)
    c.gifts.append(g4)
    c.gifts.append(g5)
    db.session.add(g)
    db.session.add(g2)
    db.session.add(g3)
    db.session.add(g4)
    db.session.add(g5)
    db.session.add(c)
    db.session.commit()
    return 'Hello World!'


@app.route('/add_4', methods=['GET'])
def add_4():
    c = Category()
    g = Gift()
    c.category_title = category4_fa
    c.category_specification = 'Category Specification 4'
    g.gift_title = 'Gift 1'
    g.gift_specification = 'Gift Specification 1'
    g.gift_price = '20$'
    g.gift_image = 'img.jpg'
    g2 = Gift()
    g2.gift_title = 'Gift 2'
    g2.gift_specification = 'Gift Specification 2'
    g2.gift_price = '230$'
    g2.gift_image = 'img2.jpg'
    g3 = Gift()
    g3.gift_title = 'Gift 3'
    g3.gift_specification = 'Gift Specification 3'
    g3.gift_price = '110$'
    g3.gift_image = 'img3.jpg'
    g4 = Gift()
    g4.gift_title = 'Gift 4'
    g4.gift_specification = 'Gift Specification 4'
    g4.gift_price = '56$'
    g4.gift_image = 'img4.jpg'
    c.gifts.append(g)
    c.gifts.append(g2)
    c.gifts.append(g3)
    c.gifts.append(g4)
    db.session.add(g)
    db.session.add(g2)
    db.session.add(g3)
    db.session.add(g4)
    db.session.add(c)
    db.session.commit()
    return 'Hello World!'


@app.route('/add_3', methods=['GET'])
def add_3():
    c = Category()
    g = Gift()
    c.category_title = category3_fa
    c.category_specification = 'Category Specification 3'
    g.gift_title = 'Gift 1'
    g.gift_specification = 'Gift Specification 1'
    g.gift_price = '760$'
    g.gift_image = 'img.jpg'
    g2 = Gift()
    g2.gift_title = 'Gift 2'
    g2.gift_specification = 'Gift Specification 2'
    g2.gift_price = '290$'
    g2.gift_image = 'img2.jpg'
    g3 = Gift()
    g3.gift_title = 'Gift 3'
    g3.gift_specification = 'Gift Specification 3'
    g3.gift_price = '120$'
    g3.gift_image = 'img3.jpg'
    g4 = Gift()
    g4.gift_title = 'Gift 4'
    g4.gift_specification = 'Gift Specification 4'
    g4.gift_price = '26$'
    g4.gift_image = 'img4.jpg'
    c.gifts.append(g)
    c.gifts.append(g2)
    c.gifts.append(g3)
    c.gifts.append(g4)
    db.session.add(g)
    db.session.add(g2)
    db.session.add(g3)
    db.session.add(g4)
    db.session.add(c)
    db.session.commit()
    return 'Hello World!'


@app.route('/add_2', methods=['GET'])
def add_2():
    c = Category()
    g = Gift()
    c.category_title = category2_fa
    c.category_specification = 'Category Specification 2'
    g.gift_title = 'Gift 11'
    g.gift_specification = 'Gift Specification 11'
    g.gift_price = '260$'
    g.gift_image = 'img.jpg'
    g2 = Gift()
    g2.gift_title = 'Gift 56'
    g2.gift_specification = 'Gift Specification 56'
    g2.gift_price = '420$'
    g2.gift_image = 'img2.jpg'
    g3 = Gift()
    g3.gift_title = 'Gift 31'
    g3.gift_specification = 'Gift Specification 31'
    g3.gift_price = '310$'
    g3.gift_image = 'img3.jpg'
    g4 = Gift()
    g4.gift_title = 'Gift 48'
    g4.gift_specification = 'Gift Specification 48'
    g4.gift_price = '120$'
    g4.gift_image = 'img4.jpg'
    g5 = Gift()
    g5.gift_title = 'Gift 48'
    g5.gift_specification = 'Gift Specification 48'
    g5.gift_price = '210$'
    g5.gift_image = 'img4.jpg'
    c.gifts.append(g)
    c.gifts.append(g2)
    c.gifts.append(g3)
    c.gifts.append(g4)
    db.session.add(g)
    db.session.add(g2)
    db.session.add(g3)
    db.session.add(g4)
    db.session.add(g5)
    db.session.add(c)
    db.session.commit()
    return 'Hello World!'


@app.route('/add_1', methods=['GET'])
def add_1():
    c = Category()
    g = Gift()
    c.category_title = category1_fa
    c.category_specification = 'Category Specification 1'
    g.gift_title = 'Gift 1'
    g.gift_specification = 'Gift Specification 1'
    g.gift_price = '210$'
    g.gift_image = 'img.jpg'
    g2 = Gift()
    g2.gift_title = 'Gift 2'
    g2.gift_specification = 'Gift Specification 2'
    g2.gift_price = '236$'
    g2.gift_image = 'img2.jpg'
    g3 = Gift()
    g3.gift_title = 'Gift 3'
    g3.gift_specification = 'Gift Specification 3'
    g3.gift_price = '10$'
    g3.gift_image = 'img3.jpg'
    g4 = Gift()
    g4.gift_title = 'Gift 4'
    g4.gift_specification = 'Gift Specification 4'
    g4.gift_price = '526$'
    g4.gift_image = 'img4.jpg'
    c.gifts.append(g)
    c.gifts.append(g2)
    c.gifts.append(g3)
    c.gifts.append(g4)
    db.session.add(g)
    db.session.add(g2)
    db.session.add(g3)
    db.session.add(g4)
    db.session.add(c)
    db.session.commit()
    return 'Hello World!'


@app.route('/send_file', methods=['POST'])
def hello_file():
    if 'file' not in request.files:
        print('no file!')
        return 'no file!'
    file = request.files['file']
    if file.filename == '':
        print('no selected file')
        return 'no selected file'
    if file:
        file_name = secure_filename(file.filename)
        print(file_name)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))
        print('Nice')
        return 'Nice!'
    return 'dafuq?'


if __name__ == '__main__':
    app.run()
