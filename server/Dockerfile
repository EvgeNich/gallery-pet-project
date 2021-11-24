FROM python:3.10

WORKDIR /server
COPY . /server

RUN pip install -r requirements.txt

ENTRYPOINT [ "python" ]
CMD [ "server.py" ]

EXPOSE 8000