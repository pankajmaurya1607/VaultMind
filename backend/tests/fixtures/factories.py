import factory
from app.models.role import Role
from app.models.department import Department
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.models.chat_session import ChatSession
from app.auth.jwt import hash_password


class RoleFactory(factory.Factory):
    class Meta:
        model = Role

    name = factory.Sequence(lambda n: f"Role{n}")


class DepartmentFactory(factory.Factory):
    class Meta:
        model = Department

    name = factory.Sequence(lambda n: f"Department{n}")


class UserFactory(factory.Factory):
    class Meta:
        model = User

    name = factory.Faker("name")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password_hash = hash_password("password123")
    department_id = 1
    role_id = 3


class DocumentFactory(factory.Factory):
    class Meta:
        model = Document

    filename = factory.Sequence(lambda n: f"doc{n}.txt")
    original_filename = factory.Sequence(lambda n: f"original{n}.txt")
    file_path = "/tmp/test.txt"
    file_size = 100
    mime_type = "text/plain"
    uploaded_by = 1
    department_id = 1
    status = DocumentStatus.READY


class ChatSessionFactory(factory.Factory):
    class Meta:
        model = ChatSession

    user_id = 1
    title = "Test Chat"
