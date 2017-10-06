import logging
import os
import sys

from peewee import Model, SqliteDatabase, CharField, IntegerField, DeleteQuery

logging.getLogger("peewee").setLevel(logging.ERROR)
logger = logging.getLogger("DB")
logger.setLevel(logging.INFO)

# Init DB
db_path = os.path.join(os.path.dirname(sys.argv[0]), 'queue.db')
db = SqliteDatabase(db_path, threadlocals=True)


class BaseQueueModel(Model):
    class Meta:
        database = db


class QueueItemModel(BaseQueueModel):
    scan_path = CharField(max_length=256, unique=True, null=False)
    scan_for = CharField(max_length=64, null=False)
    scan_section = IntegerField(null=False)
    scan_type = CharField(max_length=64, null=False)


def create_database():
    if not os.path.exists(db_path):
        db.create_tables([QueueItemModel])
        logger.info("Created database tables")


def connet():
    if not db.is_closed():
        logger.error("Already connected to database...")
        return False
    return db.connect()


def get_next_item():
    item = None
    try:
        item = QueueItemModel.get()
    except:
        # logger.exception("Exception getting first item to scan: ")
        pass
    return item


def get_all_items():
    items = []
    try:
        for item in QueueItemModel.select():
            items.append({'scan_path': item.scan_path,
                          'scan_for': item.scan_for,
                          'scan_type': item.scan_type,
                          'scan_section': item.scan_section})
    except:
        logger.exception("Exception getting all items from database: ")
        return None
    return items


def remove_item(scan_path):
    try:
        return DeleteQuery(QueueItemModel).where(QueueItemModel.scan_path == scan_path).execute()
    except:
        logger.exception("Exception deleting %r from database: ", scan_path)
        return False


def add_item(scan_path, scan_for, scan_section, scan_type):
    item = None
    try:
        return QueueItemModel.create(scan_path=scan_path, scan_for=scan_for, scan_section=scan_section,
                                     scan_type=scan_type)
    except AttributeError as ex:
        return item
    except:
        pass
        # logger.exception("Exception adding %r to database: ", scan_path)
    return item


# Create database
if not os.path.exists(db_path):
    create_database()
connet()