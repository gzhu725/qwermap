from mongoengine import connect


def init_db(app):
    mongo_uri = app.config.get("MONGO_URI")
    mongo_db = app.config.get("MONGO_DB")
    if not mongo_uri:
        raise RuntimeError("MONGO_URI is not configured")

    connect(
        db=mongo_db,
        host=mongo_uri,
        uuidRepresentation="standard",
    )
