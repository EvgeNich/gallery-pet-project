#http
from http.server import HTTPServer, BaseHTTPRequestHandler
import cgi
from jinja2 import Environment, FileSystemLoader
#database
import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
#image
from pathlib import Path
import imghdr
import hashlib
from PIL import Image
#misc
from datetime import datetime

# MISC

def _str_to_datetime(date_string, format):
    try:
        return datetime.strptime(date_string, format)
    except (ValueError, TypeError):
        return None

def _datetime_to_str(date):
    try:
        return datetime.strftime(date, '%H:%M  %d %b. %Y')
    except (ValueError, TypeError):
        return None

def _get_image_type(image_as_bytes):
    imagetype = imghdr.what(None, image_as_bytes)
    if imagetype:
        return '.' + imagetype
    else:
        return None

def _image_size_to_str(raw_size):
    pointer = 0
    while raw_size // 1024 >= 1:
        raw_size = raw_size / 1024
        pointer += 1
    size_map = {0:'B', 1:'KB', 2:'MB', 4:'GB'}
    return f'{raw_size:.2f}'.rstrip('0').rstrip('.') + f' {size_map.get(pointer)}'

def get_exif_params(image):
    image_exif = image.getexif()
    if image_exif is None : image_exif = {}
    d = dict(image_exif.items())
    output = {
        'maker' : d.get(271, None),
        'model' : d.get(272, None),
        'creation_date' : _str_to_datetime(d.get(306, None), '%Y:%m:%d %H:%M:%S')
    }
    return output

def db_to_template(image_data):
    for row in image_data:
        row.update({'file_size': _image_size_to_str(row.get('file_size'))})
        row.update({'file_path': (IMAGES_PATH + row.get('file_name'))})
        row.update({'creation_date': _datetime_to_str(row.get('creation_date'))})
        row.update({'upload_date': _datetime_to_str(row.get('upload_date'))})
        if row.get('thumbnail'):
            row.update({'thumbnail_path': (THUMBNAIL_PATH + row.get('file_name'))})
        else:
            row.update({'thumbnail_path': row.get('file_path')})
    return image_data

# DB MAPPER

Base = declarative_base()

class ImageTable(Base):
    __tablename__ = 'images'

    img_id = sql.Column(sql.Integer, primary_key=True)

    file_name = sql.Column(sql.String(55), nullable=False)
    md5 = sql.Column(sql.String(32), nullable=False)
    file_size = sql.Column(sql.Integer, nullable=False)
    maker = sql.Column(sql.String(256))
    model = sql.Column(sql.String(256))
    creation_date = sql.Column(sql.DateTime)
    thumbnail = sql.Column(sql.Boolean, nullable=False)
    upload_date = sql.Column(sql.DateTime, nullable=False)

# HANDLER

class Handler(BaseHTTPRequestHandler):
    def _set_headers(self, c_type="text/html"):
        self.send_response(200)
        self.send_header("Content-type", c_type)
        self.end_headers()

    def _html(self, message): #--?--#
        content = f"<html><body><h1>{message}</h1></body></html>"
        return content.encode("utf8")

    #REQUEST HANDLERS
    def do_GET(self):
        path = self.path[1:].rsplit('/',1) # folder/folder... + image.type path expected
        match path[0]:
            #main page
            case '':
                self._set_headers()
                self.wfile.write(INDEX.render().encode("utf8"))

            #gallery page
            case 'gallery':
                image_data = session.query(ImageTable.img_id, ImageTable.file_name, ImageTable.file_size, ImageTable.maker, ImageTable.model, ImageTable.creation_date, ImageTable.upload_date, ImageTable.thumbnail)
                image_container = [r._asdict() for r in image_data]
                self._set_headers()
                msg = GALLERY.render(images = db_to_template(image_container))
                self.wfile.write(msg.encode("utf8"))

            #image requests
            case 'images' | 'images/thumbnails':
                # if image.type in path exists in db.file_name - try to open it
                db_file_names = [r[0] for r in session.query(ImageTable.file_name)]
                if path[1] in db_file_names:
                    img_type = path[1].split('.')[1]
                    try:
                        with open(self.path[1:], 'rb') as f:
                            content = f.read()
                        self._set_headers(f'image/{img_type}')
                        self.wfile.write(content)
                    except FileNotFoundError:
                        self.send_error(404)
                else:
                    self.send_error(404)

            #other
            case _:
                self.send_error(404)
        session.close()

    def do_POST(self):
        #received <form>
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                    'CONTENT_TYPE':self.headers['Content-Type'],
                    })

        if form['file'].filename:
            if len(form['textfield'].value) > 50:
                self.send_error(400, "Name too long! Use less than 50 chars!")
            else:
                if not Path(THUMBNAIL_PATH).exists():
                    Path(THUMBNAIL_PATH).mkdir(parents=True, exist_ok=True)
                data = form['file'].file.read()
                filetype = _get_image_type(data)
                if filetype:
                    image_data = {'file_name' : form['textfield'].value + filetype}
                    md5 = hashlib.md5(data).hexdigest()
                    if md5 in [r[0] for r in session.query(ImageTable.md5)]:
                        self.send_error(400, "This image already exists!")
                    else:
                        image_data.update({'md5' : md5})
                        with open(IMAGES_PATH + image_data['file_name'], "w+b") as image:
                            image.write(data) 
                        image_data.update({'file_size' : Path(IMAGES_PATH + image_data['file_name']).stat().st_size})
                        with Image.open(IMAGES_PATH + image_data['file_name']) as loaded_image:
                            image_data.update(get_exif_params(loaded_image))
                            width, height = loaded_image.size
                            if width > THUMBNAIL_DIM and height > THUMBNAIL_DIM:
                                loaded_image.thumbnail((THUMBNAIL_DIM,THUMBNAIL_DIM))
                                loaded_image.save(THUMBNAIL_PATH + image_data["file_name"])
                                image_data.update({'thumbnail': True})
                            else:
                                image_data.update({'thumbnail': False})
                        image_data.update({'upload_date': datetime.now()})
                        session.add(ImageTable(**image_data))
                        session.commit()
                        self._set_headers()
                        self.wfile.write(MESSAGE.render(message = f"{image_data['file_name']} successfully uploaded!").encode("utf8"))
                else:
                    self.send_error(415, "This filetype is not supported!")
        else:
            self.send_error(400, "No file was uploaded!")
        session.close()

    def do_DELETE(self):
        length = int(self.headers.get('content-length'))
        image_id = int(self.rfile.read(length))
        thumbnail_flag, file_name = session.query(ImageTable.thumbnail, ImageTable.file_name).filter(ImageTable.img_id==image_id).one()
        session.query(ImageTable).filter(ImageTable.img_id==image_id).delete()
        session.commit()
        session.close()
        if thumbnail_flag:
            Path(THUMBNAIL_PATH + file_name).unlink()
        Path(IMAGES_PATH + file_name).unlink()
        self.send_response(200)
        self.end_headers()

# MAIN
if __name__ == "__main__":
    #CONSTANTS
    IMAGES_PATH = 'images/'
    THUMBNAIL_PATH = 'images/thumbnails/'
    THUMBNAIL_DIM = 128

    #DB INIT
    db_user = 'gp_user'
    db_pwd = 'gp_password'
    db_host = 'mysql'
    db_port = 3306
    db_name = 'gallery_project'

    connection_str = f'mysql+pymysql://{db_user}:{db_pwd}@{db_host}:{db_port}/{db_name}'

    engine = sql.create_engine(connection_str)
    Base.metadata.bind = engine

    try:
        Base.metadata.create_all()
        print('DB connection established')
    except Exception as e:
        print(e)
        exit()
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    #JINJA ENV
    file_loader = FileSystemLoader('templates')
    env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)
    INDEX = env.get_template('index.html')
    GALLERY = env.get_template('gallery.html')
    MESSAGE = env.get_template('message.html')

    #SERVER STARTUP
    server_address = ('0.0.0.0', 8000)
    httpd = HTTPServer(server_address, Handler)
    print(f"Starting at http://{server_address[0]}:{server_address[1]}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    #EXIT
    httpd.server_close()
    print("Sever stopped")
    engine.dispose()
    print('DB connection closed')