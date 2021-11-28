# Python HTTP server pet-project

## Description

This is my little pet-project based on a test task for python backend developer found somewhere on the web.

These are the main requirements of the said task:
- Create a small web app for image uploading.
- Frontend is not very important. 
- There must be a file upload form and a showcase of all uploaded images. Doesn't matter if they will be on the same or on a different web pages.
- Upload form must have:
    - a file selection field
    - a text field to name the image you are going to upload
- Gallery must have:
    - an image preview (which acts as a link to original image)
    - a file name (from upload form)
    - a file size
    - an info about camera model and maker the image was taken with (from EXIF)
    - a date the uploaded image was made (from EXIF)
    - an upload date
    - a button to delete an uploaded image
- The app must accept only images.
- The app must not accept duplicates.
- The app must not accept images without EXIF creation date or with one that is more than a year before now.

The last requirement was omitted in my project because EXIF data only exists for JPEG and TIFF and with a restriction on images made not more than a year ago - it would be quite difficult to find one. Therefore, my app accept any image type that can be found in this list: `'.rgb', '.gif', '.pbm', '.pgm', '.ppm', '.tiff', '.rast', '.xbm', '.jpeg', '.bmp', '.png', '.webp', '.exr'` without any restrictions on creation date. But it can be implemented very easily.

## Realization

This project uses `http.server` for the server and for the base of request handler, `jinja` as a template engine, `MySQL 5.7` paired with `sqlalchemy` for data storage and `PILLOW` for image processing. 

`Docker` was used to deploy the app. There is a separate container for the MySQL database and for the Python server, which acts both as HTTP and file server.

You can deploy the app with:
```
docker-compose up
```

After the deployment, you can find my app at http://localhost:8000

> NOTE: MySQL will take some time to get ready