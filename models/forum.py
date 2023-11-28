from typing import Optional
from time import time

import strawberry
from beanie import Document, Indexed
from pydantic import BaseModel, Field
from opendal import AsyncOperator

from models.file import File
