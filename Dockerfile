FROM python:3.10
ENV APPLICATION_SERVICE=/app

# set work directory
RUN mkdir -p $APPLICATION_SERVICE

# where the code lives
WORKDIR $APPLICATION_SERVICE

# set environment variablesf
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
COPY poetry.lock pyproject.toml ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# copy project
COPY . $APPLICATION_SERVICE
WORKDIR $APPLICATION_SERVICE
CMD python manage.py migrate && python manage.py collectstatic --noinput && \
    uvicorn core.asgi:application --port 8000 --host 0.0.0.0 --reload
