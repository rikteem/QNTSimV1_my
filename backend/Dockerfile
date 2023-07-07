FROM python:3.10
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /code/
RUN pip install .
WORKDIR /code/web
EXPOSE 8000
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]