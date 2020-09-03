import os
from src.page_groups import pathing

db_path = pathing.Static.get_database(r"local.db")
template_path = pathing.Static.get_html(r"templates")
