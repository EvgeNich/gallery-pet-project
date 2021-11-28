# spellchecker: disable
import cgi
from datetime import datetime
import hashlib
import os

from http.server import HTTPServer, BaseHTTPRequestHandler
import sqlalchemy as sql
from sqlalchemy.orm import sessionmaker

from modules.db_mapper import Base, ImageTable
from modules.templates import GALLERY_TEMPLATE, INDEX_TEMPLATE, MESSAGE_TEMPLATE
from modules import image_processing

# HANDLER

class Handler(BaseHTTPRequestHandler):
    def _set_headers(self, c_type="text/html"):
        self.send_response(200)
        self.send_header("Content-type", c_type)
        self.end_headers()

    def do_GET(self):
        # as I expect to receive a path that contains one of three possible variants:
        # 1: / 2: /gallery 3: /folder/image.type or /folder/folder/image.type
        # I get rid of the first '/' and cut the path from the back once with '/' as a separator
        # in this case as the first part of a path I will get the proper route or drop the 404th error
        path = self.path[1:].rsplit('/',1)
        match path[0]:
            #main page
            case '':
                self._set_headers()
                self.wfile.write(INDEX_TEMPLATE.render().encode("utf8"))

            #gallery page
            case 'gallery':
                image_data = session.query(
                    ImageTable.img_id, ImageTable.file_name, 
                    ImageTable.file_size, ImageTable.maker, 
                    ImageTable.model, ImageTable.creation_date, 
                    ImageTable.upload_date, ImageTable.thumbnail
                )
                image_data_dicts = [r._asdict() for r in image_data]
                self._set_headers()
                processed_data_dicts = image_processing.db_data_to_html_template(image_data_dicts)
                msg = GALLERY_TEMPLATE.render(images = processed_data_dicts)
                self.wfile.write(msg.encode("utf8"))

            #image requests
            case 'images' | 'images/thumbnails':
                # here I expect to receive image.type as the second part of a path
                # I will check the DB for this filename and if there will be one I will load it
                if not session.query(ImageTable.file_name).filter(ImageTable.file_name==path[1]).first():
                    self.send_error(404)
                    return
                try:
                    # self.path here will look the same as the propper path to an image
                    with open(self.path[1:], 'rb') as f:
                        content = f.read()
                    # get imagetype for the propper header
                    img_type = path[1].split('.')[1]
                    self._set_headers(f'image/{img_type}')
                    self.wfile.write(content)
                except FileNotFoundError:
                    self.send_error(404)

            #other
            case _:
                self.send_error(404)
        session.close()

    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                    'CONTENT_TYPE':self.headers['Content-Type'],
            })
        if not form['file'].filename:
            self.send_error(400, "No file was uploaded!")
            return
        if len(form['textfield'].value) > 50:
            self.send_error(400, "Name too long! Use less than 50 chars!")
            return
        data = form['file'].file.read()
        if not image_processing.valid_image_type(data):
            self.send_error(415, "This filetype is not supported!")
            return
        file_name = form['textfield'].value + image_processing.get_dot_type(data)
        image_data = {'file_name' : file_name}
        md5 = hashlib.md5(data).hexdigest()
        if session.query(ImageTable.md5).filter(ImageTable.md5==md5).first():
            self.send_error(400, "This image already exists!")
            return
        image_data['md5'] = md5
        saved_image_size = image_processing.save_image(data, file_name)
        image_data['file_size'] = saved_image_size
        image_data.update(image_processing.get_exif_params(file_name)) #update image data with maker, model, and creation date info
        thumanail_created = image_processing.create_thumbnail(file_name)
        image_data['thumbnail'] = thumanail_created
        image_data['upload_date'] = datetime.now()
        session.add(ImageTable(**image_data))
        session.commit()
        self._set_headers()
        self.wfile.write(MESSAGE_TEMPLATE.render(message = f"{file_name} successfully uploaded!").encode("utf8"))            
        session.close()

    def do_DELETE(self):
        length = int(self.headers.get('content-length'))
        image_id = int(self.rfile.read(length))
        thumbnail_flag, file_name = session.query(ImageTable.thumbnail, ImageTable.file_name).filter(ImageTable.img_id==image_id).one()
        image_processing.delete_image(file_name, thumbnail_flag)
        session.query(ImageTable).filter(ImageTable.img_id==image_id).delete()
        session.commit()
        session.close()
        self.send_response(200)
        self.end_headers()

# MAIN
if __name__ == "__main__":
    #DB INIT
    db_user = os.getenv('MYSQL_USER', 'gp_user')
    db_pwd = os.getenv('MYSQL_PASSWORD', 'gp_password')
    db_host = os.getenv('MYSQL_HOST', 'mysql')
    db_port =  os.getenv('MYSQL_PORT', 3306)
    db_name = os.getenv('MYSQL_DATABASE', 'gallery_project')

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

