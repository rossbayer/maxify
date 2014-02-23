"""Project wide test fixtures and utilities.

"""

import pytest

from maxify.model import *
from maxify.units import *
from maxify.repo import Repository


_db_session = open_user_data(":memory:", False)


@pytest.fixture(autouse=True)
def repository(request):
    Repository.init(":memory:")
    request.addfinalizer(_clear_test_data)
    return Repository

@pytest.fixture()
def db_session(repository):
    """Database session object for accessing in-memory persisted data.

    """
    return repository.db_session


def _clear_test_data():
    _db_session.query(Project).delete()
    _db_session.commit()

@pytest.fixture
def project(db_session):
    p = Project(name="test", desc="Test Project")

    p.add_metric(Metric(
        name="Story Points",
        units=Int,
        value_range=[1, 2, 3, 5, 8],
        default_value=3
    ))

    p.add_metric(Metric(
        name="Compile Time",
        units=Duration
    ))

    db_session.add(p)
    db_session.commit()

    return p


@pytest.fixture
def story_points_metric(project):
    return project.metric("Story Points")


@pytest.fixture
def compile_time_metric(project):
    return project.metric("Compile Time")


